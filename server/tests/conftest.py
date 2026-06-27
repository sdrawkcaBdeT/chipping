from pathlib import Path
import sys
import asyncio

import pytest
from fastapi.testclient import TestClient


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import get_settings  # noqa: E402
from app.database import Base, get_engine, reset_database_caches  # noqa: E402
from app.main import create_app  # noqa: E402
import app.models  # noqa: F401, E402


@pytest.fixture
def session_client(monkeypatch, tmp_path):
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{tmp_path / 'test.db'}")
    monkeypatch.setenv("OWNER_PIN", "1234")
    monkeypatch.setenv("JWT_SECRET", "test-secret")
    monkeypatch.setenv("COOKIE_SECURE", "false")
    get_settings.cache_clear()
    reset_database_caches()

    async def prepare_database() -> None:
        async with get_engine().begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

    asyncio.run(prepare_database())
    client = TestClient(create_app())

    try:
        yield client
    finally:
        client.close()

        async def dispose_database() -> None:
            await get_engine().dispose()

        asyncio.run(dispose_database())
        reset_database_caches()
        get_settings.cache_clear()
