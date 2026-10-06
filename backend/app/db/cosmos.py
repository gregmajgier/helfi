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

# Per-user containers backed by CosmosDocRepository, all partitioned by /user_id.
DOC_CONTAINERS = (
    "profiles",
    "weight_entries",
    "favorites",
    "recipes",
    "meal_plan",
    "shopping_items",
    "water_entries",
    "fasting_sessions",
)


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
    await database.create_container_if_not_exists(
        id="screentime_usage", partition_key=PartitionKey(path="/user_id")
    )

    for container_name in DOC_CONTAINERS:
        await database.create_container_if_not_exists(
            id=container_name, partition_key=PartitionKey(path="/user_id")
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
        return await self.list_range(user_id, day, day)

    async def list_range(self, user_id: str, start: date, end: date) -> list[dict]:
        # Older entries have no explicit "day"; fall back to the logged_at date.
        container = self._container()
        query = (
            "SELECT * FROM c WHERE c.user_id = @user_id AND ("
            "(IS_DEFINED(c.day) AND c.day >= @start AND c.day <= @end) OR "
            "(NOT IS_DEFINED(c.day) AND SUBSTRING(c.logged_at, 0, 10) >= @start "
            "AND SUBSTRING(c.logged_at, 0, 10) <= @end))"
        )
        params = [
            {"name": "@user_id", "value": user_id},
            {"name": "@start", "value": start.isoformat()},
            {"name": "@end", "value": end.isoformat()},
        ]
        items = [
            item
            async for item in container.query_items(query=query, parameters=params, partition_key=user_id)
        ]
        return sorted(items, key=lambda e: e["logged_at"])

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

    async def search(self, query: str, user_id: str, limit: int = 25) -> list[dict]:
        from .memory import rank_food_matches

        q = query.strip().lower()
        container = self._container()
        sql = (
            "SELECT TOP 200 * FROM c WHERE CONTAINS(LOWER(c.name), @q) AND "
            "(NOT IS_DEFINED(c.created_by_user_id) OR IS_NULL(c.created_by_user_id) "
            "OR c.created_by_user_id = @user_id)"
        )
        params = [{"name": "@q", "value": q}, {"name": "@user_id", "value": user_id}]
        items = [item async for item in container.query_items(query=sql, parameters=params)]
        return rank_food_matches(items, q)[:limit]

    async def list_for_user(self, user_id: str) -> list[dict]:
        container = self._container()
        sql = "SELECT * FROM c WHERE c.created_by_user_id = @user_id"
        params = [{"name": "@user_id", "value": user_id}]
        items = [item async for item in container.query_items(query=sql, parameters=params)]
        return sorted(items, key=lambda f: f["name"].lower())

    async def update(self, food_id: str, user_id: str, updates: dict) -> Optional[dict]:
        food = await self.get(food_id)
        if not food or food.get("created_by_user_id") != user_id:
            return None
        food.update(updates)
        await self._container().replace_item(item=food_id, body=food)
        return food

    async def delete(self, food_id: str, user_id: str) -> bool:
        food = await self.get(food_id)
        if not food or food.get("created_by_user_id") != user_id:
            return False
        await self._container().delete_item(item=food_id, partition_key=food_id)
        return True


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


class CosmosScreenTimeUsageRepository:
    def __init__(self, client: CosmosClient, database_name: str):
        self._client = client
        self._database_name = database_name

    def _container(self):
        return self._client.get_database_client(self._database_name).get_container_client("screentime_usage")

    async def upsert(self, user_id: str, day: date, total_minutes: int, dumb_minutes: int) -> dict:
        record = {
            "id": f"usage-{day.isoformat()}",
            "user_id": user_id,
            "date": day.isoformat(),
            "total_minutes": total_minutes,
            "dumb_minutes": dumb_minutes,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        await self._container().upsert_item(record)
        return record

    async def list_range(self, user_id: str, start: date, end: date) -> list[dict]:
        container = self._container()
        query = "SELECT * FROM c WHERE c.user_id = @user_id AND c.date >= @start AND c.date <= @end"
        params = [
            {"name": "@user_id", "value": user_id},
            {"name": "@start", "value": start.isoformat()},
            {"name": "@end", "value": end.isoformat()},
        ]
        items = [
            item
            async for item in container.query_items(query=query, parameters=params, partition_key=user_id)
        ]
        return sorted(items, key=lambda r: r["date"])


class CosmosDocRepository:
    """Generic per-user document store, one instance per container name."""

    # Only these names are ever interpolated into a query string (never client input).
    _RANGE_FIELDS = {"day", "started_at", "created_at", "logged_at"}

    def __init__(self, client: CosmosClient, database_name: str, container_name: str):
        if container_name not in DOC_CONTAINERS:
            raise ValueError(f"unknown container {container_name}")
        self._client = client
        self._database_name = database_name
        self._container_name = container_name

    def _container(self):
        return self._client.get_database_client(self._database_name).get_container_client(
            self._container_name
        )

    async def create(self, doc: dict) -> dict:
        now = datetime.now(timezone.utc).isoformat()
        record = {**doc, "id": str(uuid.uuid4()), "created_at": now, "updated_at": now}
        await self._container().create_item(record)
        return record

    async def put(self, doc: dict) -> dict:
        existing = await self.get(doc["user_id"], doc["id"])
        now = datetime.now(timezone.utc).isoformat()
        record = {**doc, "created_at": existing["created_at"] if existing else now, "updated_at": now}
        await self._container().upsert_item(record)
        return record

    async def list_for_user(
        self,
        user_id: str,
        field: Optional[str] = None,
        gte: Optional[str] = None,
        lte: Optional[str] = None,
    ) -> list[dict]:
        query = "SELECT * FROM c WHERE c.user_id = @user_id"
        params = [{"name": "@user_id", "value": user_id}]
        if field is not None:
            if field not in self._RANGE_FIELDS:
                raise ValueError(f"unsupported range field {field}")
            if gte is not None:
                query += f" AND c.{field} >= @gte"
                params.append({"name": "@gte", "value": gte})
            if lte is not None:
                query += f" AND c.{field} <= @lte"
                params.append({"name": "@lte", "value": lte})
        items = [
            item
            async for item in self._container().query_items(
                query=query, parameters=params, partition_key=user_id
            )
        ]
        return sorted(items, key=lambda d: (d.get(field or "created_at", ""), d["created_at"]))

    async def get(self, user_id: str, doc_id: str) -> Optional[dict]:
        try:
            return await self._container().read_item(item=doc_id, partition_key=user_id)
        except Exception:
            return None

    async def update(self, user_id: str, doc_id: str, updates: dict) -> Optional[dict]:
        doc = await self.get(user_id, doc_id)
        if not doc:
            return None
        doc.update(updates)
        doc["updated_at"] = datetime.now(timezone.utc).isoformat()
        await self._container().replace_item(item=doc_id, body=doc)
        return doc

    async def delete(self, user_id: str, doc_id: str) -> bool:
        doc = await self.get(user_id, doc_id)
        if not doc:
            return False
        await self._container().delete_item(item=doc_id, partition_key=user_id)
        return True
