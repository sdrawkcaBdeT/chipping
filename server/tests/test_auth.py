from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import create_app


def _auth_client(monkeypatch) -> TestClient:
    monkeypatch.setenv("OWNER_PIN", "1234")
    monkeypatch.setenv("JWT_SECRET", "test-secret")
    monkeypatch.setenv("COOKIE_SECURE", "false")
    get_settings.cache_clear()
    return TestClient(create_app())


def test_me_defaults_to_observer(monkeypatch):
    client = _auth_client(monkeypatch)

    response = client.get("/api/me")

    assert response.status_code == 200
    assert response.json() == {"mode": "observer"}


def test_owner_login_sets_cookie_and_me_returns_owner(monkeypatch):
    client = _auth_client(monkeypatch)

    login_response = client.post("/api/auth/owner-login", json={"pin": "1234"})
    me_response = client.get("/api/me")

    assert login_response.status_code == 200
    assert login_response.json() == {"mode": "owner"}
    assert me_response.status_code == 200
    assert me_response.json() == {"mode": "owner"}


def test_owner_login_rejects_invalid_pin(monkeypatch):
    client = _auth_client(monkeypatch)

    response = client.post("/api/auth/owner-login", json={"pin": "wrong"})

    assert response.status_code == 401


def test_owner_login_requires_configuration(monkeypatch):
    monkeypatch.setenv("OWNER_PIN", "")
    monkeypatch.setenv("OWNER_PASSWORD", "")
    monkeypatch.setenv("JWT_SECRET", "")
    get_settings.cache_clear()
    client = TestClient(create_app())

    response = client.post("/api/auth/owner-login", json={"pin": "1234"})

    assert response.status_code == 503


def test_logout_returns_to_observer(monkeypatch):
    client = _auth_client(monkeypatch)
    client.post("/api/auth/owner-login", json={"pin": "1234"})

    logout_response = client.post("/api/auth/logout")
    me_response = client.get("/api/me")

    assert logout_response.status_code == 200
    assert logout_response.json() == {"mode": "observer"}
    assert me_response.json() == {"mode": "observer"}
