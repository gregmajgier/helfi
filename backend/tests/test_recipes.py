import json
from pathlib import Path

from app.recipes.service import CURATED

RECIPE = {
    "name": "Banana oat bowl",
    "servings": 2,
    "meal_types": ["breakfast"],
    "prep_minutes": 5,
    "ingredients": [
        {"name": "Oats", "amount": 80, "unit": "g", "calories": 311, "protein_g": 13.6, "carbs_g": 52.8, "fat_g": 5.6},
        {"name": "Banana", "amount": 118, "unit": "g", "calories": 105, "protein_g": 1.3, "carbs_g": 27, "fat_g": 0.4},
    ],
    "instructions": ["Mix.", "Eat."],
}


def test_curated_library_is_internally_consistent():
    foods = {f["id"]: f for f in json.loads((Path(__file__).parent.parent / "app/db/data/common_foods_seed.json").read_text())}
    assert len(CURATED) >= 30
    for recipe in CURATED.values():
        assert recipe["curated"] is True
        assert recipe["meal_types"], recipe["id"]
        assert recipe["per_serving"]["calories"] > 50, recipe["id"]
        # Totals really are the sum of the ingredient rows.
        assert abs(recipe["totals"]["calories"] - sum(i["calories"] for i in recipe["ingredients"])) < 1
        assert all(i["food_id"] in foods for i in recipe["ingredients"])
    covered = {slot for r in CURATED.values() for slot in r["meal_types"]}
    assert covered == {"breakfast", "lunch", "dinner", "snack"}


def test_list_includes_curated_and_filters(client, auth_headers):
    headers = auth_headers()
    everything = client.get("/recipes", headers=headers).json()
    assert any(r["curated"] for r in everything)
    snacks = client.get("/recipes", params={"meal_type": "snack"}, headers=headers).json()
    assert snacks and all("snack" in r["meal_types"] for r in snacks)
    found = client.get("/recipes", params={"q": "salmon"}, headers=headers).json()
    assert [r["id"] for r in found] == ["curated-salmon-sweet-potato"]


def test_create_computes_totals_and_per_serving(client, auth_headers):
    headers = auth_headers()
    created = client.post("/recipes", json=RECIPE, headers=headers)
    assert created.status_code == 201
    body = created.json()
    assert body["curated"] is False
    assert body["totals"]["calories"] == 416
    assert body["per_serving"]["calories"] == 208
    assert client.get("/recipes", params={"mine": True}, headers=headers).json()[0]["id"] == body["id"]


def test_recipe_validation(client, auth_headers):
    headers = auth_headers()
    assert client.post("/recipes", json={**RECIPE, "ingredients": []}, headers=headers).status_code == 422
    assert client.post("/recipes", json={**RECIPE, "servings": 0}, headers=headers).status_code == 422


def test_recipes_are_private_and_curated_are_read_only(client, auth_headers):
    owner = auth_headers(email="r1@example.com")
    other = auth_headers(email="r2@example.com")
    recipe_id = client.post("/recipes", json=RECIPE, headers=owner).json()["id"]

    assert client.get(f"/recipes/{recipe_id}", headers=other).status_code == 404
    assert client.put(f"/recipes/{recipe_id}", json=RECIPE, headers=other).status_code == 404
    assert client.delete(f"/recipes/{recipe_id}", headers=other).status_code == 404
    assert client.put("/recipes/curated-greek-salad", json=RECIPE, headers=owner).status_code == 403
    assert client.delete("/recipes/curated-greek-salad", headers=owner).status_code == 403


def test_update_and_delete_own_recipe(client, auth_headers):
    headers = auth_headers()
    recipe_id = client.post("/recipes", json=RECIPE, headers=headers).json()["id"]
    updated = client.put(f"/recipes/{recipe_id}", json={**RECIPE, "servings": 4}, headers=headers).json()
    assert updated["per_serving"]["calories"] == 104
    assert client.delete(f"/recipes/{recipe_id}", headers=headers).status_code == 204
    assert client.get(f"/recipes/{recipe_id}", headers=headers).status_code == 404


def test_copy_curated_recipe_makes_editable_copy(client, auth_headers):
    headers = auth_headers()
    copy = client.post("/recipes/curated-greek-salad/copy", headers=headers)
    assert copy.status_code == 201
    assert copy.json()["curated"] is False
    assert copy.json()["id"] != "curated-greek-salad"
    assert copy.json()["totals"] == CURATED["curated-greek-salad"]["totals"]


def test_log_recipe_creates_single_diary_entry(client, auth_headers):
    headers = auth_headers()
    recipe_id = client.post("/recipes", json=RECIPE, headers=headers).json()["id"]
    response = client.post(
        f"/recipes/{recipe_id}/log",
        json={"servings": 1.5, "meal_slot": "breakfast", "day": "2026-10-06"},
        headers=headers,
    )
    assert response.status_code == 201
    entry = response.json()
    assert entry["source"] == "recipe"
    assert entry["name"] == "Banana oat bowl"
    assert entry["calories"] == 312
    assert entry["unit"] == "serving"
    diary = client.get("/meals/entries", params={"day": "2026-10-06"}, headers=headers).json()
    assert len(diary) == 1


def test_cannot_log_someone_elses_recipe(client, auth_headers):
    owner = auth_headers(email="rl1@example.com")
    other = auth_headers(email="rl2@example.com")
    recipe_id = client.post("/recipes", json=RECIPE, headers=owner).json()["id"]
    response = client.post(
        f"/recipes/{recipe_id}/log",
        json={"servings": 1, "meal_slot": "lunch", "day": "2026-10-06"},
        headers=other,
    )
    assert response.status_code == 404


def test_copy_respects_the_recipe_cap(client, auth_headers, monkeypatch):
    from app.recipes import router as recipes_router

    headers = auth_headers()
    monkeypatch.setattr(recipes_router, "MAX_USER_RECIPES", 1)
    assert client.post("/recipes/curated-greek-salad/copy", headers=headers).status_code == 201
    assert client.post("/recipes/curated-greek-salad/copy", headers=headers).status_code == 400
    assert client.post("/recipes", json=RECIPE, headers=headers).status_code == 400
