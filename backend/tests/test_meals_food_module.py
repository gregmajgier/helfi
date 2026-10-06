FOOD = {
    "name": "Homemade granola",
    "serving_size": 50,
    "serving_unit": "g",
    "calories_per_serving": 220,
    "protein_g": 6,
    "carbs_g": 30,
    "fat_g": 9,
    "fiber_g": 4,
    "sugar_g": 8,
    "saturated_fat_g": 2,
    "sodium_mg": 40,
}


def _entry(**overrides):
    base = {
        "meal_slot": "lunch",
        "source": "search",
        "logged_at": "2026-10-06T12:30:00Z",
        "day": "2026-10-06",
        "name": "Rice",
        "amount": 200,
        "unit": "g",
        "calories": 260,
        "protein_g": 5.4,
        "carbs_g": 56,
        "fat_g": 0.6,
        "fiber_g": 0.8,
    }
    return {**base, **overrides}


def test_search_ranks_prefix_first_and_hides_other_users_foods(client, auth_headers):
    owner = auth_headers(email="owner@example.com")
    other = auth_headers(email="other@example.com")
    client.post("/meals/foods", json={**FOOD, "name": "Chicken salad (mine)"}, headers=owner)

    mine = client.get("/meals/foods/search", params={"q": "chicken"}, headers=owner).json()
    theirs = client.get("/meals/foods/search", params={"q": "chicken"}, headers=other).json()

    assert any(f["name"] == "Chicken salad (mine)" for f in mine)
    assert not any(f["name"] == "Chicken salad (mine)" for f in theirs)
    assert mine[0]["name"].lower().startswith("chicken")
    assert any(f["name"].lower().startswith("chicken breast") for f in theirs)


def test_search_requires_two_characters(client, auth_headers):
    response = client.get("/meals/foods/search", params={"q": "a"}, headers=auth_headers())
    assert response.status_code == 422


def test_custom_food_update_delete_are_owner_only(client, auth_headers):
    owner = auth_headers(email="o1@example.com")
    other = auth_headers(email="o2@example.com")
    food_id = client.post("/meals/foods", json=FOOD, headers=owner).json()["id"]

    assert client.patch(f"/meals/foods/{food_id}", json={"calories_per_serving": 999}, headers=other).status_code == 404
    assert client.delete(f"/meals/foods/{food_id}", headers=other).status_code == 404

    updated = client.patch(f"/meals/foods/{food_id}", json={"calories_per_serving": 240}, headers=owner)
    assert updated.status_code == 200
    assert updated.json()["calories_per_serving"] == 240
    assert client.get("/meals/foods/mine", headers=owner).json()[0]["id"] == food_id
    assert client.delete(f"/meals/foods/{food_id}", headers=owner).status_code == 204
    assert client.get(f"/meals/foods/{food_id}", headers=owner).status_code == 404


def test_cannot_edit_seed_food(client, auth_headers):
    headers = auth_headers()
    response = client.patch("/meals/foods/common-banana", json={"calories_per_serving": 1}, headers=headers)
    assert response.status_code == 404


def test_other_users_custom_food_is_not_readable(client, auth_headers):
    owner = auth_headers(email="p1@example.com")
    other = auth_headers(email="p2@example.com")
    food_id = client.post("/meals/foods", json=FOOD, headers=owner).json()["id"]
    assert client.get(f"/meals/foods/{food_id}", headers=other).status_code == 404


def test_favorites_roundtrip_and_scoped_per_user(client, auth_headers):
    a = auth_headers(email="fa@example.com")
    b = auth_headers(email="fb@example.com")
    assert client.put("/meals/foods/common-banana/favorite", headers=a).status_code == 204
    assert client.put("/meals/foods/common-banana/favorite", headers=a).status_code == 204  # idempotent

    assert [f["id"] for f in client.get("/meals/foods/favorites", headers=a).json()] == ["common-banana"]
    assert client.get("/meals/foods/favorites", headers=b).json() == []

    client.delete("/meals/foods/common-banana/favorite", headers=a)
    assert client.get("/meals/foods/favorites", headers=a).json() == []


def test_favorite_unknown_food_is_404(client, auth_headers):
    assert client.put("/meals/foods/nope/favorite", headers=auth_headers()).status_code == 404


def test_log_food_computes_nutrition_server_side(client, auth_headers):
    headers = auth_headers()
    response = client.post(
        "/meals/entries/from-food",
        json={"food_id": "common-chicken-breast", "amount": 200, "meal_slot": "dinner", "day": "2026-10-06"},
        headers=headers,
    )
    assert response.status_code == 201
    entry = response.json()
    assert entry["name"] == "Chicken breast, cooked"
    assert entry["calories"] == 330  # 165 kcal per 100 g
    assert entry["protein_g"] == 62
    assert entry["unit"] == "g"
    assert entry["day"] == "2026-10-06"


def test_log_food_by_serving_scale(client, auth_headers):
    headers = auth_headers()
    # Banana serving is 118 g = 105 kcal, so 236 g is two bananas.
    entry = client.post(
        "/meals/entries/from-food",
        json={"food_id": "common-banana", "amount": 236, "meal_slot": "snack", "day": "2026-10-06"},
        headers=headers,
    ).json()
    assert entry["calories"] == 210


def test_log_food_rejects_another_users_custom_food(client, auth_headers):
    owner = auth_headers(email="l1@example.com")
    other = auth_headers(email="l2@example.com")
    food_id = client.post("/meals/foods", json=FOOD, headers=owner).json()["id"]
    response = client.post(
        "/meals/entries/from-food",
        json={"food_id": food_id, "amount": 50, "meal_slot": "snack", "day": "2026-10-06"},
        headers=other,
    )
    assert response.status_code == 404


def test_patch_amount_rescales_all_nutrients(client, auth_headers):
    headers = auth_headers()
    entry_id = client.post("/meals/entries", json=_entry(), headers=headers).json()["id"]

    updated = client.patch(f"/meals/entries/{entry_id}", json={"amount": 100}, headers=headers).json()

    assert updated["amount"] == 100
    assert updated["calories"] == 130
    assert updated["carbs_g"] == 28
    assert updated["fiber_g"] == 0.4


def test_patch_amount_without_stored_amount_is_rejected(client, auth_headers):
    headers = auth_headers()
    entry_id = client.post("/meals/entries", json=_entry(amount=None), headers=headers).json()["id"]
    response = client.patch(f"/meals/entries/{entry_id}", json={"amount": 100}, headers=headers)
    assert response.status_code == 400


def test_amount_must_be_positive(client, auth_headers):
    headers = auth_headers()
    entry_id = client.post("/meals/entries", json=_entry(), headers=headers).json()["id"]
    assert client.patch(f"/meals/entries/{entry_id}", json={"amount": 0}, headers=headers).status_code == 422


def test_entry_day_defaults_from_logged_at_and_groups_by_local_day(client, auth_headers):
    headers = auth_headers()
    # 23:30 UTC on the 5th but the user's local day is the 6th.
    client.post("/meals/entries", json=_entry(logged_at="2026-10-05T23:30:00Z", day="2026-10-06"), headers=headers)
    client.post("/meals/entries", json=_entry(day=None, logged_at="2026-10-07T08:00:00Z"), headers=headers)

    assert len(client.get("/meals/entries", params={"day": "2026-10-06"}, headers=headers).json()) == 1
    assert len(client.get("/meals/entries", params={"day": "2026-10-07"}, headers=headers).json()) == 1
    assert client.get("/meals/entries", params={"day": "2026-10-05"}, headers=headers).json() == []


def test_copy_day_and_slot(client, auth_headers):
    headers = auth_headers()
    client.post("/meals/entries", json=_entry(), headers=headers)
    client.post("/meals/entries", json=_entry(meal_slot="dinner", name="Soup"), headers=headers)

    copied = client.post(
        "/meals/entries/copy",
        json={"from_day": "2026-10-06", "to_day": "2026-10-07", "from_slot": "lunch", "to_slot": "breakfast"},
        headers=headers,
    )
    assert copied.status_code == 201
    assert len(copied.json()) == 1
    target = client.get("/meals/entries", params={"day": "2026-10-07"}, headers=headers).json()
    assert [(e["name"], e["meal_slot"], e["day"]) for e in target] == [("Rice", "breakfast", "2026-10-07")]
    assert target[0]["logged_at"].startswith("2026-10-07")
    # Original untouched.
    assert len(client.get("/meals/entries", params={"day": "2026-10-06"}, headers=headers).json()) == 2


def test_copy_only_reads_own_entries(client, auth_headers):
    owner = auth_headers(email="c1@example.com")
    other = auth_headers(email="c2@example.com")
    client.post("/meals/entries", json=_entry(), headers=owner)
    copied = client.post(
        "/meals/entries/copy", json={"from_day": "2026-10-06", "to_day": "2026-10-07"}, headers=other
    )
    assert copied.json() == []


def test_recent_dedupes_and_orders_newest_first(client, auth_headers):
    headers = auth_headers()
    client.post("/meals/entries", json=_entry(name="Rice", logged_at="2026-10-04T12:00:00Z", day="2026-10-04"), headers=headers)
    client.post("/meals/entries", json=_entry(name="Soup", logged_at="2026-10-05T12:00:00Z", day="2026-10-05"), headers=headers)
    client.post("/meals/entries", json=_entry(name="Rice", logged_at="2026-10-06T12:00:00Z", day="2026-10-06"), headers=headers)
    client.post("/meals/entries", json=_entry(name=None), headers=headers)

    recent = client.get("/meals/entries/recent", params={"today": "2026-10-06"}, headers=headers).json()

    assert [e["name"] for e in recent] == ["Rice", "Soup"]


def test_stats_fills_missing_days_and_averages_logged_days_only(client, auth_headers):
    headers = auth_headers()
    client.post("/meals/entries", json=_entry(calories=500, day="2026-10-01", logged_at="2026-10-01T12:00:00Z"), headers=headers)
    client.post("/meals/entries", json=_entry(calories=300, day="2026-10-01", logged_at="2026-10-01T18:00:00Z"), headers=headers)
    client.post("/meals/entries", json=_entry(calories=1000, day="2026-10-03", logged_at="2026-10-03T12:00:00Z"), headers=headers)

    stats = client.get("/meals/entries/stats", params={"start": "2026-10-01", "end": "2026-10-04"}, headers=headers).json()

    assert [d["calories"] for d in stats["days"]] == [800, 0, 1000, 0]
    assert stats["logged_days"] == 2
    assert stats["average_calories"] == 900


def test_stats_rejects_huge_or_inverted_ranges(client, auth_headers):
    headers = auth_headers()
    assert client.get("/meals/entries/stats", params={"start": "2026-10-04", "end": "2026-10-01"}, headers=headers).status_code == 400
    assert client.get("/meals/entries/stats", params={"start": "2026-01-01", "end": "2026-10-01"}, headers=headers).status_code == 400


def test_new_endpoints_require_auth(client):
    for path in [
        "/meals/foods/search?q=ab",
        "/meals/foods/favorites",
        "/meals/entries/recent",
        "/meals/entries/stats?start=2026-10-01&end=2026-10-02",
    ]:
        assert client.get(path).status_code in (401, 403)
