import sqlalchemy as sa
from alembic import command
from alembic.config import Config

from app.config import get_settings


FIRST_LIVE_APP_GIT_SHA = "d44fa987675a3043cf06d78047d41862a3a7123f"


def _alembic_config(database_url: str) -> Config:
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", database_url)
    return config


def test_session_provenance_migration_backfills_existing_sessions(tmp_path, monkeypatch):
    database_path = tmp_path / "migration.db"
    database_url = f"sqlite:///{database_path}"
    async_database_url = f"sqlite+aiosqlite:///{database_path}"
    monkeypatch.setenv("DATABASE_URL", async_database_url)
    get_settings.cache_clear()
    config = _alembic_config(database_url)

    command.upgrade(config, "0003_create_target_completion")
    engine = sa.create_engine(database_url)
    with engine.begin() as connection:
        connection.execute(
            sa.text(
                """
                INSERT INTO practice_sessions (
                    id,
                    started_at,
                    status,
                    default_club,
                    default_distance_ft,
                    notes,
                    created_at,
                    updated_at
                )
                VALUES (
                    'existing-session',
                    CURRENT_TIMESTAMP,
                    'completed',
                    '56',
                    15,
                    '',
                    CURRENT_TIMESTAMP,
                    CURRENT_TIMESTAMP
                )
                """
            )
        )
    engine.dispose()

    command.upgrade(config, "head")

    engine = sa.create_engine(database_url)
    with engine.connect() as connection:
        row = connection.execute(
            sa.text(
                """
                SELECT app_git_sha, app_build_version, design_version
                FROM practice_sessions
                WHERE id = 'existing-session'
                """
            )
        ).mappings().one()
    engine.dispose()

    assert row["app_git_sha"] == FIRST_LIVE_APP_GIT_SHA
    assert row["app_build_version"] == "d44fa98"
    assert row["design_version"] == "v0-manual-tracker"
    get_settings.cache_clear()
