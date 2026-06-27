from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.services.stats import build_session_detail, build_summary, load_practice_data

router = APIRouter(prefix="/public", tags=["public"])


async def _summary(db: AsyncSession) -> dict:
    return build_summary(await load_practice_data(db))


def _clean_optional_value(value: str | None) -> str | None:
    if value is None:
        return None
    clean_value = value.strip()
    return clean_value or None


@router.get("/build")
async def public_build() -> dict:
    settings = get_settings()
    app_git_sha = _clean_optional_value(settings.app_git_sha)
    return {
        "app_git_sha": app_git_sha,
        "app_build_version": _clean_optional_value(settings.app_build_version),
        "design_version": _clean_optional_value(settings.design_version) or "v1-dashboard-polish",
        "code_url": (
            f"https://github.com/sdrawkcaBdeT/chipping/tree/{app_git_sha}"
            if app_git_sha
            else None
        ),
    }


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
