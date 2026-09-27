# Training Tracker Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the Training Tracker module (manual strength/calisthenics logging with an exercise library, manual cardio logging, and session history) as the second marketable module, following the meal tracker.

**Architecture:** Extends the existing FastAPI backend with a `/workouts` router and two new repository-interface-backed containers (`workouts`, `exercises`), following the exact same in-memory/Cosmos-swap pattern already used for meals/foods. The Expo client gets a new `training-tracker` module (routes + module logic) mirroring `meal-tracker`'s structure. The app's home screen (`src/app/index.tsx`) becomes a hub linking to both shipped modules, per the platform spec's rollout note, instead of redirecting straight to meal-tracker.

**Tech Stack:** Python 3.12 / FastAPI / Pydantic v2 / pytest+pytest-asyncio (backend, unchanged). Expo Router / React 19 / TypeScript (client, unchanged). No new dependencies — GPS tracking and third-party integrations are deferred, so no maps SDK or OAuth libraries are needed.

**Spec:**
- `docs/superpowers/specs/2026-09-16-training-tracker-design.md`
- `docs/superpowers/specs/2026-09-16-platform-architecture-design.md` (home-hub requirement)

## Global Constraints

- Every timestamp is stored and transmitted as an ISO 8601 UTC string.
- The `workouts` container is partitioned on `/user_id`; the `exercises` container (global + user-custom, same pattern as `foods`) is partitioned on `/id`.
- The client never talks to Cosmos DB directly — every read/write goes through the FastAPI backend.
- Distances and weights are stored/transmitted in metric units (meters, kg) with unit conversion at the display layer, per the training-tracker spec's open assumption.
- **v1 is manual-only.** No in-app GPS tracking, route maps, or location permissions (spec: "Out of scope"). No Strava/Apple Health/Google Fit integrations — `source` is always `"manual"` and is server-assigned, never client input; `external_id`/`integration_connections` are reserved for a future version and are not built here.
- Per AGENTS.md, Expo has changed significantly — read https://docs.expo.dev/versions/v57.0.0/ before writing any Expo-specific or native-module code. This plan doesn't expect to need any (no maps, no location, no camera), but check the docs first if a task turns out to need one.
- Per the platform spec, there is no automated client test suite in this phase: logic-only frontend tasks are verified with `npx tsc --noEmit`; screen tasks are verified by running the app and manually exercising the flow.

## Review Focus

- A strength/calisthenics workout submitted with an empty or missing `exercises` list should be rejected (422), not silently stored as a workout with no exercises.
- A running/cycling workout submitted without `distance_m` should be rejected (422) rather than stored as a cardio entry with no distance.
- Negative or zero `duration_s`, `distance_m`, or `reps` should be rejected rather than silently stored as nonsensical stats that would corrupt history totals.
- A custom exercise added by one user should appear in another user's exercise-library search results, since the library is global + user-contributed, not scoped per-user (mirrors the `foods` pattern).
- Filtering workout history with an invalid `type` query value should return a clean 422, not a 500.

---

## File Structure

**Backend (extends existing `backend/` tree):**
```
backend/app/
  db/
    base.py           # (modified) + WorkoutRepository, ExerciseRepository Protocols
    memory.py          # (modified) + InMemoryWorkoutRepository, InMemoryExerciseRepository, SEED_EXERCISES
    cosmos.py           # (modified) + CosmosWorkoutRepository, CosmosExerciseRepository, containers
  deps.py                # (modified) + get_workout_repo, get_exercise_repo
  main.py                 # (modified) registers the workouts router
  workouts/
    __init__.py
    models.py               # Exercise + Workout request/response models
    router.py                # /workouts routes
backend/tests/
  conftest.py            # (modified) fresh workout/exercise repos per test
  test_memory_repositories.py  # (modified) + workout/exercise repo tests
  test_cosmos_repos.py          # (modified) + workout/exercise cosmos repo tests
  test_workouts_router.py        # new
```

**Client (extends existing Expo app):**
```
src/app/
  index.tsx                   # (modified) becomes a hub linking to both modules
  training-tracker/
    _layout.tsx
    index.tsx                  # history (home)
    log-strength.tsx
    log-cardio.tsx
    exercise-library.tsx
src/modules/
  training_tracker/
    types.ts
    api.ts
```

---

## Task 1: Workout & exercise repository interfaces, in-memory implementations, and dependency wiring

**Files:**
- Modify: `backend/app/db/base.py`, `backend/app/db/memory.py`, `backend/app/deps.py`, `backend/tests/conftest.py`, `backend/tests/test_memory_repositories.py`

**Interfaces:**
- Consumes: nothing new (uses the same `uuid`/`datetime` patterns already in `db/memory.py`).
- Produces: `WorkoutRepository`/`ExerciseRepository` Protocols from `app.db.base`; `InMemoryWorkoutRepository`, `InMemoryExerciseRepository`, `SEED_EXERCISES` from `app.db.memory`; `get_workout_repo()`, `get_exercise_repo()` from `app.deps` — used by every task from Task 2 onward.

- [ ] **Step 1: Write the failing tests**

Replace the `from app.db.memory import ...` line at the top of `backend/tests/test_memory_repositories.py` with:
```python
from app.db.memory import (
    SEED_EXERCISES,
    SEED_FOODS,
    InMemoryExerciseRepository,
    InMemoryFoodRepository,
    InMemoryMealEntryRepository,
    InMemoryUserRepository,
    InMemoryWorkoutRepository,
)
```

Append to `backend/tests/test_memory_repositories.py`:
```python
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
```

- [ ] **Step 2: Run to verify failure**

```bash
cd backend && pytest tests/test_memory_repositories.py -v
```
Expected: FAIL with `ImportError: cannot import name 'InMemoryWorkoutRepository'`.

- [ ] **Step 3: Implement**

