"""create target completion game tables

Revision ID: 0003_create_target_completion
Revises: 0002_create_practice_buckets
Create Date: 2026-06-27 00:10:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0003_create_target_completion"
down_revision: Union[str, None] = "0002_create_practice_buckets"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "game_runs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("session_id", sa.String(length=36), nullable=False),
        sa.Column("game_type", sa.String(length=32), nullable=False),
        sa.Column("variant", sa.String(length=24), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("target_order", sa.JSON(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "game_type in ('target_completion')",
            name="game_runs_game_type_check",
        ),
        sa.CheckConstraint(
            "variant in ('sequential', 'random')",
            name="game_runs_variant_check",
        ),
        sa.CheckConstraint(
            "status in ('active', 'completed', 'stopped')",
            name="game_runs_status_check",
        ),
        sa.ForeignKeyConstraint(["session_id"], ["practice_sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_game_runs_session_id"), "game_runs", ["session_id"], unique=False)

    op.create_table(
        "target_completion_targets",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("game_run_id", sa.String(length=36), nullable=False),
        sa.Column("target_number", sa.Integer(), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("hit", sa.Boolean(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("target_number between 1 and 9", name="target_number_range_check"),
        sa.CheckConstraint("attempts >= 0", name="target_attempts_non_negative_check"),
        sa.ForeignKeyConstraint(["game_run_id"], ["game_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_target_completion_targets_game_run_id"),
        "target_completion_targets",
        ["game_run_id"],
        unique=False,
    )

    op.create_table(
        "target_completion_events",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("game_run_id", sa.String(length=36), nullable=False),
        sa.Column("bucket_id", sa.String(length=36), nullable=False),
        sa.Column("target_number", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(length=16), nullable=False),
        sa.Column("event_index", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("action in ('miss', 'hit')", name="target_event_action_check"),
        sa.CheckConstraint(
            "target_number between 1 and 9",
            name="target_event_number_range_check",
        ),
        sa.ForeignKeyConstraint(["bucket_id"], ["practice_buckets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["game_run_id"], ["game_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_target_completion_events_bucket_id"),
        "target_completion_events",
        ["bucket_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_target_completion_events_game_run_id"),
        "target_completion_events",
        ["game_run_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_target_completion_events_game_run_id"),
        table_name="target_completion_events",
    )
    op.drop_index(
        op.f("ix_target_completion_events_bucket_id"),
        table_name="target_completion_events",
    )
    op.drop_table("target_completion_events")
    op.drop_index(
        op.f("ix_target_completion_targets_game_run_id"),
        table_name="target_completion_targets",
    )
    op.drop_table("target_completion_targets")
    op.drop_index(op.f("ix_game_runs_session_id"), table_name="game_runs")
    op.drop_table("game_runs")
