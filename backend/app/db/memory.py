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


SEED_EXERCISES: list[dict] = [
    {"id": "bench-press", "name": "Bench Press", "category": "chest", "is_bodyweight": False, "created_by_user_id": None},
    {"id": "squat", "name": "Barbell Squat", "category": "legs", "is_bodyweight": False, "created_by_user_id": None},
    {"id": "deadlift", "name": "Deadlift", "category": "back", "is_bodyweight": False, "created_by_user_id": None},
    {"id": "overhead-press", "name": "Overhead Press", "category": "shoulders", "is_bodyweight": False, "created_by_user_id": None},
    {"id": "bicep-curl", "name": "Bicep Curl", "category": "arms", "is_bodyweight": False, "created_by_user_id": None},
    {"id": "pull-up", "name": "Pull-Up", "category": "back", "is_bodyweight": True, "created_by_user_id": None},
    {"id": "push-up", "name": "Push-Up", "category": "chest", "is_bodyweight": True, "created_by_user_id": None},
    {"id": "plank", "name": "Plank", "category": "core", "is_bodyweight": True, "created_by_user_id": None},
    {"id": "lunge", "name": "Lunge", "category": "legs", "is_bodyweight": True, "created_by_user_id": None},
]