Append to `backend/app/db/base.py` (the existing `Optional`/`Protocol` imports already cover this — no new imports needed):
```python
class WorkoutRepository(Protocol):
    async def create(self, workout: dict) -> dict: ...
    async def list_for_user(self, user_id: str, workout_type: Optional[str] = None) -> list[dict]: ...
    async def get(self, user_id: str, workout_id: str) -> Optional[dict]: ...
    async def update(self, user_id: str, workout_id: str, updates: dict) -> Optional[dict]: ...
    async def delete(self, user_id: str, workout_id: str) -> bool: ...


class ExerciseRepository(Protocol):
    async def search(self, query: str) -> list[dict]: ...
    async def get(self, exercise_id: str) -> Optional[dict]: ...
    async def create(self, exercise: dict) -> dict: ...
```

Append to `backend/app/db/memory.py` (the existing `uuid`/`datetime`/`timezone`/`Optional` imports already cover this):
```python
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
```

In `backend/app/deps.py`, replace the `from .db.memory import (...)` line with:
```python
from .db.memory import (
    SEED_EXERCISES,
    SEED_FOODS,
    InMemoryExerciseRepository,
    InMemoryFoodRepository,
    InMemoryMealEntryRepository,
    InMemoryUserRepository,
    InMemoryWorkoutRepository,
)
```
and add below the existing `_food_repo = InMemoryFoodRepository(SEED_FOODS)` line:
```python
_memory_workout_repo = InMemoryWorkoutRepository()
_exercise_repo = InMemoryExerciseRepository(SEED_EXERCISES)
```
and add below the existing `get_food_repo` function:
```python
def get_workout_repo():
    return _memory_workout_repo


def get_exercise_repo():
    return _exercise_repo
```

Replace `backend/tests/conftest.py` with:
```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from fastapi.testclient import TestClient

from app import deps
from app.db.memory import (
    SEED_EXERCISES,
    SEED_FOODS,
    InMemoryExerciseRepository,
    InMemoryFoodRepository,
    InMemoryMealEntryRepository,
    InMemoryUserRepository,
    InMemoryWorkoutRepository,
)
from app.main import app


@pytest.fixture()
def client():
    user_repo = InMemoryUserRepository()
    meal_entry_repo = InMemoryMealEntryRepository()
    food_repo = InMemoryFoodRepository(SEED_FOODS)
    workout_repo = InMemoryWorkoutRepository()
    exercise_repo = InMemoryExerciseRepository(SEED_EXERCISES)

    app.dependency_overrides[deps.get_user_repo] = lambda: user_repo
    app.dependency_overrides[deps.get_meal_entry_repo] = lambda: meal_entry_repo
    app.dependency_overrides[deps.get_food_repo] = lambda: food_repo
    app.dependency_overrides[deps.get_workout_repo] = lambda: workout_repo
    app.dependency_overrides[deps.get_exercise_repo] = lambda: exercise_repo

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture()
def auth_headers(client):
    def _make(email: str = "default@example.com", password: str = "password123") -> dict:
        client.post("/auth/register", json={"email": email, "password": password})
        response = client.post("/auth/login", json={"email": email, "password": password})
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    return _make
```

- [ ] **Step 4: Run to verify pass**

```bash
cd backend && pytest tests/ -v
```
Expected: all tests pass (`test_memory_repositories.py` now has 6 passed).

- [ ] **Step 5: Commit**

```bash
git add backend/app/db/base.py backend/app/db/memory.py backend/app/deps.py backend/tests/conftest.py backend/tests/test_memory_repositories.py
git commit -m "$(cat <<'EOF'
Add workout and exercise repository interfaces with in-memory implementations

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: Exercise library endpoints

**Files:**
- Create: `backend/app/workouts/__init__.py`, `backend/app/workouts/models.py`, `backend/app/workouts/router.py`, `backend/tests/test_workouts_router.py`
- Modify: `backend/app/main.py` (register the workouts router)

**Interfaces:**
- Consumes: `get_current_user_id`, `get_exercise_repo` (Task 1).
- Produces: `GET /workouts/exercises`, `POST /workouts/exercises`; `ExerciseCreate`, `ExerciseOut` models from `app.workouts.models`, reused by Task 3; the `router` object from `app.workouts.router`, extended by Task 3.

- [ ] **Step 1: Write the failing tests**

`backend/tests/test_workouts_router.py`:
```python
def test_search_exercises_matches_partial_case_insensitive_name(client, auth_headers):
    headers = auth_headers()

    response = client.get("/workouts/exercises", params={"q": "BENCH"}, headers=headers)

    assert response.status_code == 200
    names = [e["name"] for e in response.json()]
    assert any("Bench" in name for name in names)


def test_search_exercises_requires_auth(client):
    response = client.get("/workouts/exercises", params={"q": "bench"})

    assert response.status_code == 403


def test_create_custom_exercise_is_then_searchable_by_other_users(client, auth_headers):
    headers_a = auth_headers(email="creator@example.com")
    headers_b = auth_headers(email="other@example.com")

    create = client.post(
        "/workouts/exercises",
        json={"name": "Cable Row", "category": "back", "is_bodyweight": False},
        headers=headers_a,
    )
    assert create.status_code == 201
    assert create.json()["created_by_user_id"]

    search = client.get("/workouts/exercises", params={"q": "cable"}, headers=headers_b)

    assert search.status_code == 200
    assert any(e["name"] == "Cable Row" for e in search.json())
```

- [ ] **Step 2: Run to verify failure**

```bash
cd backend && pytest tests/test_workouts_router.py -v
```
Expected: FAIL — `/workouts/exercises` doesn't exist (404).

- [ ] **Step 3: Implement**

`backend/app/workouts/__init__.py`: (empty file)

`backend/app/workouts/models.py`:
```python
from typing import Optional

from pydantic import BaseModel


class ExerciseCreate(BaseModel):
    name: str
    category: str
    is_bodyweight: bool = False


class ExerciseOut(ExerciseCreate):
    id: str
    created_by_user_id: Optional[str] = None
