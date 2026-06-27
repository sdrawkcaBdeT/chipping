from fastapi.testclient import TestClient


def _login(client: TestClient) -> None:
    response = client.post("/api/auth/owner-login", json={"pin": "1234"})
    assert response.status_code == 200


def _seed_practice_data(client: TestClient) -> None:
    _login(client)
    start_response = client.post("/api/sessions/start", json={})
    assert start_response.status_code == 201
    session_id = start_response.json()["id"]
    game_response = client.post("/api/game-runs", json={"variant": "sequential"})
    assert game_response.status_code == 201
    game_id = game_response.json()["id"]

    client.post(f"/api/game-runs/{game_id}/target-completion/miss")
    client.post(f"/api/game-runs/{game_id}/target-completion/hit")
    for _ in range(8):
        client.post(f"/api/game-runs/{game_id}/target-completion/hit")

    stop_response = client.post(f"/api/sessions/{session_id}/stop")
    assert stop_response.status_code == 200

    standalone_response = client.post(
        "/api/quick-log",
        json={"ball_count": 21, "mode": "standalone"},
    )
    assert standalone_response.status_code == 201


def test_public_endpoints_do_not_require_auth(session_client):
    response = session_client.get("/api/public/overview")

    assert response.status_code == 200
    assert response.json()["total_sessions"] == 0


def test_public_stats_summarize_sessions_volume_completion_and_targets(session_client):
    _seed_practice_data(session_client)

    overview = session_client.get("/api/public/overview").json()
    volume = session_client.get("/api/public/volume").json()
    accuracy = session_client.get("/api/public/accuracy").json()
    targets = session_client.get("/api/public/targets").json()
    completion = session_client.get("/api/public/completion").json()
    sessions = session_client.get("/api/public/sessions").json()

    assert overview["total_sessions"] == 2
    assert overview["total_balls"] == 31
    assert overview["best_completion_score"] == 10
    assert volume["source_totals"]["target_completion"] == 10
    assert volume["source_totals"]["quick_log"] == 21
    assert accuracy == {
        "target_completion_attempts": 10,
        "hits": 9,
        "misses": 1,
        "hit_rate": 0.9,
    }
    assert targets["targets"][0]["target_number"] == 1
    assert targets["targets"][0]["average_balls_to_hit"] == 2
    assert completion["best_score"] == 10
    assert completion["completed_runs"][0]["score"] == 10
    assert len(sessions["sessions"]) == 2


def test_public_endpoints_are_read_only(session_client):
    response = session_client.post("/api/public/overview", json={})

    assert response.status_code == 405
