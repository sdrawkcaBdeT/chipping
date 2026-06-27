import asyncio

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.database import Base, get_engine, reset_database_caches
from app.main import create_app
import app.models  # noqa: F401


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


def _login(client: TestClient) -> None:
    response = client.post("/api/auth/owner-login", json={"pin": "1234"})
    assert response.status_code == 200


def test_session_routes_require_owner_auth(session_client):
    response = session_client.post("/api/sessions/start", json={})

    assert response.status_code == 401


def test_owner_can_start_and_stop_session(session_client):
    _login(session_client)

    start_response = session_client.post("/api/sessions/start", json={})
    active_response = session_client.get("/api/sessions/active")
    session_id = start_response.json()["id"]
    stop_response = session_client.post(f"/api/sessions/{session_id}/stop")

    assert start_response.status_code == 201
    assert start_response.json()["status"] == "active"
    assert active_response.status_code == 200
    assert active_response.json()["id"] == session_id
    assert stop_response.status_code == 200
    assert stop_response.json()["status"] == "completed"
    assert stop_response.json()["ended_at"] is not None


def test_only_one_active_session_is_allowed(session_client):
    _login(session_client)

    first_response = session_client.post("/api/sessions/start", json={})
    second_response = session_client.post("/api/sessions/start", json={})

    assert first_response.status_code == 201
    assert second_response.status_code == 409


def test_owner_can_create_multiple_distinct_sessions_same_day(session_client):
    _login(session_client)

    first_start = session_client.post("/api/sessions/start", json={})
    first_id = first_start.json()["id"]
    session_client.post(f"/api/sessions/{first_id}/stop")

    second_start = session_client.post("/api/sessions/start", json={})
    second_id = second_start.json()["id"]

    list_response = session_client.get("/api/sessions")
    sessions = list_response.json()

    assert first_start.status_code == 201
    assert second_start.status_code == 201
    assert first_id != second_id
    assert list_response.status_code == 200
    assert len(sessions) == 2
    assert {session["id"] for session in sessions} == {first_id, second_id}


def test_owner_can_abandon_active_session(session_client):
    _login(session_client)
    start_response = session_client.post("/api/sessions/start", json={})
    session_id = start_response.json()["id"]

    abandon_response = session_client.post(f"/api/sessions/{session_id}/abandon")

    assert abandon_response.status_code == 200
    assert abandon_response.json()["status"] == "abandoned"
    assert abandon_response.json()["ended_at"] is not None