```

`backend/app/workouts/router.py`:
```python
from fastapi import APIRouter, Depends, status

from ..deps import get_current_user_id, get_exercise_repo
from .models import ExerciseCreate, ExerciseOut

router = APIRouter()


@router.get("/exercises", response_model=list[ExerciseOut])
async def search_exercises(
    q: str,
    user_id: str = Depends(get_current_user_id),
    exercise_repo=Depends(get_exercise_repo),
):
    return await exercise_repo.search(q)


@router.post("/exercises", response_model=ExerciseOut, status_code=status.HTTP_201_CREATED)
async def create_exercise(
    body: ExerciseCreate,
    user_id: str = Depends(get_current_user_id),
    exercise_repo=Depends(get_exercise_repo),
):
    return await exercise_repo.create({**body.model_dump(), "created_by_user_id": user_id})
```

In `backend/app/main.py`, add `from .workouts.router import router as workouts_router` alongside the existing `from .meals.router import router as meals_router` line, and add `app.include_router(workouts_router, prefix="/workouts", tags=["workouts"])` right after the existing `app.include_router(meals_router, prefix="/meals", tags=["meals"])` line.

- [ ] **Step 4: Run to verify pass**

```bash
cd backend && pytest tests/test_workouts_router.py -v
```
Expected: `3 passed`.

- [ ] **Step 5: Commit**

```bash
git add backend/app/workouts backend/app/main.py backend/tests/test_workouts_router.py
git commit -m "$(cat <<'EOF'
Add exercise library search and custom-exercise creation endpoints

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: Workout CRUD endpoints with type-specific validation and ownership checks

**Files:**
- Modify: `backend/app/workouts/models.py`, `backend/app/workouts/router.py`, `backend/tests/test_workouts_router.py`

**Interfaces:**
- Consumes: `get_current_user_id`, `get_workout_repo` (Task 1); `ExerciseCreate`, `ExerciseOut` (Task 2, unchanged).
- Produces: `GET/POST /workouts`, `PATCH/DELETE /workouts/{id}`; `WorkoutType`, `WorkoutCreate`, `WorkoutUpdate`, `WorkoutOut` models, consumed by the client tasks (Task 5).

- [ ] **Step 1: Write the failing tests**

Append to `backend/tests/test_workouts_router.py`:
```python
STRENGTH_PAYLOAD = {
    "type": "strength",
    "started_at": "2026-09-16T07:00:00Z",
    "duration_s": 3600,
    "exercises": [
        {"exercise_id": "bench-press", "sets": [{"reps": 8, "weight_kg": 60}, {"reps": 6, "weight_kg": 65}]}
    ],
}

CARDIO_PAYLOAD = {
    "type": "running",
    "started_at": "2026-09-16T06:00:00Z",
    "duration_s": 1800,
    "distance_m": 5000,
    "avg_pace_s_per_km": 360,
}


def test_create_and_list_strength_workout(client, auth_headers):
    headers = auth_headers()

    create = client.post("/workouts", json=STRENGTH_PAYLOAD, headers=headers)
    assert create.status_code == 201
    assert create.json()["source"] == "manual"

    listing = client.get("/workouts", headers=headers)
    assert listing.status_code == 200
    assert len(listing.json()) == 1
    assert listing.json()[0]["exercises"][0]["exercise_id"] == "bench-press"


def test_create_and_list_cardio_workout(client, auth_headers):
    headers = auth_headers()

    create = client.post("/workouts", json=CARDIO_PAYLOAD, headers=headers)
    assert create.status_code == 201

    listing = client.get("/workouts", params={"type": "running"}, headers=headers)
    assert listing.status_code == 200
    assert listing.json()[0]["distance_m"] == 5000


def test_list_workouts_with_invalid_type_returns_422(client, auth_headers):
    headers = auth_headers()

    response = client.get("/workouts", params={"type": "swimming"}, headers=headers)

    assert response.status_code == 422


def test_strength_workout_without_exercises_is_rejected(client, auth_headers):
    headers = auth_headers()
    payload = {**STRENGTH_PAYLOAD, "exercises": []}

    response = client.post("/workouts", json=payload, headers=headers)

    assert response.status_code == 422


def test_cardio_workout_without_distance_is_rejected(client, auth_headers):
    headers = auth_headers()
    payload = {k: v for k, v in CARDIO_PAYLOAD.items() if k != "distance_m"}

    response = client.post("/workouts", json=payload, headers=headers)

    assert response.status_code == 422


def test_workout_with_negative_values_is_rejected(client, auth_headers):
    headers = auth_headers()
    negative_duration = {**CARDIO_PAYLOAD, "duration_s": -100}
    negative_reps = {
        **STRENGTH_PAYLOAD,
        "exercises": [{"exercise_id": "bench-press", "sets": [{"reps": -1}]}],
    }

    assert client.post("/workouts", json=negative_duration, headers=headers).status_code == 422
    assert client.post("/workouts", json=negative_reps, headers=headers).status_code == 422


def test_update_and_delete_own_workout(client, auth_headers):
    headers = auth_headers()
    workout_id = client.post("/workouts", json=CARDIO_PAYLOAD, headers=headers).json()["id"]

    update = client.patch(f"/workouts/{workout_id}", json={"duration_s": 1700}, headers=headers)
    assert update.status_code == 200
    assert update.json()["duration_s"] == 1700

    delete = client.delete(f"/workouts/{workout_id}", headers=headers)
    assert delete.status_code == 204

    listing = client.get("/workouts", headers=headers)
    assert listing.json() == []


def test_user_cannot_read_or_modify_another_users_workout(client, auth_headers):
    headers_a = auth_headers(email="owner3@example.com")
    headers_b = auth_headers(email="intruder3@example.com")
    workout_id = client.post("/workouts", json=CARDIO_PAYLOAD, headers=headers_a).json()["id"]

    update = client.patch(f"/workouts/{workout_id}", json={"duration_s": 1}, headers=headers_b)
    assert update.status_code == 404

    delete = client.delete(f"/workouts/{workout_id}", headers=headers_b)
    assert delete.status_code == 404

    listing = client.get("/workouts", headers=headers_b)
    assert listing.json() == []


def test_workouts_require_auth(client):
    response = client.get("/workouts")

    assert response.status_code == 403
```

