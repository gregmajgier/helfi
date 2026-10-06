import json
import uuid
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Optional

_EXERCISES_SEED_PATH = Path(__file__).parent / "data" / "exercises_seed.json"
_FOODS_SEED_PATH = Path(__file__).parent / "data" / "foods_seed.json"
_COMMON_FOODS_SEED_PATH = Path(__file__).parent / "data" / "common_foods_seed.json"


def _load_seed_exercises() -> list[dict]:
    records = json.loads(_EXERCISES_SEED_PATH.read_text())
    return [{**r, "created_by_user_id": None} for r in records]


def _load_seed_foods() -> list[dict]:
    # Open Food Facts' category search skews heavily toward branded/regional
    # packaged products (mostly French/German), so it barely covers common
    # English staple-food search terms like "chicken" or "apple" even though
    # it's great for barcode lookups. The hand-authored common-foods list
    # fills that gap; OFF data still covers real barcode scanning.
    off_records = json.loads(_FOODS_SEED_PATH.read_text())
    common_records = json.loads(_COMMON_FOODS_SEED_PATH.read_text())
    return [{**r, "created_by_user_id": None} for r in common_records + off_records]


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
        return await self.list_range(user_id, day, day)

    async def list_range(self, user_id: str, start: date, end: date) -> list[dict]:
        # Older entries have no explicit "day"; fall back to the logged_at date.
        results = [
            e
            for e in self._entries.values()
            if e["user_id"] == user_id
            and start.isoformat() <= (e.get("day") or e["logged_at"][:10]) <= end.isoformat()
        ]
        return sorted(results, key=lambda e: e["logged_at"])

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

    async def get(self, food_id: str) -> Optional[dict]:
        return self._foods.get(food_id)

    async def get_by_barcode(self, barcode: str) -> Optional[dict]:
        # Only ever resolves to global/system records (created_by_user_id is
        # None) — never a user-submitted custom food, which would let one
        # user's bad data poison another user's barcode scan of a real product.
        for food in self._foods.values():
            if food.get("barcode") == barcode and food.get("created_by_user_id") is None:
                return food
        return None

    async def create(self, food: dict) -> dict:
        food_id = str(uuid.uuid4())
        record = {**food, "id": food_id}
        self._foods[food_id] = record
        return record

    async def search(self, query: str, user_id: str, limit: int = 25) -> list[dict]:
        q = query.strip().lower()
        matches = [
            f
            for f in self._foods.values()
            if q in f["name"].lower() and f.get("created_by_user_id") in (None, user_id)
        ]
        return rank_food_matches(matches, q)[:limit]

    async def list_for_user(self, user_id: str) -> list[dict]:
        mine = [f for f in self._foods.values() if f.get("created_by_user_id") == user_id]
        return sorted(mine, key=lambda f: f["name"].lower())

    async def update(self, food_id: str, user_id: str, updates: dict) -> Optional[dict]:
        food = self._foods.get(food_id)
        if not food or food.get("created_by_user_id") != user_id:
            return None
        food.update(updates)
        return food

    async def delete(self, food_id: str, user_id: str) -> bool:
        food = self._foods.get(food_id)
        if not food or food.get("created_by_user_id") != user_id:
            return False
        del self._foods[food_id]
        return True


def rank_food_matches(foods: list[dict], q: str) -> list[dict]:
    """Prefix matches first, then word-start matches, then shorter names."""

    def key(food: dict):
        name = food["name"].lower()
        if name.startswith(q):
            tier = 0
        elif f" {q}" in name:
            tier = 1
        else:
            tier = 2
        return (tier, len(name), name)

    return sorted(foods, key=key)


class InMemoryDocRepository:
    """Generic per-user document store used by the smaller food-module containers."""

    def __init__(self):
        self._docs: dict[str, dict] = {}

    async def create(self, doc: dict) -> dict:
        doc_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        record = {**doc, "id": doc_id, "created_at": now, "updated_at": now}
        self._docs[doc_id] = record
        return record

    async def put(self, doc: dict) -> dict:
        """Upsert a document with a caller-chosen id (one-per-user docs, favorites)."""
        now = datetime.now(timezone.utc).isoformat()
        existing = self._docs.get(doc["id"])
        if existing and existing["user_id"] != doc["user_id"]:
            raise PermissionError("document id belongs to another user")
        created = existing["created_at"] if existing else now
        record = {**doc, "created_at": created, "updated_at": now}
        self._docs[doc["id"]] = record
        return record

    async def list_for_user(
        self,
        user_id: str,
        field: Optional[str] = None,
        gte: Optional[str] = None,
        lte: Optional[str] = None,
    ) -> list[dict]:
        results = [d for d in self._docs.values() if d["user_id"] == user_id]
        if field is not None:
            if gte is not None:
                results = [d for d in results if d.get(field, "") >= gte]
            if lte is not None:
                results = [d for d in results if d.get(field, "") <= lte]
        return sorted(results, key=lambda d: (d.get(field or "created_at", ""), d["created_at"]))

    async def get(self, user_id: str, doc_id: str) -> Optional[dict]:
        doc = self._docs.get(doc_id)
        return doc if doc and doc["user_id"] == user_id else None

    async def update(self, user_id: str, doc_id: str, updates: dict) -> Optional[dict]:
        doc = await self.get(user_id, doc_id)
        if not doc:
            return None
        doc.update(updates)
        doc["updated_at"] = datetime.now(timezone.utc).isoformat()
        return doc

    async def delete(self, user_id: str, doc_id: str) -> bool:
        doc = await self.get(user_id, doc_id)
        if not doc:
            return False
        del self._docs[doc_id]
        return True


