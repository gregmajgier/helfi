from datetime import datetime, timedelta, timezone

DAY = "2026-10-06"


def _hours_ago(hours: float) -> str:
    return (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()


def test_water_accumulates_and_uses_default_goal(client, auth_headers):
    headers = auth_headers()
    client.post("/water", json={"day": DAY, "amount_ml": 250}, headers=headers)
    response = client.post("/water", json={"day": DAY, "amount_ml": 500}, headers=headers)
    body = response.json()
    assert body["total_ml"] == 750
    assert body["goal_ml"] == 2000
    assert len(body["entries"]) == 2
    assert client.get("/water", params={"day": "2026-10-07"}, headers=headers).json()["total_ml"] == 0


def test_water_goal_follows_profile_weight(client, auth_headers):
    headers = auth_headers()
    client.put(
        "/profile",
        json={"sex": "male", "birth_year": 1990, "height_cm": 180, "weight_kg": 80, "activity_level": "moderate", "goal": "maintain"},
        headers=headers,
    )
    assert client.get("/water", params={"day": DAY}, headers=headers).json()["goal_ml"] == 2800


def test_water_delete_returns_updated_day_and_is_private(client, auth_headers):
    owner = auth_headers(email="w1@example.com")
    other = auth_headers(email="w2@example.com")
    day = client.post("/water", json={"day": DAY, "amount_ml": 300}, headers=owner).json()
    entry_id = day["entries"][0]["id"]

    assert client.delete(f"/water/{entry_id}", headers=other).status_code == 404
    after = client.delete(f"/water/{entry_id}", headers=owner)
    assert after.status_code == 200
    assert after.json()["total_ml"] == 0


def test_water_limits(client, auth_headers):
    headers = auth_headers()
    assert client.post("/water", json={"day": DAY, "amount_ml": 0}, headers=headers).status_code == 422
    assert client.post("/water", json={"day": DAY, "amount_ml": 6000}, headers=headers).status_code == 422
    for _ in range(4):
        client.post("/water", json={"day": DAY, "amount_ml": 5000}, headers=headers)
    assert client.post("/water", json={"day": DAY, "amount_ml": 1000}, headers=headers).status_code == 400


def test_fast_lifecycle(client, auth_headers):
    headers = auth_headers()
    assert client.get("/fasting/current", headers=headers).json() is None

    started = client.post("/fasting/start", json={"protocol": "16:8", "started_at": _hours_ago(17)}, headers=headers)
    assert started.status_code == 201
    assert started.json()["target_hours"] == 16
    assert started.json()["completed"] is True

    current = client.get("/fasting/current", headers=headers).json()
    assert current["id"] == started.json()["id"]

    ended = client.post("/fasting/end", json={}, headers=headers).json()
    assert ended["ended_at"] is not None
    assert client.get("/fasting/current", headers=headers).json() is None


def test_only_one_active_fast(client, auth_headers):
    headers = auth_headers()
    client.post("/fasting/start", json={"protocol": "16:8"}, headers=headers)
    assert client.post("/fasting/start", json={"protocol": "18:6"}, headers=headers).status_code == 409


def test_custom_protocol_needs_hours_and_future_start_rejected(client, auth_headers):
    headers = auth_headers()
    assert client.post("/fasting/start", json={"protocol": "custom"}, headers=headers).status_code == 400
    future = (datetime.now(timezone.utc) + timedelta(hours=3)).isoformat()
    assert client.post("/fasting/start", json={"protocol": "16:8", "started_at": future}, headers=headers).status_code == 400
    ok = client.post("/fasting/start", json={"protocol": "custom", "target_hours": 36}, headers=headers)
    assert ok.status_code == 201
    assert ok.json()["target_hours"] == 36


def test_end_without_fast_is_404(client, auth_headers):
    assert client.post("/fasting/end", json={}, headers=auth_headers()).status_code == 404


def test_history_stats_and_streak(client, auth_headers):
    headers = auth_headers()

    def run(start_hours_ago: float, duration: float):
        started = datetime.now(timezone.utc) - timedelta(hours=start_hours_ago)
        client.post("/fasting/start", json={"protocol": "16:8", "started_at": started.isoformat()}, headers=headers)
        client.post("/fasting/end", json={"ended_at": (started + timedelta(hours=duration)).isoformat()}, headers=headers)

    run(120, 17)  # completed
    run(96, 10)  # missed target, breaks the streak
    run(72, 16)  # completed
    run(48, 18)  # completed

    history = client.get("/fasting/history", headers=headers).json()

    assert history["stats"]["total"] == 4
    assert history["stats"]["completed"] == 3
    assert history["stats"]["current_streak"] == 2
    assert history["stats"]["longest_hours"] == 18
    assert history["stats"]["average_hours"] == 15.2
    assert history["sessions"][0]["elapsed_hours"] == 18  # newest first


def test_fasts_are_private(client, auth_headers):
    owner = auth_headers(email="f1@example.com")
    other = auth_headers(email="f2@example.com")
    session_id = client.post("/fasting/start", json={"protocol": "16:8"}, headers=owner).json()["id"]
    assert client.get("/fasting/current", headers=other).json() is None
    assert client.delete(f"/fasting/{session_id}", headers=other).status_code == 404
    assert client.delete(f"/fasting/{session_id}", headers=owner).status_code == 204