- [ ] **Step 2: Run to verify failure**

```bash
cd backend && pytest tests/test_workouts_router.py -v
```
Expected: FAIL — `/workouts` (list/create/update/delete) doesn't exist yet.

- [ ] **Step 3: Implement**

Replace `backend/app/workouts/models.py` with:
```python
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, field_validator, model_validator


class ExerciseCreate(BaseModel):
    name: str
    category: str
    is_bodyweight: bool = False


class ExerciseOut(ExerciseCreate):
    id: str
    created_by_user_id: Optional[str] = None


WorkoutType = Literal["strength", "calisthenics", "running", "cycling"]
WorkoutSource = Literal["manual"]

STRENGTH_TYPES = {"strength", "calisthenics"}
CARDIO_TYPES = {"running", "cycling"}


class ExerciseSet(BaseModel):
    reps: int
    weight_kg: Optional[float] = None
    bodyweight: Optional[bool] = None

    @field_validator("reps")
    @classmethod
    def reps_must_be_positive(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("reps must be greater than 0")
        return value

    @field_validator("weight_kg")
    @classmethod
    def weight_must_be_non_negative(cls, value: Optional[float]) -> Optional[float]:
        if value is not None and value < 0:
            raise ValueError("weight_kg must not be negative")
        return value


class WorkoutExercise(BaseModel):
    exercise_id: str
    sets: list[ExerciseSet]


class WorkoutCreate(BaseModel):
    type: WorkoutType
    started_at: datetime
    duration_s: int
    exercises: Optional[list[WorkoutExercise]] = None
    distance_m: Optional[float] = None
    avg_pace_s_per_km: Optional[float] = None
    elevation_gain_m: Optional[float] = None

    @field_validator("duration_s")
    @classmethod
    def duration_must_be_positive(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("duration_s must be greater than 0")
        return value

    @field_validator("distance_m")
    @classmethod
    def distance_must_be_positive(cls, value: Optional[float]) -> Optional[float]:
        if value is not None and value <= 0:
            raise ValueError("distance_m must be greater than 0")
        return value

    @model_validator(mode="after")
    def check_type_specific_fields(self) -> "WorkoutCreate":
        if self.type in STRENGTH_TYPES and not self.exercises:
            raise ValueError(f"{self.type} workouts require at least one exercise")
        if self.type in CARDIO_TYPES and self.distance_m is None:
            raise ValueError(f"{self.type} workouts require distance_m")
        return self


class WorkoutUpdate(BaseModel):
    # Deliberately narrower than WorkoutCreate: exercises/distance_m/type are
    # not editable here, so an update can never violate the type-specific
    # invariants enforced above (e.g. clearing a strength workout's exercises)
    # after the workout has already been validated once at creation.
    duration_s: Optional[int] = None
    avg_pace_s_per_km: Optional[float] = None
    elevation_gain_m: Optional[float] = None

    @field_validator("duration_s")
    @classmethod
    def duration_must_be_positive(cls, value: Optional[int]) -> Optional[int]:
        if value is not None and value <= 0:
            raise ValueError("duration_s must be greater than 0")
        return value


class WorkoutOut(WorkoutCreate):
    id: str
    user_id: str
    source: WorkoutSource  # always "manual" in v1; server-assigned, never client input
    created_at: str
    updated_at: str
```

Replace `backend/app/workouts/router.py` with:
```python
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status

from ..deps import get_current_user_id, get_exercise_repo, get_workout_repo
from .models import (
    ExerciseCreate,
    ExerciseOut,
    WorkoutCreate,
    WorkoutOut,
    WorkoutType,
    WorkoutUpdate,
)

router = APIRouter()


@router.get("/exercises", response_model=list[ExerciseOut])
async def search_exercises(
    q: str,
    user_id: str = Depends(get_current_user_id),
    exercise_repo=Depends(get_exercise_repo),
):
    return await exercise_repo.search(q)


@router.post("/exercises", response_model=ExerciseOut, status_code=status.HTTP_201_CREATED)
async def create_exercise(
    body: ExerciseCreate,
    user_id: str = Depends(get_current_user_id),
    exercise_repo=Depends(get_exercise_repo),
):
    return await exercise_repo.create({**body.model_dump(), "created_by_user_id": user_id})


@router.get("", response_model=list[WorkoutOut])
async def list_workouts(
    type: Optional[WorkoutType] = None,
    user_id: str = Depends(get_current_user_id),
    workout_repo=Depends(get_workout_repo),
):
    return await workout_repo.list_for_user(user_id, workout_type=type)


@router.post("", response_model=WorkoutOut, status_code=status.HTTP_201_CREATED)
async def create_workout(
    body: WorkoutCreate,
    user_id: str = Depends(get_current_user_id),
    workout_repo=Depends(get_workout_repo),
):
    return await workout_repo.create(
        {**body.model_dump(mode="json"), "user_id": user_id, "source": "manual"}
    )


@router.patch("/{workout_id}", response_model=WorkoutOut)
async def update_workout(
    workout_id: str,
    body: WorkoutUpdate,
    user_id: str = Depends(get_current_user_id),
    workout_repo=Depends(get_workout_repo),
):
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    updated = await workout_repo.update(user_id, workout_id, updates)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="workout not found")
    return updated


@router.delete("/{workout_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workout(
    workout_id: str,
    user_id: str = Depends(get_current_user_id),
    workout_repo=Depends(get_workout_repo),
):
    if not await workout_repo.delete(user_id, workout_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="workout not found")
```

- [ ] **Step 4: Run to verify pass**

