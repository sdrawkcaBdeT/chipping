from fastapi.testclient import TestClient


def _login(client: TestClient) -> None:
    response = client.post("/api/auth/owner-login", json={"pin": "1234"})
    assert response.status_code == 200


def _seed_practice_data(client: TestClient) -> None:
    _login(client)
    start_response = client.post("/api/sessions/start", json={})
    assert start_response.status_code == 201
    session_id = start_response.json()["id"]
    quick_log_response = client.post("/api/quick-log", json={"ball_count": 42})
    assert quick_log_response.status_code == 201
    stop_response = client.post(f"/api/sessions/{session_id}/stop")
    assert stop_response.status_code == 200


def test_export_and_prompt_routes_require_owner_auth(session_client):
    json_response = session_client.get("/api/export/json")
    csv_response = session_client.get("/api/export/csv")
    prompt_response = session_client.get("/api/prompts/practice-summary")

    assert json_response.status_code == 401
    assert csv_response.status_code == 401
    assert prompt_response.status_code == 401


def test_owner_can_export_json(session_client):
    _seed_practice_data(session_client)

    response = session_client.get("/api/export/json")
    payload = response.json()

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert payload["summary"]["overview"]["total_balls"] == 42
    assert len(payload["sessions"]) == 1
    assert len(payload["buckets"]) == 1


def test_owner_can_export_csv(session_client):
    _seed_practice_data(session_client)

    response = session_client.get("/api/export/csv")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "record_type,id,session_id" in response.text
    assert "bucket" in response.text
    assert "42" in response.text


def test_owner_can_generate_prompt_helper(session_client):
    _seed_practice_data(session_client)

    response = session_client.get("/api/prompts/practice-summary")
    payload = response.json()

    assert response.status_code == 200
    assert "golf chipping practice log" in payload["prompt"]
    assert payload["summary"]["overview"]["total_balls"] == 42
