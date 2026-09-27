from datetime import date

from app.db.memory import (
    SEED_EXERCISES,
    SEED_FOODS,
    InMemoryExerciseRepository,
    InMemoryFoodRepository,
    InMemoryMealEntryRepository,
    InMemoryUserRepository,
    InMemoryWorkoutRepository,
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


async def test_workout_repository_crud_scoped_by_user():
    repo = InMemoryWorkoutRepository()

    workout = await repo.create(
        {
            "user_id": "user-1",
            "type": "running",
            "source": "manual",
            "started_at": "2026-09-16T08:00:00+00:00",
            "duration_s": 1800,
            "distance_m": 5000,
        }
    )

    assert workout["id"]
    mine = await repo.list_for_user("user-1")
    assert [w["id"] for w in mine] == [workout["id"]]
    assert await repo.list_for_user("user-2") == []

    updated = await repo.update("user-1", workout["id"], {"duration_s": 1700})
    assert updated["duration_s"] == 1700
    assert await repo.update("user-2", workout["id"], {"duration_s": 1}) is None

    assert await repo.delete("user-2", workout["id"]) is False
    assert await repo.delete("user-1", workout["id"]) is True
    assert await repo.get("user-1", workout["id"]) is None


async def test_workout_repository_list_for_user_filters_by_type():
    repo = InMemoryWorkoutRepository()
    await repo.create(
        {
            "user_id": "user-1",
            "type": "running",
            "source": "manual",
            "started_at": "2026-09-16T08:00:00+00:00",
            "duration_s": 1800,
        }
    )
    await repo.create(
        {
            "user_id": "user-1",
            "type": "strength",
            "source": "manual",
            "started_at": "2026-09-17T08:00:00+00:00",
            "duration_s": 3600,
        }
    )

    running_only = await repo.list_for_user("user-1", workout_type="running")

    assert [w["type"] for w in running_only] == ["running"]


async def test_exercise_repository_search_and_create():
    repo = InMemoryExerciseRepository(SEED_EXERCISES)

    seeded = await repo.search("bench")
    assert any("Bench" in e["name"] for e in seeded)

    created = await repo.create(
        {"name": "Cable Row", "category": "back", "is_bodyweight": False, "created_by_user_id": "user-1"}
    )
    assert created["id"]
    found = await repo.search("cable")
    assert any(e["id"] == created["id"] for e in found)
