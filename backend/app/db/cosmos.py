import json
import uuid
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Optional

from azure.cosmos import PartitionKey
from azure.cosmos.aio import CosmosClient

_EXERCISES_SEED_PATH = Path(__file__).parent / "data" / "exercises_seed.json"
_FOODS_SEED_PATH = Path(__file__).parent / "data" / "foods_seed.json"

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
    foods_container = await database.create_container_if_not_exists(
        id="foods", partition_key=PartitionKey(path="/id")
    )
    await database.create_container_if_not_exists(
        id="workouts", partition_key=PartitionKey(path="/user_id")
    )
    exercises_container = await database.create_container_if_not_exists(
        id="exercises", partition_key=PartitionKey(path="/id")
    )
    await database.create_container_if_not_exists(
        id="mood_entries", partition_key=PartitionKey(path="/user_id")
    )
    await database.create_container_if_not_exists(
        id="journal_entries", partition_key=PartitionKey(path="/user_id")
    )
    await database.create_container_if_not_exists(
        id="screentime_rules", partition_key=PartitionKey(path="/user_id")
    )
    await _seed_exercises(exercises_container)
    await _seed_foods(foods_container)


async def _seed_exercises(container) -> None:
    # Idempotent: upsert_item by id, so re-running at every app startup never
    # duplicates and never touches user-created exercises (created_by_user_id
    # is never None for those).
    records = json.loads(_EXERCISES_SEED_PATH.read_text())
    for record in records:
        await container.upsert_item({**record, "created_by_user_id": None})


async def _seed_foods(container) -> None:
    # Idempotent: upsert_item by id, so re-running at every app startup never
    # duplicates and never touches user-created foods (created_by_user_id is
    # never None for those, enforced in the /meals/foods create handler).
    records = json.loads(_FOODS_SEED_PATH.read_text())
    for record in records:
        await container.upsert_item({**record, "created_by_user_id": None})


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

    async def get(self, food_id: str) -> Optional[dict]:
        container = self._container()
        try:
            return await container.read_item(item=food_id, partition_key=food_id)
        except Exception:
            return None

    async def get_by_barcode(self, barcode: str) -> Optional[dict]:
        # Only ever resolves to global/system records — never a user-submitted
        # custom food, which would let one user's bad data poison another
        # user's barcode scan of a real product.
        container = self._container()
        query = (
            "SELECT * FROM c WHERE c.barcode = @barcode "
            "AND (NOT IS_DEFINED(c.created_by_user_id) OR IS_NULL(c.created_by_user_id))"
        )
        params = [{"name": "@barcode", "value": barcode}]
        async for item in container.query_items(query=query, parameters=params):
            return item
        return None

    async def create(self, food: dict) -> dict:
        container = self._container()
        record = {**food, "id": str(uuid.uuid4())}
        await container.create_item(record)
        return record


class CosmosWorkoutRepository:
    def __init__(self, client: CosmosClient, database_name: str):
        self._client = client
        self._database_name = database_name

    def _container(self):
        return self._client.get_database_client(self._database_name).get_container_client("workouts")

    async def create(self, workout: dict) -> dict:
        container = self._container()
        now = datetime.now(timezone.utc).isoformat()
        record = {**workout, "id": str(uuid.uuid4()), "created_at": now, "updated_at": now}
        await container.create_item(record)
        return record

    async def list_for_user(self, user_id: str, workout_type: Optional[str] = None) -> list[dict]:
        container = self._container()
        query = "SELECT * FROM c WHERE c.user_id = @user_id"
        params = [{"name": "@user_id", "value": user_id}]
        if workout_type is not None:
            query += " AND c.type = @type"
            params.append({"name": "@type", "value": workout_type})
        items = [
            item
            async for item in container.query_items(query=query, parameters=params, partition_key=user_id)
        ]
        return sorted(items, key=lambda w: w["started_at"], reverse=True)

    async def get(self, user_id: str, workout_id: str) -> Optional[dict]:
        container = self._container()
        try:
            return await container.read_item(item=workout_id, partition_key=user_id)
        except Exception:
            return None

    async def update(self, user_id: str, workout_id: str, updates: dict) -> Optional[dict]:
        workout = await self.get(user_id, workout_id)
        if not workout:
            return None
        workout.update(updates)
        workout["updated_at"] = datetime.now(timezone.utc).isoformat()
        await self._container().replace_item(item=workout_id, body=workout)
        return workout

    async def delete(self, user_id: str, workout_id: str) -> bool:
        workout = await self.get(user_id, workout_id)
        if not workout:
            return False
        await self._container().delete_item(item=workout_id, partition_key=user_id)
        return True


