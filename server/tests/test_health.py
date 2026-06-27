from fastapi.testclient import TestClient

from app.api import health as health_module
from app.main import app


async def _database_ok() -> None:
    return None


async def _database_unavailable() -> None:
    raise RuntimeError("database unavailable")


def test_health_returns_ok_when_database_is_available(monkeypatch):
    monkeypatch.setattr(health_module, "check_database_connection", _database_ok)

    client = TestClient(app)
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


def test_health_returns_service_unavailable_when_database_is_down(monkeypatch):
    monkeypatch.setattr(health_module, "check_database_connection", _database_unavailable)

    client = TestClient(app)
    response = client.get("/api/health")

    assert response.status_code == 503
    assert response.json() == {"status": "error", "database": "unavailable"}
