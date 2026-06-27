from fastapi.testclient import TestClient


def _login(client: TestClient) -> None:
    response = client.post("/api/auth/owner-login", json={"pin": "1234"})
    assert response.status_code == 200


def test_quick_log_requires_owner_auth(session_client):
    response = session_client.post("/api/quick-log", json={"ball_count": 42})

    assert response.status_code == 401


def test_quick_log_requires_explicit_mode_without_active_session(session_client):
    _login(session_client)

    response = session_client.post("/api/quick-log", json={"ball_count": 42})

    assert response.status_code == 409
    assert "No active session" in response.json()["detail"]


def test_quick_log_adds_bucket_to_active_session(session_client):
    _login(session_client)
    start_response = session_client.post("/api/sessions/start", json={})
    session_id = start_response.json()["id"]

    quick_log_response = session_client.post("/api/quick-log", json={"ball_count": 42})
    bucket = quick_log_response.json()["bucket"]
    buckets_response = session_client.get(f"/api/sessions/{session_id}/buckets")

    assert quick_log_response.status_code == 201
    assert quick_log_response.json()["session"]["id"] == session_id
    assert quick_log_response.json()["active_session_created"] is False
    assert bucket["session_id"] == session_id
    assert bucket["ball_count"] == 42
    assert bucket["club"] == "56"
    assert bucket["distance_ft"] == 15
    assert bucket["status"] == "completed"
    assert buckets_response.status_code == 200
    assert [item["id"] for item in buckets_response.json()] == [bucket["id"]]


def test_quick_log_can_start_session_and_log(session_client):
    _login(session_client)

    quick_log_response = session_client.post(
        "/api/quick-log",
        json={"ball_count": 21, "mode": "start_session"},
    )
    active_response = session_client.get("/api/sessions/active")

    assert quick_log_response.status_code == 201
    assert quick_log_response.json()["active_session_created"] is True
    assert quick_log_response.json()["standalone_session_created"] is False
    assert quick_log_response.json()["session"]["status"] == "active"
    assert quick_log_response.json()["bucket"]["ball_count"] == 21
    assert active_response.status_code == 200
    assert active_response.json()["id"] == quick_log_response.json()["session"]["id"]


def test_quick_log_can_create_standalone_completed_session(session_client):
    _login(session_client)

    quick_log_response = session_client.post(
        "/api/quick-log",
        json={"ball_count": 10, "mode": "standalone", "club": "60", "distance_ft": 20},
    )
    active_response = session_client.get("/api/sessions/active")

    assert quick_log_response.status_code == 201
    assert quick_log_response.json()["standalone_session_created"] is True
    assert quick_log_response.json()["session"]["status"] == "completed"
    assert quick_log_response.json()["session"]["ended_at"] is not None
    assert quick_log_response.json()["bucket"]["ball_count"] == 10
    assert quick_log_response.json()["bucket"]["club"] == "60"
    assert quick_log_response.json()["bucket"]["distance_ft"] == 20
    assert active_response.status_code == 200
    assert active_response.json() is None


def test_quick_log_rejects_invalid_ball_count(session_client):
    _login(session_client)

    response = session_client.post(
        "/api/quick-log",
        json={"ball_count": 0, "mode": "standalone"},
    )

    assert response.status_code == 422


def test_end_bucket_is_idempotent_for_completed_bucket(session_client):
    _login(session_client)
    quick_log_response = session_client.post(
        "/api/quick-log",
        json={"ball_count": 42, "mode": "standalone"},
    )
    bucket_id = quick_log_response.json()["bucket"]["id"]

    end_response = session_client.post(f"/api/buckets/{bucket_id}/end")

    assert end_response.status_code == 200
    assert end_response.json()["id"] == bucket_id
    assert end_response.json()["status"] == "completed"
