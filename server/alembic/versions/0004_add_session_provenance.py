"""add session provenance fields

Revision ID: 0004_add_session_provenance
Revises: 0003_create_target_completion
Create Date: 2026-06-27 00:40:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0004_add_session_provenance"
down_revision: Union[str, None] = "0003_create_target_completion"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("practice_sessions", sa.Column("app_git_sha", sa.String(length=64), nullable=True))
    op.add_column(
        "practice_sessions",
        sa.Column("app_build_version", sa.String(length=128), nullable=True),
    )
    op.add_column(
        "practice_sessions",
        sa.Column(
            "design_version",
            sa.String(length=64),
            nullable=False,
            server_default="v0-manual-tracker",
        ),
    )


def downgrade() -> None:
    op.drop_column("practice_sessions", "design_version")
    op.drop_column("practice_sessions", "app_build_version")
    op.drop_column("practice_sessions", "app_git_sha")
