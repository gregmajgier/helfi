from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.db.cosmos import CosmosDocRepository, CosmosFoodRepository, CosmosMealEntryRepository


def _client(container: MagicMock) -> MagicMock:
    database = MagicMock()
    database.get_container_client.return_value = container
    client = MagicMock()
    client.get_database_client.return_value = database
    return client


def _query_container(items, captured):
    container = MagicMock()

    async def fake_query_items(query, parameters, partition_key=None):
        captured["query"] = query
        captured["parameters"] = parameters
        captured["partition_key"] = partition_key
        for item in items:
            yield item

    container.query_items = fake_query_items
    return container


async def test_doc_repository_rejects_unknown_container():
    with pytest.raises(ValueError):
        CosmosDocRepository(MagicMock(), "db", "users")


async def test_doc_repository_range_query_is_partitioned_and_parameterised():
    captured = {}
    items = [
        {"id": "b", "user_id": "u1", "day": "2026-10-02", "created_at": "2"},
        {"id": "a", "user_id": "u1", "day": "2026-10-01", "created_at": "1"},
    ]
    repo = CosmosDocRepository(_client(_query_container(items, captured)), "db", "water_entries")

    result = await repo.list_for_user("u1", field="day", gte="2026-10-01", lte="2026-10-31")

    assert [d["id"] for d in result] == ["a", "b"]
    assert captured["partition_key"] == "u1"
    assert "c.day >= @gte" in captured["query"] and "c.day <= @lte" in captured["query"]
    assert {"name": "@gte", "value": "2026-10-01"} in captured["parameters"]


async def test_doc_repository_never_interpolates_arbitrary_field_names():
    repo = CosmosDocRepository(_client(MagicMock()), "db", "water_entries")
    with pytest.raises(ValueError):
        await repo.list_for_user("u1", field="day; DROP", gte="x")


async def test_doc_repository_put_upserts_and_keeps_created_at():
    container = MagicMock()
    container.read_item = AsyncMock(return_value={"id": "u1", "user_id": "u1", "created_at": "old"})
    container.upsert_item = AsyncMock()
    repo = CosmosDocRepository(_client(container), "db", "profiles")

    record = await repo.put({"id": "u1", "user_id": "u1", "height_cm": 180})

    assert record["created_at"] == "old"
    container.upsert_item.assert_awaited_once_with(record)


async def test_doc_repository_get_is_scoped_by_partition_key():
    container = MagicMock()
    container.read_item = AsyncMock(side_effect=Exception("not found"))
    repo = CosmosDocRepository(_client(container), "db", "recipes")

    assert await repo.get("u1", "r1") is None
    container.read_item.assert_awaited_once_with(item="r1", partition_key="u1")


async def test_meal_entry_range_handles_legacy_entries_without_day():
    captured = {}
    items = [
        {"id": "late", "user_id": "u1", "logged_at": "2026-10-02T09:00:00"},
        {"id": "early", "user_id": "u1", "logged_at": "2026-10-01T09:00:00"},
    ]
    repo = CosmosMealEntryRepository(_client(_query_container(items, captured)), "db")

    result = await repo.list_range("u1", date(2026, 10, 1), date(2026, 10, 2))

    assert [e["id"] for e in result] == ["early", "late"]
    assert "NOT IS_DEFINED(c.day)" in captured["query"]
    assert captured["partition_key"] == "u1"


async def test_food_search_filters_to_global_and_own_foods_and_ranks():
    captured = {}
    items = [
        {"id": "1", "name": "Wild chicken soup"},
        {"id": "2", "name": "Chicken"},
    ]
    repo = CosmosFoodRepository(_client(_query_container(items, captured)), "db")

    result = await repo.search("Chicken", "u1")

    assert [f["id"] for f in result] == ["2", "1"]
    assert "created_by_user_id = @user_id" in captured["query"]
    assert {"name": "@q", "value": "chicken"} in captured["parameters"]


async def test_food_update_and_delete_require_ownership():
    container = MagicMock()
    container.read_item = AsyncMock(return_value={"id": "f1", "name": "x", "created_by_user_id": "owner"})
    container.replace_item = AsyncMock()
    container.delete_item = AsyncMock()
    repo = CosmosFoodRepository(_client(container), "db")

    assert await repo.update("f1", "intruder", {"name": "y"}) is None
    assert await repo.delete("f1", "intruder") is False
    container.replace_item.assert_not_awaited()
    container.delete_item.assert_not_awaited()

    assert (await repo.update("f1", "owner", {"name": "y"}))["name"] == "y"
    assert await repo.delete("f1", "owner") is True
