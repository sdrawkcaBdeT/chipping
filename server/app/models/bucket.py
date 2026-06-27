from datetime import datetime
from uuid import uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.session import utc_now


class PracticeBucket(Base):
    __tablename__ = "practice_buckets"
    __table_args__ = (
        CheckConstraint(
            "status in ('active', 'completed')",
            name="practice_buckets_status_check",
        ),
        CheckConstraint("ball_count >= 0", name="practice_buckets_ball_count_check"),
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
    game_run_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    ball_count: Mapped[int] = mapped_column(Integer, nullable=False)
    club: Mapped[str] = mapped_column(String(64), default="56", nullable=False)
    distance_ft: Mapped[int] = mapped_column(Integer, default=15, nullable=False)
    source: Mapped[str] = mapped_column(String(32), default="quick_log", nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="completed", nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )
