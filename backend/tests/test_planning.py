from datetime import date

from app.planning.generator import SLOT_SHARE, generate
from app.recipes.service import CURATED

START = "2026-10-12"


def _add_recipe(client, headers, recipe_id="curated-greek-salad", slot="lunch", day=START, servings=1):
    return client.post(
        "/plan",
        json={"day": day, "meal_slot": slot, "recipe_id": recipe_id, "servings": servings},
        headers=headers,
    )


def test_generator_hits_calorie_target_and_varies_meals():
    plan = generate(list(CURATED.values()), date(2026, 10, 12), 7, 2000)
    by_day: dict[date, float] = {}
    for item in plan:
        by_day[item["day"]] = by_day.get(item["day"], 0) + item["servings"] * item["recipe"]["per_serving"]["calories"]
    assert len(by_day) == 7
    for day, kcal in by_day.items():
        assert 1500 <= kcal <= 2500, (day, kcal)
    dinners = {i["recipe"]["id"] for i in plan if i["meal_slot"] == "dinner"}
    assert len(dinners) >= 5
    # Same recipe never twice in one day.
    for day in by_day:
        ids = [i["recipe"]["id"] for i in plan if i["day"] == day]
        assert len(ids) == len(set(ids))
    assert set(SLOT_SHARE) == {i["meal_slot"] for i in plan}


def test_generator_is_deterministic():
    a = generate(list(CURATED.values()), date(2026, 10, 12), 5, 1800)
    b = generate(list(CURATED.values()), date(2026, 10, 12), 5, 1800)
    assert [(i["day"], i["recipe"]["id"], i["servings"]) for i in a] == [(i["day"], i["recipe"]["id"], i["servings"]) for i in b]


def test_add_recipe_and_food_items(client, auth_headers):
    headers = auth_headers()
    recipe_item = _add_recipe(client, headers, servings=2)
    assert recipe_item.status_code == 201
    assert recipe_item.json()["calories"] == round(CURATED["curated-greek-salad"]["per_serving"]["calories"] * 2, 2)
    assert recipe_item.json()["ingredients"][0]["amount"] > 0

    food_item = client.post(
        "/plan",
        json={"day": START, "meal_slot": "snack", "food_id": "common-banana", "amount": 118},
        headers=headers,
    )
    assert food_item.status_code == 201
    assert food_item.json()["calories"] == 105

    plan = client.get("/plan", params={"start": START, "end": START}, headers=headers).json()
    assert [p["meal_slot"] for p in plan] == ["lunch", "snack"]


def test_plan_item_needs_exactly_one_kind(client, auth_headers):
    headers = auth_headers()
    both = {"day": START, "meal_slot": "lunch", "recipe_id": "curated-greek-salad", "servings": 1, "food_id": "common-banana", "amount": 1}
    neither = {"day": START, "meal_slot": "lunch"}
    assert client.post("/plan", json=both, headers=headers).status_code == 422
    assert client.post("/plan", json=neither, headers=headers).status_code == 422


def test_plan_is_private_and_range_limited(client, auth_headers):
    owner = auth_headers(email="pl1@example.com")
    other = auth_headers(email="pl2@example.com")
    item_id = _add_recipe(client, owner).json()["id"]
    assert client.get("/plan", params={"start": START, "end": START}, headers=other).json() == []
    assert client.delete(f"/plan/{item_id}", headers=other).status_code == 404
    assert client.get("/plan", params={"start": "2026-01-01", "end": "2026-12-31"}, headers=owner).status_code == 400
    assert _add_recipe(client, owner, recipe_id="someone-elses").status_code == 404


def test_apply_plan_copies_into_diary(client, auth_headers):
    headers = auth_headers()
    _add_recipe(client, headers, slot="lunch")
    _add_recipe(client, headers, recipe_id="curated-apple-pb", slot="snack")

    applied = client.post("/plan/apply", json={"day": START, "meal_slot": "snack"}, headers=headers)
    assert applied.status_code == 201
    assert [e["name"] for e in applied.json()] == ["Apple with peanut butter"]
    assert applied.json()[0]["source"] == "plan"

    diary = client.get("/meals/entries", params={"day": START}, headers=headers).json()
    assert len(diary) == 1


def test_generate_uses_profile_target_and_replace(client, auth_headers):
    headers = auth_headers()
    client.put(
        "/profile",
        json={"sex": "female", "birth_year": 1992, "height_cm": 168, "weight_kg": 62, "activity_level": "light", "goal": "maintain"},
        headers=headers,
    )
    first = client.post("/plan/generate", json={"start": START, "days": 3}, headers=headers)
    assert first.status_code == 201
    count = len(first.json())
    assert count >= 9  # 3 days x at least 3 slots
    # Generating again replaces instead of stacking.
    client.post("/plan/generate", json={"start": START, "days": 3}, headers=headers)
    plan = client.get("/plan", params={"start": START, "end": "2026-10-14"}, headers=headers).json()
    assert len(plan) == count

    cleared = client.post("/plan/clear", json={"start": START, "end": "2026-10-14"}, headers=headers).json()
    assert cleared == {"deleted": count}


def test_shopping_list_aggregates_and_preserves_ticks(client, auth_headers):
    headers = auth_headers()
    _add_recipe(client, headers, recipe_id="curated-greek-salad", day=START)
    _add_recipe(client, headers, recipe_id="curated-greek-salad", day="2026-10-13")
    client.post("/shopping", json={"name": "Dish soap"}, headers=headers)

    items = client.post("/shopping/generate", json={"start": START, "end": "2026-10-13"}, headers=headers).json()

    tomato = next(i for i in items if i["name"] == "Tomato")
    assert tomato["amount"] == 300  # 150 g on each of two days
    assert tomato["source"] == "plan"
    assert any(i["name"] == "Dish soap" for i in items)

    client.patch(f"/shopping/{tomato['id']}", json={"checked": True}, headers=headers)
    again = client.post("/shopping/generate", json={"start": START, "end": "2026-10-13"}, headers=headers).json()
    assert next(i for i in again if i["name"] == "Tomato")["checked"] is True
    assert sum(1 for i in again if i["name"] == "Dish soap") == 1

    cleared = client.post("/shopping/clear-checked", headers=headers).json()
    assert not any(i["name"] == "Tomato" for i in cleared)


def test_shopping_is_private(client, auth_headers):
    owner = auth_headers(email="s1@example.com")
    other = auth_headers(email="s2@example.com")
    item_id = client.post("/shopping", json={"name": "Milk", "amount": 1, "unit": "l"}, headers=owner).json()["id"]
    assert client.get("/shopping", headers=other).json() == []
    assert client.patch(f"/shopping/{item_id}", json={"checked": True}, headers=other).status_code == 404
    assert client.delete(f"/shopping/{item_id}", headers=other).status_code == 404
    assert client.delete(f"/shopping/{item_id}", headers=owner).status_code == 204


def test_generate_plan_cannot_exceed_the_plan_cap(client, auth_headers, monkeypatch):
    from app.planning import router as planning_router

    headers = auth_headers()
    monkeypatch.setattr(planning_router, "MAX_PLAN_ITEMS", 10)
    ok = client.post("/plan/generate", json={"start": START, "days": 2}, headers=headers)
    assert ok.status_code == 201  # 2 days x 4 slots = 8

    # replace=false would stack another 8 on top of the existing 8.
    over = client.post("/plan/generate", json={"start": "2026-11-01", "days": 2, "replace": False}, headers=headers)
    assert over.status_code == 400
    # A rejected request must not have changed anything.
    assert len(client.get("/plan", params={"start": START, "end": "2026-11-02"}, headers=headers).json()) == 8


def test_generate_plan_replace_counts_only_net_growth(client, auth_headers, monkeypatch):
    from app.planning import router as planning_router

    headers = auth_headers()
    monkeypatch.setattr(planning_router, "MAX_PLAN_ITEMS", 10)
    client.post("/plan/generate", json={"start": START, "days": 2}, headers=headers)
    # Same range with replace swaps 8 for 8, so it stays within the cap.
    again = client.post("/plan/generate", json={"start": START, "days": 2}, headers=headers)
    assert again.status_code == 201


def test_shopping_generation_is_capped(client, auth_headers, monkeypatch):
    from app.planning import router as planning_router

    headers = auth_headers()
    _add_recipe(client, headers, recipe_id="curated-chicken-rice-bowl")
    monkeypatch.setattr(planning_router, "MAX_SHOPPING_ITEMS", 2)
    response = client.post("/shopping/generate", json={"start": START, "end": START}, headers=headers)
    assert response.status_code == 400