```bash
cd backend && pytest tests/test_workouts_router.py -v
```
Expected: `12 passed`.

- [ ] **Step 5: Commit**

```bash
git add backend/app/workouts backend/tests/test_workouts_router.py
git commit -m "$(cat <<'EOF'
Add workout CRUD endpoints with type-specific validation and ownership checks

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: Cosmos DB repositories for workouts and exercises

**Files:**
- Modify: `backend/app/db/cosmos.py`, `backend/app/deps.py`, `backend/tests/test_cosmos_repos.py`

**Interfaces:**
- Consumes: `settings` (existing); implements `WorkoutRepository`/`ExerciseRepository` Protocols (Task 1).
- Produces: `CosmosWorkoutRepository`, `CosmosExerciseRepository` from `app.db.cosmos`.

- [ ] **Step 1: Write the failing tests**

Replace the `from app.db.cosmos import ...` line at the top of `backend/tests/test_cosmos_repos.py` with:
```python
from app.db.cosmos import (
    CosmosExerciseRepository,
    CosmosFoodRepository,
    CosmosMealEntryRepository,
    CosmosUserRepository,
    CosmosWorkoutRepository,
)
```

Append to `backend/tests/test_cosmos_repos.py`:
```python
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
```

- [ ] **Step 2: Run to verify failure**

```bash
cd backend && pytest tests/test_cosmos_repos.py -v
```
Expected: FAIL — `ImportError: cannot import name 'CosmosWorkoutRepository'`.

- [ ] **Step 3: Implement**

In `backend/app/db/cosmos.py`, update `init_cosmos` to also create the new containers:
```python
async def init_cosmos(client: CosmosClient, database_name: str) -> None:
    database = await client.create_database_if_not_exists(database_name)
    await database.create_container_if_not_exists(id="users", partition_key=PartitionKey(path="/id"))
    await database.create_container_if_not_exists(
        id="meal_entries", partition_key=PartitionKey(path="/user_id")
    )
    await database.create_container_if_not_exists(id="foods", partition_key=PartitionKey(path="/id"))
    await database.create_container_if_not_exists(
        id="workouts", partition_key=PartitionKey(path="/user_id")
    )
    await database.create_container_if_not_exists(id="exercises", partition_key=PartitionKey(path="/id"))
```

Append to `backend/app/db/cosmos.py`:
```python
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
```

In `backend/app/deps.py`, add `CosmosExerciseRepository, CosmosWorkoutRepository` to the existing `from .db.cosmos import (...)` line, then replace the `get_workout_repo` / `get_exercise_repo` functions with:
```python
def get_workout_repo():
    if settings.db_backend == "cosmos":
        return CosmosWorkoutRepository(get_cosmos_client(), settings.cosmos_database_name)
    return _memory_workout_repo


def get_exercise_repo():
    if settings.db_backend == "cosmos":
        return CosmosExerciseRepository(get_cosmos_client(), settings.cosmos_database_name)
    return _exercise_repo
```

- [ ] **Step 4: Run to verify pass**

```bash
cd backend && pytest tests/ -v
```
Expected: all tests pass. `db_backend` defaults to `"memory"`, so the full suite still runs with zero Azure connectivity.

- [ ] **Step 5: Commit**

```bash
git add backend/app/db/cosmos.py backend/app/deps.py backend/tests/test_cosmos_repos.py
git commit -m "$(cat <<'EOF'
Add Cosmos DB repositories for workouts and exercises

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 5: Client API bindings and types

**Files:**
- Create: `src/modules/training_tracker/types.ts`, `src/modules/training_tracker/api.ts`

**Interfaces:**
- Consumes: `apiFetch` (`src/lib/api-client.ts`, existing).
- Produces: `WorkoutType`, `Workout`, `WorkoutInput`, `WorkoutUpdateInput`, `Exercise`, `ExerciseInput` types; `listWorkouts(type?)`, `createWorkout(workout)`, `updateWorkout(id, updates)`, `deleteWorkout(id)`, `searchExercises(query)`, `createExercise(exercise)` — used by Task 6.

- [ ] **Step 1: Define the shared types**

`src/modules/training_tracker/types.ts`:
```typescript
export type WorkoutType = "strength" | "calisthenics" | "running" | "cycling";
export type WorkoutSource = "manual";

export type ExerciseSet = {
  reps: number;
  weight_kg?: number;
  bodyweight?: boolean;
};

export type WorkoutExercise = {
  exercise_id: string;
  sets: ExerciseSet[];
};

export type Workout = {
  id: string;
  user_id: string;
  type: WorkoutType;
  source: WorkoutSource;
  started_at: string;
  duration_s: number;
  exercises?: WorkoutExercise[];
  distance_m?: number;
  avg_pace_s_per_km?: number;
  elevation_gain_m?: number;
  created_at: string;
  updated_at: string;
};

export type WorkoutInput = {
  type: WorkoutType;
  started_at: string;
  duration_s: number;
  exercises?: WorkoutExercise[];
  distance_m?: number;
  avg_pace_s_per_km?: number;
  elevation_gain_m?: number;
};

export type WorkoutUpdateInput = {
  duration_s?: number;
  avg_pace_s_per_km?: number;
  elevation_gain_m?: number;
};

export type Exercise = {
  id: string;
  name: string;
  category: string;
  is_bodyweight: boolean;
  created_by_user_id?: string | null;
};

export type ExerciseInput = {
  name: string;
  category: string;
  is_bodyweight: boolean;
};
```

- [ ] **Step 2: Implement the API bindings**

`src/modules/training_tracker/api.ts`:
```typescript
import { apiFetch } from "@/lib/api-client";

import type {
  Exercise,
  ExerciseInput,
  Workout,
  WorkoutInput,
  WorkoutType,
  WorkoutUpdateInput,
} from "./types";

export function listWorkouts(type?: WorkoutType): Promise<Workout[]> {
  const query = type ? `?type=${encodeURIComponent(type)}` : "";
  return apiFetch<Workout[]>(`/workouts${query}`);
}

export function createWorkout(workout: WorkoutInput): Promise<Workout> {
  return apiFetch<Workout>("/workouts", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(workout),
  });
}

export function updateWorkout(id: string, updates: WorkoutUpdateInput): Promise<Workout> {
  return apiFetch<Workout>(`/workouts/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(updates),
  });
}

