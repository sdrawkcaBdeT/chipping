from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.stats import build_session_detail, build_summary, load_practice_data

router = APIRouter(prefix="/public", tags=["public"])


async def _summary(db: AsyncSession) -> dict:
    return build_summary(await load_practice_data(db))


@router.get("/overview")
async def public_overview(db: AsyncSession = Depends(get_db)) -> dict:
    summary = await _summary(db)
    return summary["overview"]


@router.get("/volume")
async def public_volume(db: AsyncSession = Depends(get_db)) -> dict:
    summary = await _summary(db)
    return summary["volume"]


@router.get("/accuracy")
async def public_accuracy(db: AsyncSession = Depends(get_db)) -> dict:
    summary = await _summary(db)
    return summary["accuracy"]


@router.get("/targets")
async def public_targets(db: AsyncSession = Depends(get_db)) -> dict:
    summary = await _summary(db)
    return summary["targets"]


@router.get("/completion")
async def public_completion(db: AsyncSession = Depends(get_db)) -> dict:
    summary = await _summary(db)
    return summary["completion"]


@router.get("/sessions")
async def public_sessions(db: AsyncSession = Depends(get_db)) -> dict:
    summary = await _summary(db)
    return summary["sessions"]


@router.get("/sessions/{session_id}")
async def public_session_detail(
    session_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    detail = build_session_detail(await load_practice_data(db), session_id)
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return detail
