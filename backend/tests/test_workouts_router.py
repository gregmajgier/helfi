def test_search_exercises_matches_partial_case_insensitive_name(client, auth_headers):
    headers = auth_headers()

    response = client.get("/workouts/exercises", params={"q": "BENCH"}, headers=headers)

    assert response.status_code == 200
    names = [e["name"] for e in response.json()]
    assert any("Bench" in name for name in names)


def test_search_exercises_requires_auth(client):
    response = client.get("/workouts/exercises", params={"q": "bench"})

    assert response.status_code == 403


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