export function deleteWorkout(id: string): Promise<void> {
  return apiFetch<void>(`/workouts/${id}`, { method: "DELETE" });
}

export function searchExercises(query: string): Promise<Exercise[]> {
  return apiFetch<Exercise[]>(`/workouts/exercises?q=${encodeURIComponent(query)}`);
}

export function createExercise(exercise: ExerciseInput): Promise<Exercise> {
  return apiFetch<Exercise>("/workouts/exercises", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(exercise),
  });
}
```

- [ ] **Step 3: Verify it compiles**

```bash
npx tsc --noEmit
```
Expected: no errors.

- [ ] **Step 4: Commit**

```bash
git add src/modules/training_tracker/types.ts src/modules/training_tracker/api.ts
git commit -m "$(cat <<'EOF'
Add training tracker API bindings and shared types

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 6: Training tracker screens (history, log-strength, log-cardio, exercise library)

**Files:**
- Create: `src/app/training-tracker/_layout.tsx`, `src/app/training-tracker/index.tsx`, `src/app/training-tracker/log-strength.tsx`, `src/app/training-tracker/log-cardio.tsx`, `src/app/training-tracker/exercise-library.tsx`

**Interfaces:**
- Consumes: `listWorkouts`, `createWorkout`, `deleteWorkout`, `searchExercises`, `createExercise` (Task 5); `Workout`, `WorkoutExercise`, `ExerciseSet`, `Exercise`, `WorkoutType` types (Task 5).
- Produces: the `/training-tracker` route tree, linked from the home hub (Task 7).

- [ ] **Step 1: Create the stack layout**

`src/app/training-tracker/_layout.tsx`:
```tsx
import { Stack } from "expo-router";

export default function TrainingTrackerLayout() {
  return (
    <Stack>
      <Stack.Screen name="index" options={{ title: "Training Tracker" }} />
      <Stack.Screen name="log-strength" options={{ title: "Log Strength" }} />
      <Stack.Screen name="log-cardio" options={{ title: "Log Cardio" }} />
      <Stack.Screen name="exercise-library" options={{ title: "Exercise Library" }} />
    </Stack>
  );
}
```

- [ ] **Step 2: Create the history (home) screen**

`src/app/training-tracker/index.tsx`:
```tsx
import { useFocusEffect, useRouter, type Href } from "expo-router";
import { useCallback, useState } from "react";
import { Button, FlatList, SafeAreaView, Text, View } from "react-native";

import { deleteWorkout, listWorkouts } from "@/modules/training_tracker/api";
import type { Workout } from "@/modules/training_tracker/types";

function summarize(workout: Workout): string {
  if (workout.type === "strength" || workout.type === "calisthenics") {
    const setCount = workout.exercises?.reduce((sum, e) => sum + e.sets.length, 0) ?? 0;
    return `${workout.type}: ${workout.exercises?.length ?? 0} exercises, ${setCount} sets`;
  }
  const km = workout.distance_m ? (workout.distance_m / 1000).toFixed(1) : "?";
  return `${workout.type}: ${km} km`;
}

export default function TrainingTrackerRoute() {
  const router = useRouter();
  const [workouts, setWorkouts] = useState<Workout[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setIsLoading(true);
    try {
      setWorkouts(await listWorkouts());
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "failed to load workouts");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useFocusEffect(
    useCallback(() => {
      load();
    }, [load])
  );

  return (
    <SafeAreaView style={{ flex: 1, padding: 16, gap: 12 }}>
      <Text style={{ fontSize: 20, fontWeight: "600" }}>Training History</Text>

      {error ? <Text style={{ color: "red" }}>{error}</Text> : null}

      <FlatList
        data={workouts}
        keyExtractor={(item) => item.id}
        refreshing={isLoading}
        onRefresh={load}
        ListEmptyComponent={<Text>No workouts logged yet.</Text>}
        renderItem={({ item }) => (
          <View style={{ flexDirection: "row", justifyContent: "space-between", paddingVertical: 8 }}>
            <Text>{summarize(item)}</Text>
            <Button
              title="Delete"
              onPress={async () => {
                try {
                  await deleteWorkout(item.id);
                  setError(null);
                  load();
                } catch (err) {
                  setError(err instanceof Error ? err.message : "failed to delete workout");
                }
              }}
            />
          </View>
        )}
      />

      <View style={{ flexDirection: "row", gap: 8 }}>
        <Button title="Log Strength" onPress={() => router.push("/training-tracker/log-strength" as Href)} />
        <Button title="Log Cardio" onPress={() => router.push("/training-tracker/log-cardio" as Href)} />
      </View>
      <Button
        title="Exercise Library"
        onPress={() => router.push("/training-tracker/exercise-library" as Href)}
      />
    </SafeAreaView>
  );
}
```

- [ ] **Step 3: Create the log-strength screen**

