from datetime import date
from unittest.mock import AsyncMock, MagicMock

from app.db.cosmos import CosmosMealEntryRepository, CosmosUserRepository


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
