from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.buckets import BucketResponse
from app.api.sessions import SessionResponse
from app.config import get_settings
from app.database import get_db
from app.models import PracticeBucket, PracticeSession
from app.models.session import utc_now
from app.security import require_owner

router = APIRouter(tags=["quick-log"], dependencies=[Depends(require_owner)])

QuickLogMode = Literal["active", "start_session", "standalone"]


class QuickLogRequest(BaseModel):
    ball_count: int = Field(..., ge=1, le=500)
    mode: QuickLogMode = "active"
    club: str = Field(default="56", min_length=1, max_length=64)
    distance_ft: int = Field(default=15, ge=1, le=300)


class QuickLogResponse(BaseModel):
    session: SessionResponse
    bucket: BucketResponse
    active_session_created: bool
    standalone_session_created: bool


async def _active_session(db: AsyncSession) -> PracticeSession | None:
    result = await db.execute(
        select(PracticeSession)
        .where(PracticeSession.status == "active")
        .order_by(PracticeSession.started_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


def _completed_quick_log_bucket(
    session_id: str,
    ball_count: int,
    club: str,
    distance_ft: int,
    now: datetime,
) -> PracticeBucket:
    return PracticeBucket(
        session_id=session_id,
        ball_count=ball_count,
        club=club,
        distance_ft=distance_ft,
        source="quick_log",
        status="completed",
        started_at=now,
        ended_at=now,
        created_at=now,
        updated_at=now,
    )


def _clean_optional_value(value: str | None) -> str | None:
    if value is None:
        return None
    clean_value = value.strip()
    return clean_value or None


def _session_provenance() -> dict[str, str | None]:
    settings = get_settings()
    return {
        "app_git_sha": _clean_optional_value(settings.app_git_sha),
        "app_build_version": _clean_optional_value(settings.app_build_version),
        "design_version": _clean_optional_value(settings.design_version)
        or "v3-app-era-timeline",
    }


@router.post("/quick-log", response_model=QuickLogResponse, status_code=status.HTTP_201_CREATED)
async def quick_log(
    payload: QuickLogRequest,
    db: AsyncSession = Depends(get_db),
) -> QuickLogResponse:
    now = utc_now()
    session = await _active_session(db)
    active_session_created = False
    standalone_session_created = False

    if session is None:
        if payload.mode == "active":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="No active session. Choose start_session or standalone.",
            )

        if payload.mode == "start_session":
            session = PracticeSession(
                default_club=payload.club,
                default_distance_ft=payload.distance_ft,
                started_at=now,
                created_at=now,
                updated_at=now,
                **_session_provenance(),
            )
            active_session_created = True
        else:
            session = PracticeSession(
                started_at=now,
                ended_at=now,
                status="completed",
                default_club=payload.club,
                default_distance_ft=payload.distance_ft,
                created_at=now,
                updated_at=now,
                **_session_provenance(),
            )
            standalone_session_created = True

        db.add(session)
        await db.flush()

    bucket = _completed_quick_log_bucket(
        session_id=session.id,
        ball_count=payload.ball_count,
        club=payload.club,
        distance_ft=payload.distance_ft,
        now=now,
    )
    db.add(bucket)

    if session.status == "active":
        session.updated_at = now

    await db.commit()
    await db.refresh(session)
    await db.refresh(bucket)
    return QuickLogResponse(
        session=SessionResponse.model_validate(session),
        bucket=BucketResponse.model_validate(bucket),
        active_session_created=active_session_created,
        standalone_session_created=standalone_session_created,
    )
