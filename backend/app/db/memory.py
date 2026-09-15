import uuid
from datetime import date, datetime, timezone
from typing import Optional


class InMemoryUserRepository:
    def __init__(self):
        self._by_id: dict[str, dict] = {}
        self._id_by_email: dict[str, str] = {}

    async def get_by_email(self, email: str) -> Optional[dict]:
        user_id = self._id_by_email.get(email.lower())
        return self._by_id.get(user_id) if user_id else None

    async def get_by_id(self, user_id: str) -> Optional[dict]:
        return self._by_id.get(user_id)

    async def create(self, user: dict) -> dict:
        user_id = str(uuid.uuid4())
        record = {
            **user,
            "id": user_id,
            "email": user["email"].lower(),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self._by_id[user_id] = record
        self._id_by_email[record["email"]] = user_id
        return record


class InMemoryMealEntryRepository:
    def __init__(self):
        self._entries: dict[str, dict] = {}

    async def create(self, entry: dict) -> dict:
        entry_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        record = {**entry, "id": entry_id, "created_at": now, "updated_at": now}
        self._entries[entry_id] = record
        return record

    async def list_for_day(self, user_id: str, day: date) -> list[dict]:
        return [
            e
            for e in self._entries.values()
            if e["user_id"] == user_id and e["logged_at"].startswith(day.isoformat())
        ]

    async def get(self, user_id: str, entry_id: str) -> Optional[dict]:
        entry = self._entries.get(entry_id)
        return entry if entry and entry["user_id"] == user_id else None

    async def update(self, user_id: str, entry_id: str, updates: dict) -> Optional[dict]:
        entry = await self.get(user_id, entry_id)
        if not entry:
            return None
        entry.update(updates)
        entry["updated_at"] = datetime.now(timezone.utc).isoformat()
        return entry

    async def delete(self, user_id: str, entry_id: str) -> bool:
        entry = await self.get(user_id, entry_id)
        if not entry:
            return False
        del self._entries[entry["id"]]
        return True


class InMemoryFoodRepository:
    def __init__(self, seed: list[dict]):
        self._foods = {f["id"]: dict(f) for f in seed}

    async def search(self, query: str) -> list[dict]:
        q = query.lower()
        return [f for f in self._foods.values() if q in f["name"].lower()]

    async def get(self, food_id: str) -> Optional[dict]:
        return self._foods.get(food_id)


SEED_FOODS: list[dict] = [
    {
        "id": "chicken-breast", "name": "Chicken Breast, cooked",
        "serving_size": 100, "serving_unit": "g",
        "calories_per_serving": 165, "protein_g": 31, "carbs_g": 0, "fat_g": 3.6,
    },
    {
        "id": "white-rice", "name": "White Rice, cooked",
        "serving_size": 100, "serving_unit": "g",
        "calories_per_serving": 130, "protein_g": 2.7, "carbs_g": 28, "fat_g": 0.3,
    },
    {
        "id": "banana", "name": "Banana",
        "serving_size": 118, "serving_unit": "g",
        "calories_per_serving": 105, "protein_g": 1.3, "carbs_g": 27, "fat_g": 0.4,
    },
    {
        "id": "egg", "name": "Egg, large",
        "serving_size": 50, "serving_unit": "g",
        "calories_per_serving": 78, "protein_g": 6.3, "carbs_g": 0.6, "fat_g": 5.3,
    },
]