`src/app/training-tracker/log-strength.tsx`:
```tsx
import { useRouter } from "expo-router";
import { useState } from "react";
import { Button, FlatList, SafeAreaView, Text, TextInput, View } from "react-native";

import { createWorkout, searchExercises } from "@/modules/training_tracker/api";
import type { Exercise, ExerciseSet, WorkoutType } from "@/modules/training_tracker/types";

const STRENGTH_TYPES: WorkoutType[] = ["strength", "calisthenics"];

type DraftExercise = {
  exercise: Exercise;
  sets: ExerciseSet[];
};

export default function LogStrengthScreen() {
  const router = useRouter();
  const [workoutType, setWorkoutType] = useState<WorkoutType>("strength");
  const [durationMinutes, setDurationMinutes] = useState("");
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<Exercise[]>([]);
  const [draftExercises, setDraftExercises] = useState<DraftExercise[]>([]);
  const [error, setError] = useState<string | null>(null);

  const onSearch = async (text: string) => {
    setQuery(text);
    try {
      setResults(text.length >= 2 ? await searchExercises(text) : []);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "search failed");
    }
  };

  const addExercise = (exercise: Exercise) => {
    setDraftExercises((prev) => [...prev, { exercise, sets: [{ reps: 10 }] }]);
    setQuery("");
    setResults([]);
  };

  const addSet = (index: number) => {
    setDraftExercises((prev) =>
      prev.map((d, i) => (i === index ? { ...d, sets: [...d.sets, { reps: 10 }] } : d))
    );
  };

  const updateSet = (exerciseIndex: number, setIndex: number, reps: number, weightKg?: number) => {
    setDraftExercises((prev) =>
      prev.map((d, i) =>
        i === exerciseIndex
          ? { ...d, sets: d.sets.map((s, si) => (si === setIndex ? { reps, weight_kg: weightKg } : s)) }
          : d
      )
    );
  };

  const save = async () => {
    const duration_s = Math.round(Number(durationMinutes) * 60);
    if (!Number.isFinite(duration_s) || duration_s <= 0 || draftExercises.length === 0) {
      setError("enter a duration and at least one exercise");
      return;
    }
    try {
      await createWorkout({
        type: workoutType,
        started_at: new Date().toISOString(),
        duration_s,
        exercises: draftExercises.map((d) => ({ exercise_id: d.exercise.id, sets: d.sets })),
      });
      router.back();
    } catch (err) {
      setError(err instanceof Error ? err.message : "failed to save workout");
    }
  };

  return (
    <SafeAreaView style={{ flex: 1, padding: 16, gap: 12 }}>
      {error ? <Text style={{ color: "red" }}>{error}</Text> : null}

      <View style={{ flexDirection: "row", gap: 8 }}>
        {STRENGTH_TYPES.map((t) => (
          <Button
            key={t}
            title={t}
            color={t === workoutType ? "#208AEF" : undefined}
            onPress={() => setWorkoutType(t)}
          />
        ))}
      </View>

      <TextInput
        placeholder="Duration (minutes)"
        keyboardType="numeric"
        value={durationMinutes}
        onChangeText={setDurationMinutes}
        style={{ borderWidth: 1, padding: 12, borderRadius: 8 }}
      />

      <TextInput
        placeholder="Search exercises"
        value={query}
        onChangeText={onSearch}
        style={{ borderWidth: 1, padding: 12, borderRadius: 8 }}
      />
      <FlatList
        data={results}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => <Button title={item.name} onPress={() => addExercise(item)} />}
      />

      <FlatList
        data={draftExercises}
        keyExtractor={(_, index) => String(index)}
        renderItem={({ item, index }) => (
          <View style={{ paddingVertical: 8 }}>
            <Text style={{ fontWeight: "600" }}>{item.exercise.name}</Text>
            {item.sets.map((set, setIndex) => (
              <View key={setIndex} style={{ flexDirection: "row", gap: 8, alignItems: "center" }}>
                <TextInput
                  placeholder="reps"
                  keyboardType="numeric"
                  value={String(set.reps)}
                  onChangeText={(text) => updateSet(index, setIndex, Number(text) || 0, set.weight_kg)}
                  style={{ borderWidth: 1, padding: 8, borderRadius: 8, width: 60 }}
                />
                <TextInput
                  placeholder="kg"
                  keyboardType="numeric"
                  value={set.weight_kg !== undefined ? String(set.weight_kg) : ""}
                  onChangeText={(text) => updateSet(index, setIndex, set.reps, text ? Number(text) : undefined)}
                  style={{ borderWidth: 1, padding: 8, borderRadius: 8, width: 60 }}
                />
              </View>
            ))}
            <Button title="Add Set" onPress={() => addSet(index)} />
          </View>
        )}
      />

      <Button title="Save Workout" onPress={save} />
    </SafeAreaView>
  );
}
```

- [ ] **Step 4: Create the log-cardio screen**

`src/app/training-tracker/log-cardio.tsx`:
```tsx
import { useRouter } from "expo-router";
import { useState } from "react";
import { Button, SafeAreaView, Text, TextInput, View } from "react-native";

import { createWorkout } from "@/modules/training_tracker/api";
import type { WorkoutType } from "@/modules/training_tracker/types";

const CARDIO_TYPES: WorkoutType[] = ["running", "cycling"];

export default function LogCardioScreen() {
  const router = useRouter();
  const [workoutType, setWorkoutType] = useState<WorkoutType>("running");
  const [durationMinutes, setDurationMinutes] = useState("");
  const [distanceKm, setDistanceKm] = useState("");
  const [elevationM, setElevationM] = useState("");
  const [error, setError] = useState<string | null>(null);

  const save = async () => {
    const duration_s = Math.round(Number(durationMinutes) * 60);
    const distance_m = Number(distanceKm) * 1000;
    if (!Number.isFinite(duration_s) || duration_s <= 0 || !Number.isFinite(distance_m) || distance_m <= 0) {
      setError("enter a valid duration and distance");
      return;
    }
    try {
      await createWorkout({
        type: workoutType,
        started_at: new Date().toISOString(),
        duration_s,
        distance_m,
        avg_pace_s_per_km: Math.round(duration_s / (distance_m / 1000)),
        elevation_gain_m: elevationM ? Number(elevationM) : undefined,
      });
      router.back();
    } catch (err) {
      setError(err instanceof Error ? err.message : "failed to save workout");
    }
  };

  return (
    <SafeAreaView style={{ flex: 1, padding: 16, gap: 12 }}>
      {error ? <Text style={{ color: "red" }}>{error}</Text> : null}

      <View style={{ flexDirection: "row", gap: 8 }}>
        {CARDIO_TYPES.map((t) => (
          <Button
            key={t}
            title={t}
            color={t === workoutType ? "#208AEF" : undefined}
            onPress={() => setWorkoutType(t)}
          />
        ))}
      </View>

      <TextInput
        placeholder="Duration (minutes)"
        keyboardType="numeric"
        value={durationMinutes}
        onChangeText={setDurationMinutes}
        style={{ borderWidth: 1, padding: 12, borderRadius: 8 }}
      />
      <TextInput
        placeholder="Distance (km)"
        keyboardType="numeric"
        value={distanceKm}
        onChangeText={setDistanceKm}
        style={{ borderWidth: 1, padding: 12, borderRadius: 8 }}
      />
      <TextInput
        placeholder="Elevation gain (m, optional)"
        keyboardType="numeric"
        value={elevationM}
        onChangeText={setElevationM}
        style={{ borderWidth: 1, padding: 12, borderRadius: 8 }}
      />

      <Button title="Save Workout" onPress={save} />
    </SafeAreaView>
  );
}
```

