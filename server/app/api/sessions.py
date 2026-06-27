from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import PracticeSession
from app.models.session import utc_now
from app.security import require_owner

router = APIRouter(
    prefix="/sessions",
    tags=["sessions"],
    dependencies=[Depends(require_owner)],
)

SessionStatus = Literal["active", "completed", "abandoned"]


class SessionStartRequest(BaseModel):
    default_club: str = Field(default="56", min_length=1, max_length=64)
    default_distance_ft: int = Field(default=15, ge=1, le=300)
    notes: str = ""


class SessionUpdateRequest(BaseModel):
    default_club: str | None = Field(default=None, min_length=1, max_length=64)
    default_distance_ft: int | None = Field(default=None, ge=1, le=300)
    notes: str | None = None


class SessionResponse(BaseModel):
    id: str
    started_at: datetime
    ended_at: datetime | None
    status: SessionStatus
    default_club: str
    default_distance_ft: int
    notes: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


async def _active_session(db: AsyncSession) -> PracticeSession | None:
    result = await db.execute(
        select(PracticeSession)
        .where(PracticeSession.status == "active")
        .order_by(PracticeSession.started_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def _session_or_404(session_id: str, db: AsyncSession) -> PracticeSession:
    session = await db.get(PracticeSession, session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return session


@router.post("/start", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def start_session(
    payload: SessionStartRequest,
    db: AsyncSession = Depends(get_db),
) -> PracticeSession:
    existing_active = await _active_session(db)
    if existing_active is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An active session already exists",
        )

    practice_session = PracticeSession(
        default_club=payload.default_club,
        default_distance_ft=payload.default_distance_ft,
        notes=payload.notes,
    )
    db.add(practice_session)
    await db.commit()
    await db.refresh(practice_session)
    return practice_session


@router.get("/active", response_model=SessionResponse | None)
async def get_active_session(db: AsyncSession = Depends(get_db)) -> PracticeSession | None:
    return await _active_session(db)


@router.get("", response_model=list[SessionResponse])
async def list_sessions(db: AsyncSession = Depends(get_db)) -> list[PracticeSession]:
    result = await db.execute(
        select(PracticeSession).order_by(PracticeSession.started_at.desc(), PracticeSession.id)
    )
    return list(result.scalars().all())


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
) -> PracticeSession:
    return await _session_or_404(session_id, db)


@router.patch("/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: str,
    payload: SessionUpdateRequest,
    db: AsyncSession = Depends(get_db),
) -> PracticeSession:
    practice_session = await _session_or_404(session_id, db)

    if payload.default_club is not None:
        practice_session.default_club = payload.default_club
    if payload.default_distance_ft is not None:
        practice_session.default_distance_ft = payload.default_distance_ft
    if payload.notes is not None:
        practice_session.notes = payload.notes
    practice_session.updated_at = utc_now()

    await db.commit()
    await db.refresh(practice_session)
    return practice_session


@router.post("/{session_id}/stop", response_model=SessionResponse)
async def stop_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
) -> PracticeSession:
    practice_session = await _session_or_404(session_id, db)
    if practice_session.status != "active":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only active sessions can be stopped",
        )

    now = utc_now()
    practice_session.status = "completed"
    practice_session.ended_at = now
    practice_session.updated_at = now
    await db.commit()
    await db.refresh(practice_session)
    return practice_session


@router.post("/{session_id}/abandon", response_model=SessionResponse)
async def abandon_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
) -> PracticeSession:
    practice_session = await _session_or_404(session_id, db)
    if practice_session.status != "active":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only active sessions can be abandoned",
        )

    now = utc_now()
    practice_session.status = "abandoned"
    practice_session.ended_at = now
    practice_session.updated_at = now
    await db.commit()
    await db.refresh(practice_session)
    return practice_session


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
) -> Response:
    await _session_or_404(session_id, db)
    await db.execute(delete(PracticeSession).where(PracticeSession.id == session_id))
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
