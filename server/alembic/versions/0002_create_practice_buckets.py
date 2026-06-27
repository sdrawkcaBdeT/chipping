"""create practice buckets

Revision ID: 0002_create_practice_buckets
Revises: 0001_create_practice_sessions
Create Date: 2026-06-26 23:05:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0002_create_practice_buckets"
down_revision: Union[str, None] = "0001_create_practice_sessions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "practice_buckets",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("session_id", sa.String(length=36), nullable=False),
        sa.Column("game_run_id", sa.String(length=36), nullable=True),
        sa.Column("ball_count", sa.Integer(), nullable=False),
        sa.Column("club", sa.String(length=64), nullable=False),
        sa.Column("distance_ft", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "status in ('active', 'completed')",
            name="practice_buckets_status_check",
        ),
        sa.CheckConstraint("ball_count >= 0", name="practice_buckets_ball_count_check"),
        sa.ForeignKeyConstraint(["session_id"], ["practice_sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_practice_buckets_game_run_id"),
        "practice_buckets",
        ["game_run_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_practice_buckets_session_id"),
        "practice_buckets",
        ["session_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_practice_buckets_session_id"), table_name="practice_buckets")
    op.drop_index(op.f("ix_practice_buckets_game_run_id"), table_name="practice_buckets")
    op.drop_table("practice_buckets")