class CosmosExerciseRepository:
    def __init__(self, client: CosmosClient, database_name: str):
        self._client = client
        self._database_name = database_name

    def _container(self):
        return self._client.get_database_client(self._database_name).get_container_client("exercises")

    async def search(self, query: str) -> list[dict]:
        container = self._container()
        sql_query = "SELECT * FROM c WHERE CONTAINS(LOWER(c.name), @query)"
        params = [{"name": "@query", "value": query.lower()}]
        return [item async for item in container.query_items(query=sql_query, parameters=params)]

    async def get(self, exercise_id: str) -> Optional[dict]:
        container = self._container()
        try:
            return await container.read_item(item=exercise_id, partition_key=exercise_id)
        except Exception:
            return None

    async def create(self, exercise: dict) -> dict:
        container = self._container()
        record = {**exercise, "id": str(uuid.uuid4())}
        await container.create_item(record)
        return record


class CosmosMoodEntryRepository:
    def __init__(self, client: CosmosClient, database_name: str):
        self._client = client
        self._database_name = database_name

    def _container(self):
        return self._client.get_database_client(self._database_name).get_container_client("mood_entries")

    async def create(self, entry: dict) -> dict:
        container = self._container()
        now = datetime.now(timezone.utc).isoformat()
        record = {**entry, "id": str(uuid.uuid4()), "created_at": now, "updated_at": now}
        await container.create_item(record)
        return record

    async def list_for_user(
        self, user_id: str, start: Optional[date] = None, end: Optional[date] = None
    ) -> list[dict]:
        container = self._container()
        query = "SELECT * FROM c WHERE c.user_id = @user_id"
        params = [{"name": "@user_id", "value": user_id}]
        if start is not None:
            query += " AND c.logged_at >= @start"
            params.append({"name": "@start", "value": start.isoformat()})
        if end is not None:
            query += " AND c.logged_at <= @end"
            params.append({"name": "@end", "value": f"{end.isoformat()}T23:59:59"})
        items = [
            item
            async for item in container.query_items(query=query, parameters=params, partition_key=user_id)
        ]
        return sorted(items, key=lambda e: e["logged_at"], reverse=True)

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


class CosmosJournalEntryRepository:
    def __init__(self, client: CosmosClient, database_name: str):
        self._client = client
        self._database_name = database_name

    def _container(self):
        return self._client.get_database_client(self._database_name).get_container_client("journal_entries")

    async def create(self, entry: dict) -> dict:
        container = self._container()
        now = datetime.now(timezone.utc).isoformat()
        record = {**entry, "id": str(uuid.uuid4()), "created_at": now, "updated_at": now}
        await container.create_item(record)
        return record

    async def list_for_user(self, user_id: str) -> list[dict]:
        container = self._container()
        query = "SELECT * FROM c WHERE c.user_id = @user_id"
        params = [{"name": "@user_id", "value": user_id}]
        items = [
            item
            async for item in container.query_items(query=query, parameters=params, partition_key=user_id)
        ]
        return sorted(items, key=lambda e: e["written_at"], reverse=True)

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


class CosmosScreenTimeRuleRepository:
    def __init__(self, client: CosmosClient, database_name: str):
        self._client = client
        self._database_name = database_name

    def _container(self):
        return self._client.get_database_client(self._database_name).get_container_client("screentime_rules")

    async def create(self, rule: dict) -> dict:
        container = self._container()
        now = datetime.now(timezone.utc).isoformat()
        record = {**rule, "id": str(uuid.uuid4()), "created_at": now, "updated_at": now}
        await container.create_item(record)
        return record

    async def list_for_user(self, user_id: str) -> list[dict]:
        container = self._container()
        query = "SELECT * FROM c WHERE c.user_id = @user_id"
        params = [{"name": "@user_id", "value": user_id}]
        items = [
            item
            async for item in container.query_items(query=query, parameters=params, partition_key=user_id)
        ]
        return sorted(items, key=lambda r: r["created_at"], reverse=True)

    async def get(self, user_id: str, rule_id: str) -> Optional[dict]:
        container = self._container()
        try:
            return await container.read_item(item=rule_id, partition_key=user_id)
        except Exception:
            return None

    async def update(self, user_id: str, rule_id: str, updates: dict) -> Optional[dict]:
        rule = await self.get(user_id, rule_id)
        if not rule:
            return None
        rule.update(updates)
        rule["updated_at"] = datetime.now(timezone.utc).isoformat()
        await self._container().replace_item(item=rule_id, body=rule)
        return rule

    async def delete(self, user_id: str, rule_id: str) -> bool:
        rule = await self.get(user_id, rule_id)
        if not rule:
            return False
        await self._container().delete_item(item=rule_id, partition_key=user_id)
        return True
