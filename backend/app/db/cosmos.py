import uuid
from datetime import date, datetime, timezone
from typing import Optional

from azure.cosmos import PartitionKey
from azure.cosmos.aio import CosmosClient

_client: Optional[CosmosClient] = None


def get_cosmos_client() -> CosmosClient:
    global _client
    if _client is None:
        from ..config import settings

        _client = CosmosClient.from_connection_string(settings.cosmos_connection_string)
    return _client


async def close_cosmos_client() -> None:
    global _client
    if _client is not None:
        await _client.close()
        _client = None


async def init_cosmos(client: CosmosClient, database_name: str) -> None:
    database = await client.create_database_if_not_exists(database_name)
    await database.create_container_if_not_exists(id="users", partition_key=PartitionKey(path="/id"))
    await database.create_container_if_not_exists(
        id="meal_entries", partition_key=PartitionKey(path="/user_id")
    )
    await database.create_container_if_not_exists(id="foods", partition_key=PartitionKey(path="/id"))


class CosmosUserRepository:
    def __init__(self, client: CosmosClient, database_name: str):
        self._client = client
        self._database_name = database_name

    def _container(self):
        return self._client.get_database_client(self._database_name).get_container_client("users")

    async def get_by_email(self, email: str) -> Optional[dict]:
        container = self._container()
        query = "SELECT * FROM c WHERE c.email = @email"
        params = [{"name": "@email", "value": email.lower()}]
        async for item in container.query_items(query=query, parameters=params):
            return item
        return None

    async def get_by_id(self, user_id: str) -> Optional[dict]:
        container = self._container()
        try:
            return await container.read_item(item=user_id, partition_key=user_id)
        except Exception:
            return None

    async def create(self, user: dict) -> dict:
        container = self._container()
        record = {
            **user,
            "id": str(uuid.uuid4()),
            "email": user["email"].lower(),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        await container.create_item(record)
        return record


class CosmosMealEntryRepository:
    def __init__(self, client: CosmosClient, database_name: str):
        self._client = client
        self._database_name = database_name

    def _container(self):
        return self._client.get_database_client(self._database_name).get_container_client("meal_entries")

    async def create(self, entry: dict) -> dict:
        container = self._container()
        now = datetime.now(timezone.utc).isoformat()
        record = {**entry, "id": str(uuid.uuid4()), "created_at": now, "updated_at": now}
        await container.create_item(record)
        return record

    async def list_for_day(self, user_id: str, day: date) -> list[dict]:
        container = self._container()
        query = "SELECT * FROM c WHERE c.user_id = @user_id AND STARTSWITH(c.logged_at, @day)"
        params = [
            {"name": "@user_id", "value": user_id},
            {"name": "@day", "value": day.isoformat()},
        ]
        return [
            item
            async for item in container.query_items(query=query, parameters=params, partition_key=user_id)
        ]

    async def get(self, user_id: str, entry_id: str) -> Optional[dict]:
        container = self._container()
        try:
            return await container.read_item(item=entry_id, partition_key=user_id)
        except Exception:
            return None

    async def update(self, user_id: str, entry_id: str, updates: dict) -> Optional[dict]:
        entry = await self.get(user_id, entry_id)
        if not entry:
            return None
        entry.update(updates)
        entry["updated_at"] = datetime.now(timezone.utc).isoformat()
        await self._container().replace_item(item=entry_id, body=entry)
        return entry

    async def delete(self, user_id: str, entry_id: str) -> bool:
        entry = await self.get(user_id, entry_id)
        if not entry:
            return False
        await self._container().delete_item(item=entry_id, partition_key=user_id)
        return True


class CosmosFoodRepository:
    def __init__(self, client: CosmosClient, database_name: str):
        self._client = client
        self._database_name = database_name

    def _container(self):
        return self._client.get_database_client(self._database_name).get_container_client("foods")

    async def search(self, query: str) -> list[dict]:
        container = self._container()
        sql_query = "SELECT * FROM c WHERE CONTAINS(LOWER(c.name), @query)"
        params = [{"name": "@query", "value": query.lower()}]
        return [item async for item in container.query_items(query=sql_query, parameters=params)]

    async def get(self, food_id: str) -> Optional[dict]:
        container = self._container()
        try:
            return await container.read_item(item=food_id, partition_key=food_id)
        except Exception:
            return None
