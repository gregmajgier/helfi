from datetime import date
from unittest.mock import AsyncMock, MagicMock

from app.db.cosmos import (
    CosmosExerciseRepository,
    CosmosFoodRepository,
    CosmosJournalEntryRepository,
    CosmosMealEntryRepository,
    CosmosMoodEntryRepository,
    CosmosScreenTimeRuleRepository,
    CosmosUserRepository,
    CosmosWorkoutRepository,
)


def _client_with_container(container: MagicMock) -> MagicMock:
    database = MagicMock()
    database.get_container_client.return_value = container
    client = MagicMock()
    client.get_database_client.return_value = database
    return client


async def test_user_repository_create_lowercases_email_and_assigns_id():
    container = MagicMock()
    container.create_item = AsyncMock()
    repo = CosmosUserRepository(_client_with_container(container), "health_app")

    record = await repo.create({"email": "User@Example.com", "password_hash": "x"})

    assert record["email"] == "user@example.com"
    assert record["id"]
    container.create_item.assert_awaited_once_with(record)


async def test_meal_entry_repository_list_for_day_queries_by_partition_key():
    container = MagicMock()

    async def fake_query_items(query, parameters, partition_key):
        assert partition_key == "user-1"
        for item in [{"id": "e1", "user_id": "user-1", "logged_at": "2026-09-16T08:00:00"}]:
            yield item

    container.query_items = fake_query_items
    repo = CosmosMealEntryRepository(_client_with_container(container), "health_app")

    entries = await repo.list_for_day("user-1", date(2026, 9, 16))

    assert [e["id"] for e in entries] == ["e1"]


async def test_food_repository_get_by_barcode_only_matches_global_records():
    container = MagicMock()
    captured = {}

    async def fake_query_items(query, parameters):
        captured["query"] = query
        captured["parameters"] = parameters
        for item in [{"id": "chicken-breast", "name": "Chicken Breast, cooked", "barcode": "123"}]:
            yield item

    container.query_items = fake_query_items
    repo = CosmosFoodRepository(_client_with_container(container), "health_app")

    result = await repo.get_by_barcode("123")

    assert result["id"] == "chicken-breast"
    assert "c.barcode = @barcode" in captured["query"]
    assert "created_by_user_id" in captured["query"]
    assert captured["parameters"] == [{"name": "@barcode", "value": "123"}]


async def test_workout_repository_list_for_user_filters_by_type_and_partition_key():
    container = MagicMock()

    async def fake_query_items(query, parameters, partition_key):
        assert partition_key == "user-1"
        assert "c.type = @type" in query
        for item in [{"id": "w1", "user_id": "user-1", "type": "running", "started_at": "2026-09-16T08:00:00"}]:
            yield item

    container.query_items = fake_query_items
    repo = CosmosWorkoutRepository(_client_with_container(container), "health_app")

    workouts = await repo.list_for_user("user-1", workout_type="running")

    assert [w["id"] for w in workouts] == ["w1"]


async def test_exercise_repository_search_queries_case_insensitive_substring():
    container = MagicMock()
    captured = {}

    async def fake_query_items(query, parameters):
        captured["query"] = query
        captured["parameters"] = parameters
        for item in [{"id": "bench-press", "name": "Bench Press"}]:
            yield item

    container.query_items = fake_query_items
    repo = CosmosExerciseRepository(_client_with_container(container), "health_app")

    results = await repo.search("BENCH")

    assert [e["id"] for e in results] == ["bench-press"]
    assert "CONTAINS(LOWER(c.name)" in captured["query"]
    assert captured["parameters"] == [{"name": "@query", "value": "bench"}]


async def test_exercise_repository_create_assigns_id():
    container = MagicMock()
    container.create_item = AsyncMock()
    repo = CosmosExerciseRepository(_client_with_container(container), "health_app")

    record = await repo.create(
        {"name": "Cable Row", "category": "back", "is_bodyweight": False, "created_by_user_id": "user-1"}
    )

    assert record["id"]
    container.create_item.assert_awaited_once_with(record)


async def test_mood_entry_repository_list_for_user_queries_by_partition_key_and_range():
    container = MagicMock()

    async def fake_query_items(query, parameters, partition_key):
        assert partition_key == "user-1"
        assert "c.logged_at >= @start" in query
        for item in [{"id": "m1", "user_id": "user-1", "logged_at": "2026-10-05T08:00:00", "mood_score": 5}]:
            yield item

    container.query_items = fake_query_items
    repo = CosmosMoodEntryRepository(_client_with_container(container), "health_app")

    from datetime import date

    entries = await repo.list_for_user("user-1", start=date(2026, 10, 1))

    assert [e["id"] for e in entries] == ["m1"]


async def test_mood_entry_repository_create_assigns_id():
    container = MagicMock()
    container.create_item = AsyncMock()
    repo = CosmosMoodEntryRepository(_client_with_container(container), "health_app")

    record = await repo.create({"user_id": "user-1", "logged_at": "2026-10-01T08:00:00", "mood_score": 3, "tags": []})

    assert record["id"]
    container.create_item.assert_awaited_once_with(record)


async def test_journal_entry_repository_list_for_user_queries_by_partition_key():
    container = MagicMock()

    async def fake_query_items(query, parameters, partition_key):
        assert partition_key == "user-1"
        for item in [{"id": "j1", "user_id": "user-1", "written_at": "2026-10-01T08:00:00", "body": "hi"}]:
            yield item

    container.query_items = fake_query_items
    repo = CosmosJournalEntryRepository(_client_with_container(container), "health_app")

    entries = await repo.list_for_user("user-1")

    assert [e["id"] for e in entries] == ["j1"]


async def test_screentime_rule_repository_list_for_user_queries_by_partition_key():
    container = MagicMock()

    async def fake_query_items(query, parameters, partition_key):
        assert partition_key == "user-1"
        for item in [{"id": "r1", "user_id": "user-1", "name": "Wind-down", "created_at": "2026-10-01T08:00:00"}]:
            yield item

    container.query_items = fake_query_items
    repo = CosmosScreenTimeRuleRepository(_client_with_container(container), "health_app")

    rules = await repo.list_for_user("user-1")

    assert [r["id"] for r in rules] == ["r1"]


async def test_screentime_rule_repository_create_assigns_id():
    container = MagicMock()
    container.create_item = AsyncMock()
    repo = CosmosScreenTimeRuleRepository(_client_with_container(container), "health_app")

    record = await repo.create(
        {"user_id": "user-1", "name": "Wind-down", "apps_or_categories": ["social"], "enabled": True}
    )

    assert record["id"]
    container.create_item.assert_awaited_once_with(record)
