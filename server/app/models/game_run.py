from datetime import datetime
from uuid import uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.session import utc_now


class GameRun(Base):
    __tablename__ = "game_runs"
    __table_args__ = (
        CheckConstraint(
            "game_type in ('target_completion')",
            name="game_runs_game_type_check",
        ),
        CheckConstraint(
            "variant in ('sequential', 'random')",
            name="game_runs_variant_check",
        ),
        CheckConstraint(
            "status in ('active', 'completed', 'stopped')",
            name="game_runs_status_check",
        ),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    session_id: Mapped[str] = mapped_column(
        ForeignKey("practice_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    game_type: Mapped[str] = mapped_column(
        String(32),
        default="target_completion",
        nullable=False,
    )
    variant: Mapped[str] = mapped_column(String(24), nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="active", nullable=False)
    target_order: Mapped[list[int]] = mapped_column(JSON, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )


class TargetCompletionTarget(Base):
    __tablename__ = "target_completion_targets"
    __table_args__ = (
        CheckConstraint("target_number between 1 and 9", name="target_number_range_check"),
        CheckConstraint("attempts >= 0", name="target_attempts_non_negative_check"),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    game_run_id: Mapped[str] = mapped_column(
        ForeignKey("game_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    target_number: Mapped[int] = mapped_column(Integer, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    hit: Mapped[bool] = mapped_column(default=False, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )


class TargetCompletionEvent(Base):
    __tablename__ = "target_completion_events"
    __table_args__ = (
        CheckConstraint("action in ('miss', 'hit')", name="target_event_action_check"),
        CheckConstraint("target_number between 1 and 9", name="target_event_number_range_check"),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    game_run_id: Mapped[str] = mapped_column(
        ForeignKey("game_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    bucket_id: Mapped[str] = mapped_column(
        ForeignKey("practice_buckets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    target_number: Mapped[int] = mapped_column(Integer, nullable=False)
    action: Mapped[str] = mapped_column(String(16), nullable=False)
    event_index: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
