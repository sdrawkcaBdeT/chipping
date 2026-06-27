from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import PracticeBucket, PracticeSession
from app.models.session import utc_now
from app.security import require_owner

router = APIRouter(tags=["buckets"], dependencies=[Depends(require_owner)])

BucketStatus = Literal["active", "completed"]


class BucketResponse(BaseModel):
    id: str
    session_id: str
    game_run_id: str | None
    ball_count: int
    club: str
    distance_ft: int
    source: str
    status: BucketStatus
    started_at: datetime
    ended_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


async def bucket_or_404(bucket_id: str, db: AsyncSession) -> PracticeBucket:
    bucket = await db.get(PracticeBucket, bucket_id)
    if bucket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bucket not found")
    return bucket


@router.get("/sessions/{session_id}/buckets", response_model=list[BucketResponse])
async def list_session_buckets(
    session_id: str,
    db: AsyncSession = Depends(get_db),
) -> list[PracticeBucket]:
    session = await db.get(PracticeSession, session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    result = await db.execute(
        select(PracticeBucket)
        .where(PracticeBucket.session_id == session_id)
        .order_by(PracticeBucket.started_at.desc(), PracticeBucket.id)
    )
    return list(result.scalars().all())


@router.post("/buckets/{bucket_id}/end", response_model=BucketResponse)
async def end_bucket(
    bucket_id: str,
    db: AsyncSession = Depends(get_db),
) -> PracticeBucket:
    bucket = await bucket_or_404(bucket_id, db)
    if bucket.status == "completed":
        return bucket

    now = utc_now()
    bucket.status = "completed"
    bucket.ended_at = now
    bucket.updated_at = now
    await db.commit()
    await db.refresh(bucket)
    return bucket


@router.delete("/buckets/{bucket_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bucket(
    bucket_id: str,
    db: AsyncSession = Depends(get_db),
) -> Response:
    bucket = await bucket_or_404(bucket_id, db)
    await db.delete(bucket)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
