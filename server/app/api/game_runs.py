import random
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.buckets import BucketResponse
from app.database import get_db
from app.models import (
    GameRun,
    PracticeBucket,
    PracticeSession,
    TargetCompletionEvent,
    TargetCompletionTarget,
)
from app.models.session import utc_now
from app.security import require_owner

router = APIRouter(
    prefix="/game-runs",
    tags=["game-runs"],
    dependencies=[Depends(require_owner)],
)

GameRunStatus = Literal["active", "completed", "stopped"]
TargetCompletionVariant = Literal["sequential", "random"]


class GameRunCreateRequest(BaseModel):
    game_type: Literal["target_completion"] = "target_completion"
    variant: TargetCompletionVariant = "sequential"


class TargetCompletionTargetResponse(BaseModel):
    target_number: int
    order_index: int
    attempts: int
    hit: bool
    completed_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class GameRunResponse(BaseModel):
    id: str
    session_id: str
    game_type: Literal["target_completion"]
    variant: TargetCompletionVariant
    status: GameRunStatus
    target_order: list[int]
    started_at: datetime
    ended_at: datetime | None
    targets: list[TargetCompletionTargetResponse]
    current_target: TargetCompletionTargetResponse | None
    completed_targets: list[int]
    total_balls_used: int
    current_bucket_balls: int
    active_bucket: BucketResponse | None


