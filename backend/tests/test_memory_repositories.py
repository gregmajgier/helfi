from datetime import date

from app.db.memory import (
    SEED_FOODS,
    InMemoryFoodRepository,
    InMemoryMealEntryRepository,
    InMemoryUserRepository,
)


async def test_user_repository_create_and_lookup():
    repo = InMemoryUserRepository()

    created = await repo.create({"email": "user@example.com", "password_hash": "hashed"})

    assert created["id"]
    assert await repo.get_by_id(created["id"]) == created
    assert await repo.get_by_email("user@example.com") == created
    assert await repo.get_by_email("missing@example.com") is None


async def test_meal_entry_repository_crud_scoped_by_user():
    repo = InMemoryMealEntryRepository()

    entry = await repo.create(
        {"user_id": "user-1", "logged_at": "2026-09-16T08:00:00+00:00", "calories": 300}
    )

    assert entry["id"]
    same_day = await repo.list_for_day("user-1", date(2026, 9, 16))
    assert [e["id"] for e in same_day] == [entry["id"]]
    assert await repo.list_for_day("user-2", date(2026, 9, 16)) == []

    updated = await repo.update("user-1", entry["id"], {"calories": 350})
    assert updated["calories"] == 350
    assert await repo.update("user-2", entry["id"], {"calories": 999}) is None

    assert await repo.delete("user-2", entry["id"]) is False
    assert await repo.delete("user-1", entry["id"]) is True
    assert await repo.get("user-1", entry["id"]) is None


async def test_food_repository_search_is_case_insensitive_substring_match():
    repo = InMemoryFoodRepository(SEED_FOODS)

    results = await repo.search("chick")

    assert any("Chicken" in food["name"] for food in results)
    assert await repo.search("nonexistent-food-xyz") == []