SEED_FOODS: list[dict] = _load_seed_foods()


class InMemoryWorkoutRepository:
    def __init__(self):
        self._workouts: dict[str, dict] = {}

    async def create(self, workout: dict) -> dict:
        workout_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        record = {**workout, "id": workout_id, "created_at": now, "updated_at": now}
        self._workouts[workout_id] = record
        return record

    async def list_for_user(self, user_id: str, workout_type: Optional[str] = None) -> list[dict]:
        results = [w for w in self._workouts.values() if w["user_id"] == user_id]
        if workout_type is not None:
            results = [w for w in results if w["type"] == workout_type]
        return sorted(results, key=lambda w: w["started_at"], reverse=True)

    async def get(self, user_id: str, workout_id: str) -> Optional[dict]:
        workout = self._workouts.get(workout_id)
        return workout if workout and workout["user_id"] == user_id else None

    async def update(self, user_id: str, workout_id: str, updates: dict) -> Optional[dict]:
        workout = await self.get(user_id, workout_id)
        if not workout:
            return None
        workout.update(updates)
        workout["updated_at"] = datetime.now(timezone.utc).isoformat()
        return workout

    async def delete(self, user_id: str, workout_id: str) -> bool:
        workout = await self.get(user_id, workout_id)
        if not workout:
            return False
        del self._workouts[workout["id"]]
        return True


class InMemoryExerciseRepository:
    def __init__(self, seed: list[dict]):
        self._exercises = {e["id"]: dict(e) for e in seed}

    async def search(self, query: str) -> list[dict]:
        q = query.lower()
        return [e for e in self._exercises.values() if q in e["name"].lower()]

    async def get(self, exercise_id: str) -> Optional[dict]:
        return self._exercises.get(exercise_id)

    async def create(self, exercise: dict) -> dict:
        exercise_id = str(uuid.uuid4())
        record = {**exercise, "id": exercise_id}
        self._exercises[exercise_id] = record
        return record


SEED_EXERCISES: list[dict] = _load_seed_exercises()


class InMemoryMoodEntryRepository:
    def __init__(self):
        self._entries: dict[str, dict] = {}

    async def create(self, entry: dict) -> dict:
        entry_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        record = {**entry, "id": entry_id, "created_at": now, "updated_at": now}
        self._entries[entry_id] = record
        return record

    async def list_for_user(
        self, user_id: str, start: Optional[date] = None, end: Optional[date] = None
    ) -> list[dict]:
        results = [e for e in self._entries.values() if e["user_id"] == user_id]
        if start is not None:
            results = [e for e in results if e["logged_at"] >= start.isoformat()]
        if end is not None:
            results = [e for e in results if e["logged_at"] <= f"{end.isoformat()}T23:59:59"]
        return sorted(results, key=lambda e: e["logged_at"], reverse=True)

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


class InMemoryJournalEntryRepository:
    def __init__(self):
        self._entries: dict[str, dict] = {}

    async def create(self, entry: dict) -> dict:
        entry_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        record = {**entry, "id": entry_id, "created_at": now, "updated_at": now}
        self._entries[entry_id] = record
        return record

    async def list_for_user(self, user_id: str) -> list[dict]:
        results = [e for e in self._entries.values() if e["user_id"] == user_id]
        return sorted(results, key=lambda e: e["written_at"], reverse=True)

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


class InMemoryScreenTimeRuleRepository:
    def __init__(self):
        self._rules: dict[str, dict] = {}

    async def create(self, rule: dict) -> dict:
        rule_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        record = {**rule, "id": rule_id, "created_at": now, "updated_at": now}
        self._rules[rule_id] = record
        return record

    async def list_for_user(self, user_id: str) -> list[dict]:
        results = [r for r in self._rules.values() if r["user_id"] == user_id]
        return sorted(results, key=lambda r: r["created_at"], reverse=True)

    async def get(self, user_id: str, rule_id: str) -> Optional[dict]:
        rule = self._rules.get(rule_id)
        return rule if rule and rule["user_id"] == user_id else None

    async def update(self, user_id: str, rule_id: str, updates: dict) -> Optional[dict]:
        rule = await self.get(user_id, rule_id)
        if not rule:
            return None
        rule.update(updates)
        rule["updated_at"] = datetime.now(timezone.utc).isoformat()
        return rule

    async def delete(self, user_id: str, rule_id: str) -> bool:
        rule = await self.get(user_id, rule_id)
        if not rule:
            return False
        del self._rules[rule["id"]]
        return True


class InMemoryScreenTimeUsageRepository:
    def __init__(self):
        self._records: dict[tuple[str, str], dict] = {}

    async def upsert(self, user_id: str, day: date, total_minutes: int, dumb_minutes: int) -> dict:
        record = {
            "id": f"usage-{day.isoformat()}",
            "user_id": user_id,
            "date": day.isoformat(),
            "total_minutes": total_minutes,
            "dumb_minutes": dumb_minutes,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        self._records[(user_id, record["date"])] = record
        return dict(record)

    async def list_range(self, user_id: str, start: date, end: date) -> list[dict]:
        results = [
            dict(r)
            for (uid, d), r in self._records.items()
            if uid == user_id and start.isoformat() <= d <= end.isoformat()
        ]
        return sorted(results, key=lambda r: r["date"])