async def _active_session(db: AsyncSession) -> PracticeSession | None:
    result = await db.execute(
        select(PracticeSession)
        .where(PracticeSession.status == "active")
        .order_by(PracticeSession.started_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def _active_game(db: AsyncSession, session_id: str | None = None) -> GameRun | None:
    query = select(GameRun).where(GameRun.status == "active")
    if session_id is not None:
        query = query.where(GameRun.session_id == session_id)
    result = await db.execute(query.order_by(GameRun.started_at.desc()).limit(1))
    return result.scalar_one_or_none()


async def _game_or_404(game_run_id: str, db: AsyncSession) -> GameRun:
    game = await db.get(GameRun, game_run_id)
    if game is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game run not found")
    return game


async def _targets_for_game(
    game_run_id: str,
    db: AsyncSession,
) -> list[TargetCompletionTarget]:
    result = await db.execute(
        select(TargetCompletionTarget)
        .where(TargetCompletionTarget.game_run_id == game_run_id)
        .order_by(TargetCompletionTarget.order_index)
    )
    return list(result.scalars().all())


async def _target_for_number(
    game_run_id: str,
    target_number: int,
    db: AsyncSession,
) -> TargetCompletionTarget:
    result = await db.execute(
        select(TargetCompletionTarget).where(
            TargetCompletionTarget.game_run_id == game_run_id,
            TargetCompletionTarget.target_number == target_number,
        )
    )
    target = result.scalar_one_or_none()
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target not found")
    return target


async def _active_bucket(game_run_id: str, db: AsyncSession) -> PracticeBucket | None:
    result = await db.execute(
        select(PracticeBucket)
        .where(
            PracticeBucket.game_run_id == game_run_id,
            PracticeBucket.status == "active",
        )
        .order_by(PracticeBucket.started_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def _bucket_for_action(game: GameRun, db: AsyncSession) -> PracticeBucket:
    bucket = await _active_bucket(game.id, db)
    if bucket is not None:
        return bucket

    session = await db.get(PracticeSession, game.session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    now = utc_now()
    bucket = PracticeBucket(
        session_id=game.session_id,
        game_run_id=game.id,
        ball_count=0,
        club=session.default_club,
        distance_ft=session.default_distance_ft,
        source="target_completion",
        status="active",
        started_at=now,
        created_at=now,
        updated_at=now,
    )
    db.add(bucket)
    await db.flush()
    return bucket


async def _next_event_index(game_run_id: str, db: AsyncSession) -> int:
    result = await db.execute(
        select(func.coalesce(func.max(TargetCompletionEvent.event_index), 0)).where(
            TargetCompletionEvent.game_run_id == game_run_id
        )
    )
    return int(result.scalar_one()) + 1


async def _last_event(game_run_id: str, db: AsyncSession) -> TargetCompletionEvent | None:
    result = await db.execute(
        select(TargetCompletionEvent)
        .where(TargetCompletionEvent.game_run_id == game_run_id)
        .order_by(TargetCompletionEvent.event_index.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def _game_response(game: GameRun, db: AsyncSession) -> GameRunResponse:
    targets = await _targets_for_game(game.id, db)
    current_target = next((target for target in targets if not target.hit), None)
    active_bucket = await _active_bucket(game.id, db)

    return GameRunResponse(
        id=game.id,
        session_id=game.session_id,
        game_type="target_completion",
        variant=game.variant,
        status=game.status,
        target_order=game.target_order,
        started_at=game.started_at,
        ended_at=game.ended_at,
        targets=[TargetCompletionTargetResponse.model_validate(target) for target in targets],
        current_target=(
            TargetCompletionTargetResponse.model_validate(current_target)
            if current_target is not None
            else None
        ),
        completed_targets=[target.target_number for target in targets if target.hit],
        total_balls_used=sum(target.attempts for target in targets),
        current_bucket_balls=active_bucket.ball_count if active_bucket is not None else 0,
        active_bucket=(
            BucketResponse.model_validate(active_bucket) if active_bucket is not None else None
        ),
    )


def _target_order_for_variant(variant: TargetCompletionVariant) -> list[int]:
    target_order = list(range(1, 10))
    if variant == "random":
        random.shuffle(target_order)
    return target_order


def _require_active_game(game: GameRun) -> None:
    if game.status != "active":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only active games can be changed",
        )


async def _record_target_event(
    game: GameRun,
    target: TargetCompletionTarget,
    action: Literal["miss", "hit"],
    db: AsyncSession,
) -> None:
    now = utc_now()
    bucket = await _bucket_for_action(game, db)
    bucket.ball_count += 1
    bucket.updated_at = now
    target.attempts += 1
    target.updated_at = now

    if action == "hit":
        target.hit = True
        target.completed_at = now

    db.add(
        TargetCompletionEvent(
            game_run_id=game.id,
            bucket_id=bucket.id,
            target_number=target.target_number,
            action=action,
            event_index=await _next_event_index(game.id, db),
            created_at=now,
        )
    )

    targets = await _targets_for_game(game.id, db)
    if action == "hit" and all(item.hit or item.id == target.id for item in targets):
        game.status = "completed"
        game.ended_at = now
        bucket.status = "completed"
        bucket.ended_at = now

    game.updated_at = now


@router.post("", response_model=GameRunResponse, status_code=status.HTTP_201_CREATED)
async def create_game_run(
    payload: GameRunCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> GameRunResponse:
    session = await _active_session(db)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Start a session before starting a game",
        )

    existing_game = await _active_game(db, session.id)
    if existing_game is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An active game already exists",
        )

    now = utc_now()
    target_order = _target_order_for_variant(payload.variant)
    game = GameRun(
        session_id=session.id,
        game_type=payload.game_type,
        variant=payload.variant,
        target_order=target_order,
        started_at=now,
        created_at=now,
        updated_at=now,
    )
    db.add(game)
    await db.flush()

    db.add_all(
        [
            TargetCompletionTarget(
                game_run_id=game.id,
                target_number=target_number,
                order_index=index,
                attempts=0,
                hit=False,
                created_at=now,
                updated_at=now,
            )
            for index, target_number in enumerate(target_order)
        ]
    )
    db.add(
        PracticeBucket(
            session_id=session.id,
            game_run_id=game.id,
            ball_count=0,
            club=session.default_club,
            distance_ft=session.default_distance_ft,
            source="target_completion",
            status="active",
            started_at=now,
            created_at=now,
            updated_at=now,
        )
    )

    await db.commit()
    await db.refresh(game)
    return await _game_response(game, db)


@router.get("/active", response_model=GameRunResponse | None)
async def get_active_game_run(db: AsyncSession = Depends(get_db)) -> GameRunResponse | None:
    session = await _active_session(db)
    if session is None:
        return None

    game = await _active_game(db, session.id)
    if game is None:
        return None

    return await _game_response(game, db)


@router.get("/{game_run_id}", response_model=GameRunResponse)
async def get_game_run(
    game_run_id: str,
    db: AsyncSession = Depends(get_db),
) -> GameRunResponse:
    game = await _game_or_404(game_run_id, db)
    return await _game_response(game, db)


@router.post("/{game_run_id}/stop", response_model=GameRunResponse)
async def stop_game_run(
    game_run_id: str,
    db: AsyncSession = Depends(get_db),
) -> GameRunResponse:
    game = await _game_or_404(game_run_id, db)
    _require_active_game(game)

    now = utc_now()
    bucket = await _active_bucket(game.id, db)
    game.status = "stopped"
    game.ended_at = now
    game.updated_at = now
    if bucket is not None:
        bucket.status = "completed"
        bucket.ended_at = now
        bucket.updated_at = now

    await db.commit()
    await db.refresh(game)
    return await _game_response(game, db)


@router.post("/{game_run_id}/buckets", response_model=BucketResponse, status_code=201)
async def start_game_bucket(
    game_run_id: str,
    db: AsyncSession = Depends(get_db),
) -> PracticeBucket:
    game = await _game_or_404(game_run_id, db)
    _require_active_game(game)
    bucket = await _bucket_for_action(game, db)
    await db.commit()
    await db.refresh(bucket)
    return bucket


@router.post("/{game_run_id}/target-completion/miss", response_model=GameRunResponse)
async def target_completion_miss(
    game_run_id: str,
    db: AsyncSession = Depends(get_db),
) -> GameRunResponse:
    game = await _game_or_404(game_run_id, db)
    _require_active_game(game)
    targets = await _targets_for_game(game.id, db)
    target = next((item for item in targets if not item.hit), None)
    if target is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Game is complete")

    await _record_target_event(game, target, "miss", db)
    await db.commit()
    await db.refresh(game)
    return await _game_response(game, db)


@router.post("/{game_run_id}/target-completion/hit", response_model=GameRunResponse)
async def target_completion_hit(
    game_run_id: str,
    db: AsyncSession = Depends(get_db),
) -> GameRunResponse:
    game = await _game_or_404(game_run_id, db)
    _require_active_game(game)
    targets = await _targets_for_game(game.id, db)
    target = next((item for item in targets if not item.hit), None)
    if target is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Game is complete")

    await _record_target_event(game, target, "hit", db)
    await db.commit()
    await db.refresh(game)
    return await _game_response(game, db)


@router.post("/{game_run_id}/undo", response_model=GameRunResponse)
async def undo_game_run_event(
    game_run_id: str,
    db: AsyncSession = Depends(get_db),
) -> GameRunResponse:
    game = await _game_or_404(game_run_id, db)
    if game.status == "stopped":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Stopped games cannot be changed",
        )

    event = await _last_event(game.id, db)
    if event is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Nothing to undo")

    now = utc_now()
    target = await _target_for_number(game.id, event.target_number, db)
    bucket = await db.get(PracticeBucket, event.bucket_id)

    target.attempts = max(0, target.attempts - 1)
    target.updated_at = now
    if event.action == "hit":
        target.hit = False
        target.completed_at = None

    if bucket is not None:
        bucket.ball_count = max(0, bucket.ball_count - 1)
        bucket.updated_at = now
        if game.status == "completed":
            bucket.status = "active"
            bucket.ended_at = None

    if game.status == "completed":
        game.status = "active"
        game.ended_at = None
    game.updated_at = now

    await db.delete(event)
    await db.commit()
    await db.refresh(game)
    return await _game_response(game, db)