- [ ] **Step 5: Create the exercise library screen**

`src/app/training-tracker/exercise-library.tsx`:
```tsx
import { useState } from "react";
import { Button, FlatList, SafeAreaView, Text, TextInput } from "react-native";

import { createExercise, searchExercises } from "@/modules/training_tracker/api";
import type { Exercise } from "@/modules/training_tracker/types";

export default function ExerciseLibraryScreen() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<Exercise[]>([]);
  const [newName, setNewName] = useState("");
  const [newCategory, setNewCategory] = useState("");
  const [error, setError] = useState<string | null>(null);

  const onSearch = async (text: string) => {
    setQuery(text);
    try {
      setResults(text.length >= 2 ? await searchExercises(text) : []);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "search failed");
    }
  };

  const addCustomExercise = async () => {
    if (!newName.trim() || !newCategory.trim()) return;
    try {
      await createExercise({ name: newName.trim(), category: newCategory.trim(), is_bodyweight: false });
      setNewName("");
      setNewCategory("");
      await onSearch(query);
    } catch (err) {
      setError(err instanceof Error ? err.message : "failed to add exercise");
    }
  };

  return (
    <SafeAreaView style={{ flex: 1, padding: 16, gap: 12 }}>
      {error ? <Text style={{ color: "red" }}>{error}</Text> : null}

      <TextInput
        placeholder="Search exercises"
        value={query}
        onChangeText={onSearch}
        style={{ borderWidth: 1, padding: 12, borderRadius: 8 }}
      />
      <FlatList
        data={results}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => (
          <Text style={{ paddingVertical: 8 }}>
            {item.name} · {item.category}
            {item.is_bodyweight ? " · bodyweight" : ""}
          </Text>
        )}
      />

      <Text style={{ fontWeight: "600" }}>Add a custom exercise</Text>
      <TextInput
        placeholder="Name"
        value={newName}
        onChangeText={setNewName}
        style={{ borderWidth: 1, padding: 12, borderRadius: 8 }}
      />
      <TextInput
        placeholder="Category (e.g. chest, back, legs)"
        value={newCategory}
        onChangeText={setNewCategory}
        style={{ borderWidth: 1, padding: 12, borderRadius: 8 }}
      />
      <Button title="Add Exercise" onPress={addCustomExercise} />
    </SafeAreaView>
  );
}
```

- [ ] **Step 6: Manual verification**

```bash
cd backend && uvicorn app.main:app --reload &
npx expo start
```
Log in, navigate to `/training-tracker`, confirm the history screen shows "No workouts logged yet." Tap "Log Cardio", enter a duration and distance, save, confirm it appears in history with the correct km. Tap "Log Strength", search for "bench", add it, add a set with reps/weight, save, confirm it appears in history. Open "Exercise Library", confirm search works and a custom exercise can be added. Delete a workout from history and confirm it disappears.

- [ ] **Step 7: Commit**

```bash
git add src/app/training-tracker
git commit -m "$(cat <<'EOF'
Add training tracker screens: history, log-strength, log-cardio, exercise library

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 7: Home screen becomes a module hub

**Files:**
- Modify: `src/app/index.tsx`

**Interfaces:**
- Consumes: `useAuth` (`src/lib/auth-context.tsx`, existing).
- Produces: the `/` route now links to `/meal-tracker` and `/training-tracker` instead of auto-redirecting to meal-tracker, per the platform spec's "Home dashboard becomes a hub" note.

- [ ] **Step 1: Replace the redirect-only home screen with a hub**

`src/app/index.tsx`:
```tsx
import { Redirect, useRouter, type Href } from "expo-router";
import { Button, SafeAreaView, Text } from "react-native";

import { useAuth } from "@/lib/auth-context";

export default function Home() {
  const router = useRouter();
  const { user, isLoading, logout } = useAuth();

  if (isLoading) {
    return null;
  }

  if (!user) {
    return <Redirect href={"/login" as Href} />;
  }

  return (
    <SafeAreaView style={{ flex: 1, padding: 16, gap: 12 }}>
      <Text style={{ fontSize: 20, fontWeight: "600" }}>Health App</Text>
      <Button title="Meal Tracker" onPress={() => router.push("/meal-tracker" as Href)} />
      <Button title="Training Tracker" onPress={() => router.push("/training-tracker" as Href)} />
      <Button title="Log Out" onPress={logout} />
    </SafeAreaView>
  );
}
```

- [ ] **Step 2: Manual verification**

```bash
npx expo start
```
Log in, confirm you land on the hub screen (not an auto-redirect), see "Health App" with three buttons. Tap "Meal Tracker" and confirm it navigates there and back works. Tap "Training Tracker" and confirm the same. Tap "Log Out" and confirm you're returned to the login screen.

- [ ] **Step 3: Commit**

```bash
git add src/app/index.tsx
git commit -m "$(cat <<'EOF'
Turn the home screen into a hub linking to meal and training trackers

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```
