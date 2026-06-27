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


FIRST_LIVE_APP_GIT_SHA = "d44fa987675a3043cf06d78047d41862a3a7123f"
FIRST_LIVE_APP_BUILD_VERSION = "d44fa98"
FIRST_LIVE_DESIGN_VERSION = "v0-manual-tracker"


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
    op.execute(
        sa.text(
            """
            UPDATE practice_sessions
            SET app_git_sha = :app_git_sha,
                app_build_version = :app_build_version,
                design_version = :design_version
            """
        ).bindparams(
            app_git_sha=FIRST_LIVE_APP_GIT_SHA,
            app_build_version=FIRST_LIVE_APP_BUILD_VERSION,
            design_version=FIRST_LIVE_DESIGN_VERSION,
        )
    )


def downgrade() -> None:
    op.drop_column("practice_sessions", "design_version")
    op.drop_column("practice_sessions", "app_build_version")
    op.drop_column("practice_sessions", "app_git_sha")
