from fastapi.testclient import TestClient


def _login(client: TestClient) -> None:
    response = client.post("/api/auth/owner-login", json={"pin": "1234"})
    assert response.status_code == 200


def _start_session(client: TestClient) -> str:
    response = client.post("/api/sessions/start", json={})
    assert response.status_code == 201
    return response.json()["id"]


def _start_game(client: TestClient, variant: str = "sequential") -> dict:
    response = client.post("/api/game-runs", json={"variant": variant})
    assert response.status_code == 201
    return response.json()


def test_game_run_routes_require_owner_auth(session_client):
    response = session_client.post("/api/game-runs", json={"variant": "sequential"})

    assert response.status_code == 401


def test_target_completion_requires_active_session(session_client):
    _login(session_client)

    response = session_client.post("/api/game-runs", json={"variant": "sequential"})

    assert response.status_code == 409
    assert "Start a session" in response.json()["detail"]


def test_sequential_target_completion_starts_with_targets_one_to_nine(session_client):
    _login(session_client)
    session_id = _start_session(session_client)

    game = _start_game(session_client, "sequential")

    assert game["session_id"] == session_id
    assert game["variant"] == "sequential"
    assert game["status"] == "active"
    assert game["target_order"] == [1, 2, 3, 4, 5, 6, 7, 8, 9]
    assert game["current_target"]["target_number"] == 1
    assert game["total_balls_used"] == 0
    assert game["current_bucket_balls"] == 0
    assert game["active_bucket"]["status"] == "active"


def test_random_target_completion_has_all_targets(session_client):
    _login(session_client)
    _start_session(session_client)

    game = _start_game(session_client, "random")

    assert game["variant"] == "random"
    assert sorted(game["target_order"]) == [1, 2, 3, 4, 5, 6, 7, 8, 9]
    assert len(set(game["target_order"])) == 9
    assert game["current_target"]["target_number"] == game["target_order"][0]


def test_miss_and_hit_record_balls_to_hit_and_move_target(session_client):
    _login(session_client)
    _start_session(session_client)
    game = _start_game(session_client)
    game_id = game["id"]

    miss_response = session_client.post(f"/api/game-runs/{game_id}/target-completion/miss")
    hit_response = session_client.post(f"/api/game-runs/{game_id}/target-completion/hit")
    game_after_hit = hit_response.json()
    first_target = game_after_hit["targets"][0]

    assert miss_response.status_code == 200
    assert miss_response.json()["current_target"]["attempts"] == 1
    assert miss_response.json()["total_balls_used"] == 1
    assert miss_response.json()["current_bucket_balls"] == 1
    assert hit_response.status_code == 200
    assert first_target["target_number"] == 1
    assert first_target["attempts"] == 2
    assert first_target["hit"] is True
    assert game_after_hit["current_target"]["target_number"] == 2
    assert game_after_hit["completed_targets"] == [1]
    assert game_after_hit["total_balls_used"] == 2
    assert game_after_hit["current_bucket_balls"] == 2


def test_undo_reverses_last_hit(session_client):
    _login(session_client)
    _start_session(session_client)
    game_id = _start_game(session_client)["id"]
    session_client.post(f"/api/game-runs/{game_id}/target-completion/miss")
    session_client.post(f"/api/game-runs/{game_id}/target-completion/hit")

    undo_response = session_client.post(f"/api/game-runs/{game_id}/undo")
    game = undo_response.json()

    assert undo_response.status_code == 200
    assert game["status"] == "active"
    assert game["current_target"]["target_number"] == 1
    assert game["current_target"]["attempts"] == 1
    assert game["completed_targets"] == []
    assert game["total_balls_used"] == 1
    assert game["current_bucket_balls"] == 1


