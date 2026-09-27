def test_search_exercises_matches_partial_case_insensitive_name(client, auth_headers):
    headers = auth_headers()

    response = client.get("/workouts/exercises", params={"q": "BENCH"}, headers=headers)

    assert response.status_code == 200
    names = [e["name"] for e in response.json()]
    assert any("Bench" in name for name in names)


def test_search_exercises_requires_auth(client):
    response = client.get("/workouts/exercises", params={"q": "bench"})

    assert response.status_code == 401


def test_create_custom_exercise_is_then_searchable_by_other_users(client, auth_headers):
    headers_a = auth_headers(email="creator@example.com")
    headers_b = auth_headers(email="other@example.com")

    create = client.post(
        "/workouts/exercises",
        json={"name": "Cable Row", "category": "back", "is_bodyweight": False},
        headers=headers_a,
    )
    assert create.status_code == 201
    assert create.json()["created_by_user_id"]

    search = client.get("/workouts/exercises", params={"q": "cable"}, headers=headers_b)

    assert search.status_code == 200
    assert any(e["name"] == "Cable Row" for e in search.json())


STRENGTH_PAYLOAD = {
    "type": "strength",
    "started_at": "2026-09-16T07:00:00Z",
    "duration_s": 3600,
    "exercises": [
        {"exercise_id": "bench-press", "sets": [{"reps": 8, "weight_kg": 60}, {"reps": 6, "weight_kg": 65}]}
    ],
}

CARDIO_PAYLOAD = {
    "type": "running",
    "started_at": "2026-09-16T06:00:00Z",
    "duration_s": 1800,
    "distance_m": 5000,
    "avg_pace_s_per_km": 360,
}


def test_create_and_list_strength_workout(client, auth_headers):
    headers = auth_headers()

    create = client.post("/workouts", json=STRENGTH_PAYLOAD, headers=headers)
    assert create.status_code == 201
    assert create.json()["source"] == "manual"

    listing = client.get("/workouts", headers=headers)
    assert listing.status_code == 200
    assert len(listing.json()) == 1
    assert listing.json()[0]["exercises"][0]["exercise_id"] == "bench-press"


def test_create_and_list_cardio_workout(client, auth_headers):
    headers = auth_headers()

    create = client.post("/workouts", json=CARDIO_PAYLOAD, headers=headers)
    assert create.status_code == 201

    listing = client.get("/workouts", params={"type": "running"}, headers=headers)
    assert listing.status_code == 200
    assert listing.json()[0]["distance_m"] == 5000


def test_list_workouts_with_invalid_type_returns_422(client, auth_headers):
    headers = auth_headers()

    response = client.get("/workouts", params={"type": "swimming"}, headers=headers)

    assert response.status_code == 422


def test_strength_workout_without_exercises_is_rejected(client, auth_headers):
    headers = auth_headers()
    payload = {**STRENGTH_PAYLOAD, "exercises": []}

    response = client.post("/workouts", json=payload, headers=headers)

    assert response.status_code == 422


def test_cardio_workout_without_distance_is_rejected(client, auth_headers):
    headers = auth_headers()
    payload = {k: v for k, v in CARDIO_PAYLOAD.items() if k != "distance_m"}

    response = client.post("/workouts", json=payload, headers=headers)

    assert response.status_code == 422


def test_workout_with_negative_values_is_rejected(client, auth_headers):
    headers = auth_headers()
    negative_duration = {**CARDIO_PAYLOAD, "duration_s": -100}
    negative_reps = {
        **STRENGTH_PAYLOAD,
        "exercises": [{"exercise_id": "bench-press", "sets": [{"reps": -1}]}],
    }

    assert client.post("/workouts", json=negative_duration, headers=headers).status_code == 422
    assert client.post("/workouts", json=negative_reps, headers=headers).status_code == 422


def test_update_and_delete_own_workout(client, auth_headers):
    headers = auth_headers()
    workout_id = client.post("/workouts", json=CARDIO_PAYLOAD, headers=headers).json()["id"]

    update = client.patch(f"/workouts/{workout_id}", json={"duration_s": 1700}, headers=headers)
    assert update.status_code == 200
    assert update.json()["duration_s"] == 1700

    delete = client.delete(f"/workouts/{workout_id}", headers=headers)
    assert delete.status_code == 204

    listing = client.get("/workouts", headers=headers)
    assert listing.json() == []


def test_user_cannot_read_or_modify_another_users_workout(client, auth_headers):
    headers_a = auth_headers(email="owner3@example.com")
    headers_b = auth_headers(email="intruder3@example.com")
    workout_id = client.post("/workouts", json=CARDIO_PAYLOAD, headers=headers_a).json()["id"]

    update = client.patch(f"/workouts/{workout_id}", json={"duration_s": 1}, headers=headers_b)
    assert update.status_code == 404

    delete = client.delete(f"/workouts/{workout_id}", headers=headers_b)
    assert delete.status_code == 404

    listing = client.get("/workouts", headers=headers_b)
    assert listing.json() == []


def test_workouts_require_auth(client):
    response = client.get("/workouts")

    assert response.status_code == 401