def test_target_completion_can_span_retrieval_buckets(session_client):
    _login(session_client)
    session_id = _start_session(session_client)
    game_id = _start_game(session_client)["id"]
    session_client.post(f"/api/game-runs/{game_id}/target-completion/miss")
    first_state = session_client.get(f"/api/game-runs/{game_id}").json()
    first_bucket_id = first_state["active_bucket"]["id"]

    end_response = session_client.post(f"/api/buckets/{first_bucket_id}/end")
    next_miss_response = session_client.post(
        f"/api/game-runs/{game_id}/target-completion/miss"
    )
    buckets_response = session_client.get(f"/api/sessions/{session_id}/buckets")
    buckets = buckets_response.json()

    assert end_response.status_code == 200
    assert end_response.json()["status"] == "completed"
    assert next_miss_response.status_code == 200
    assert next_miss_response.json()["current_bucket_balls"] == 1
    assert next_miss_response.json()["active_bucket"]["id"] != first_bucket_id
    assert len(buckets) == 2
    assert sum(bucket["ball_count"] for bucket in buckets) == 2


def test_game_completes_after_all_targets_hit_and_session_stays_active(session_client):
    _login(session_client)
    _start_session(session_client)
    game_id = _start_game(session_client)["id"]

    state = None
    for _ in range(9):
        response = session_client.post(f"/api/game-runs/{game_id}/target-completion/hit")
        state = response.json()

    active_session_response = session_client.get("/api/sessions/active")

    assert state is not None
    assert state["status"] == "completed"
    assert state["ended_at"] is not None
    assert state["current_target"] is None
    assert state["completed_targets"] == [1, 2, 3, 4, 5, 6, 7, 8, 9]
    assert state["total_balls_used"] == 9
    assert state["active_bucket"] is None
    assert active_session_response.status_code == 200
    assert active_session_response.json()["status"] == "active"


def test_undo_reopens_completed_game(session_client):
    _login(session_client)
    _start_session(session_client)
    game_id = _start_game(session_client)["id"]
    for _ in range(9):
        session_client.post(f"/api/game-runs/{game_id}/target-completion/hit")

    undo_response = session_client.post(f"/api/game-runs/{game_id}/undo")
    game = undo_response.json()

    assert undo_response.status_code == 200
    assert game["status"] == "active"
    assert game["current_target"]["target_number"] == 9
    assert game["total_balls_used"] == 8
    assert game["active_bucket"] is not None


def test_stop_game_does_not_stop_session(session_client):
    _login(session_client)
    _start_session(session_client)
    game_id = _start_game(session_client)["id"]
    session_client.post(f"/api/game-runs/{game_id}/target-completion/miss")

    stop_response = session_client.post(f"/api/game-runs/{game_id}/stop")
    active_session_response = session_client.get("/api/sessions/active")
    miss_after_stop = session_client.post(f"/api/game-runs/{game_id}/target-completion/miss")

    assert stop_response.status_code == 200
    assert stop_response.json()["status"] == "stopped"
    assert stop_response.json()["active_bucket"] is None
    assert active_session_response.status_code == 200
    assert active_session_response.json()["status"] == "active"
    assert miss_after_stop.status_code == 409


def test_stop_session_stops_active_game(session_client):
    _login(session_client)
    _start_session(session_client)
    game_id = _start_game(session_client)["id"]

    active_session = session_client.get("/api/sessions/active").json()
    stop_session_response = session_client.post(f"/api/sessions/{active_session['id']}/stop")
    game_response = session_client.get(f"/api/game-runs/{game_id}")

    assert stop_session_response.status_code == 200
    assert stop_session_response.json()["status"] == "completed"
    assert game_response.status_code == 200
    assert game_response.json()["status"] == "stopped"


def test_only_one_active_game_is_allowed(session_client):
    _login(session_client)
    _start_session(session_client)
    _start_game(session_client)

    second_response = session_client.post("/api/game-runs", json={"variant": "random"})

    assert second_response.status_code == 409


def test_empty_game_undo_returns_conflict(session_client):
    _login(session_client)
    _start_session(session_client)
    game_id = _start_game(session_client)["id"]

    response = session_client.post(f"/api/game-runs/{game_id}/undo")

    assert response.status_code == 409
    assert "Nothing to undo" in response.json()["detail"]
