# Platform Shell + Meal & Calorie Tracker Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stand up the shared backend/auth platform and ship a working Meal & Calorie Tracker (Yazio-style diary, food search, quick-add, and photo-AI estimation) as the first marketable module.

**Architecture:** A FastAPI backend (containerized for Azure Container Apps) backed by a repository-interface layer with in-memory implementations for dev/tests and Cosmos DB implementations for production, issuing its own JWTs for both password and OAuth sign-in. The Expo client extends the existing `calorie_camera` stub into a full `meal-tracker` module, talking to the backend through a shared token-refreshing API client.

**Tech Stack:** Python 3.12 / FastAPI / Pydantic v2 / PyJWT / bcrypt / azure-cosmos / anthropic SDK / pytest+pytest-asyncio (backend). Expo Router / React 19 / TypeScript / expo-secure-store / expo-image-picker (client).

**Spec:**
- `docs/superpowers/specs/2026-09-16-platform-architecture-design.md`
- `docs/superpowers/specs/2026-09-16-meal-tracker-design.md`

## Global Constraints

- Every timestamp is stored and transmitted as an ISO 8601 UTC string.
- Per-user Cosmos containers are partitioned on `/user_id`; the `users` container is partitioned on `/id` (it has no separate owner).
- The client never talks to Cosmos DB directly — every read/write goes through the FastAPI backend.
- The backend issues its own access + refresh JWTs regardless of whether the user signed in with a password or via OAuth; the client only ever handles one token type.
- Per AGENTS.md, Expo has changed significantly — read https://docs.expo.dev/versions/v57.0.0/ before writing any Expo-specific or native-module code, don't rely on older training knowledge.
- Per the platform spec, there is no automated client test suite in this phase: logic-only frontend tasks are verified with `npx tsc --noEmit`; screen tasks are verified by running the app and manually exercising the flow.
- Deferred out of this plan (tracked in the meal-tracker spec's "open assumptions," not silently dropped): barcode scanning, custom user-created foods/recipes, live Open Food Facts lookups. The food search in this plan searches a small in-memory seed list only.

---

## File Structure

**Backend (new `backend/` directory at repo root):**
```
backend/
  requirements.txt
  pytest.ini
  Dockerfile
  .env.example
  app/
    __init__.py
    main.py                  # FastAPI app, router registration, lifespan
    config.py                 # Settings (env-driven)
    security.py                # password hashing, JWT create/decode
    deps.py                     # get_user_repo, get_meal_entry_repo, get_food_repo, get_current_user_id
    db/
      __init__.py
      base.py                   # Repository Protocols
      memory.py                  # In-memory repos + seed foods (dev/test default)
      cosmos.py                   # Cosmos DB repos (prod)
    auth/
      __init__.py
      models.py                   # Request/response Pydantic models
      router.py                    # /auth routes
      oauth.py                      # OAuthVerifier + Google/Apple/Fake implementations
    meals/
      __init__.py
      models.py
      router.py                     # /meals routes
      nutrition_estimator.py         # NutritionEstimator + Claude/Fake implementations
  tests/
    conftest.py
    test_health.py
    test_security.py
    test_memory_repositories.py
    test_deps.py
    test_auth_router.py
    test_meals_router.py
    test_cosmos_repos.py
```

**Client (existing Expo app):**
```
src/lib/
  api-client.ts              # token storage + fetch wrapper with refresh-on-401
  auth-context.tsx            # AuthProvider / useAuth()
src/app/
  _layout.tsx                  # (modified) wraps Stack in AuthProvider
  index.tsx                     # (modified) redirect based on auth state
  (auth)/
    _layout.tsx
    login.tsx
    register.tsx
  meal-tracker/                 # renamed from calorie-ai-tools
    _layout.tsx
    index.tsx                    # diary (new home)
    add-entry.tsx
    camera.tsx
    confirm-estimate.tsx
src/modules/
  meal_tracker/                 # renamed from calorie_camera
    api.ts
    types.ts
    CalorieCamera.tsx
```

---

## Task 1: Backend scaffold + health check

**Files:**
- Create: `backend/requirements.txt`, `backend/pytest.ini`, `backend/app/__init__.py`, `backend/app/main.py`, `backend/tests/conftest.py`, `backend/tests/test_health.py`

**Interfaces:**
- Produces: FastAPI `app` object importable as `app.main.app`, used by every later task's tests and router registration.

- [ ] **Step 1: Create the backend project files**

`backend/requirements.txt`:
```
fastapi==0.115.0
uvicorn[standard]==0.32.0
pydantic==2.9.2
pydantic-settings==2.5.2
email-validator==2.2.0
bcrypt==4.2.0
PyJWT==2.9.0
cryptography==43.0.1
google-auth==2.35.0
azure-cosmos==4.7.0
anthropic==0.39.0
pytest==8.3.3
pytest-asyncio==0.24.0
httpx==0.27.2
```

`backend/pytest.ini`:
```ini
[pytest]
asyncio_mode = auto
```

`backend/app/__init__.py`: (empty file)

`backend/app/main.py`:
```python
from fastapi import FastAPI

app = FastAPI(title="Health App API")


@app.get("/health")
async def health():
    return {"status": "ok"}
```

`backend/tests/conftest.py`:
```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture()
def client():
    with TestClient(app) as test_client:
        yield test_client
```

`backend/tests/test_health.py`:
```python
def test_health_returns_ok(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

- [ ] **Step 2: Install dependencies and run the test**

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest tests/test_health.py -v
```
Expected: `1 passed`.

- [ ] **Step 3: Commit**

```bash
git add backend/requirements.txt backend/pytest.ini backend/app/__init__.py backend/app/main.py backend/tests/conftest.py backend/tests/test_health.py
git commit -m "$(cat <<'EOF'
Scaffold FastAPI backend with a health check endpoint

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: Password hashing and JWT utilities

**Files:**
- Create: `backend/app/security.py`, `backend/tests/test_security.py`

**Interfaces:**
- Produces: `hash_password(password: str) -> str`, `verify_password(password: str, password_hash: str) -> bool`, `create_token(user_id: str, secret: str, token_type: Literal["access","refresh"]) -> str`, `decode_token(token: str, secret: str, expected_type: Literal["access","refresh"]) -> str` (returns the user id, raises on invalid/expired/wrong-type token) — used by every task from Task 3 onward.

- [ ] **Step 1: Write the failing tests**

`backend/tests/test_security.py`:
```python
import pytest

from app.security import create_token, decode_token, hash_password, verify_password


def test_hash_password_and_verify_roundtrip():
    hashed = hash_password("correct horse battery staple")

    assert verify_password("correct horse battery staple", hashed)
    assert not verify_password("wrong password", hashed)


def test_create_and_decode_access_token_roundtrip():
    token = create_token("user-123", "test-secret", "access")

    assert decode_token(token, "test-secret", "access") == "user-123"


def test_decode_token_rejects_wrong_type():
    token = create_token("user-123", "test-secret", "refresh")

    with pytest.raises(Exception):
        decode_token(token, "test-secret", "access")


def test_decode_token_rejects_wrong_secret():
    token = create_token("user-123", "test-secret", "access")

    with pytest.raises(Exception):
        decode_token(token, "different-secret", "access")
```

- [ ] **Step 2: Run to verify failure**

```bash
cd backend && pytest tests/test_security.py -v
```
Expected: FAIL with `ModuleNotFoundError: No module named 'app.security'`.

- [ ] **Step 3: Implement**

`backend/app/security.py`:
```python
from datetime import datetime, timedelta, timezone
from typing import Literal

import bcrypt
import jwt

ACCESS_TOKEN_MINUTES = 15
REFRESH_TOKEN_DAYS = 30
ALGORITHM = "HS256"

TokenType = Literal["access", "refresh"]


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def create_token(user_id: str, secret: str, token_type: TokenType) -> str:
    now = datetime.now(timezone.utc)
    expires = now + (
        timedelta(minutes=ACCESS_TOKEN_MINUTES)
        if token_type == "access"
        else timedelta(days=REFRESH_TOKEN_DAYS)
    )
    payload = {"sub": user_id, "type": token_type, "iat": now, "exp": expires}
    return jwt.encode(payload, secret, algorithm=ALGORITHM)


def decode_token(token: str, secret: str, expected_type: TokenType) -> str:
    payload = jwt.decode(token, secret, algorithms=[ALGORITHM])
    if payload.get("type") != expected_type:
        raise ValueError(f"expected a {expected_type} token")
    return payload["sub"]
```

- [ ] **Step 4: Run to verify pass**

```bash
cd backend && pytest tests/test_security.py -v
```
Expected: `4 passed`.

- [ ] **Step 5: Commit**

```bash
git add backend/app/security.py backend/tests/test_security.py
git commit -m "$(cat <<'EOF'
Add password hashing and JWT create/decode utilities

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: Settings, repository interfaces, in-memory repos, and shared dependencies

**Files:**
- Create: `backend/app/config.py`, `backend/app/db/__init__.py`, `backend/app/db/base.py`, `backend/app/db/memory.py`, `backend/app/deps.py`, `backend/tests/test_memory_repositories.py`, `backend/tests/test_deps.py`

**Interfaces:**
- Consumes: `create_token`, `decode_token` from `app.security` (Task 2).
- Produces: `settings` (a `Settings` instance) from `app.config`; `UserRepository`/`MealEntryRepository`/`FoodRepository` Protocols and `InMemoryUserRepository`/`InMemoryMealEntryRepository`/`InMemoryFoodRepository`/`SEED_FOODS` from `app.db.memory`; `get_user_repo()`, `get_meal_entry_repo()`, `get_food_repo()`, `get_current_user_id(credentials) -> str` from `app.deps` — used by every router task from Task 4 onward.

- [ ] **Step 1: Write the failing tests**

`backend/tests/test_memory_repositories.py`:
```python
from datetime import date

from app.db.memory import (
    SEED_FOODS,
    InMemoryFoodRepository,
    InMemoryMealEntryRepository,
    InMemoryUserRepository,
)


async def test_user_repository_create_and_lookup():
    repo = InMemoryUserRepository()

    created = await repo.create({"email": "user@example.com", "password_hash": "hashed"})

    assert created["id"]
    assert await repo.get_by_id(created["id"]) == created
    assert await repo.get_by_email("user@example.com") == created
    assert await repo.get_by_email("missing@example.com") is None


async def test_meal_entry_repository_crud_scoped_by_user():
    repo = InMemoryMealEntryRepository()

    entry = await repo.create(
        {"user_id": "user-1", "logged_at": "2026-09-16T08:00:00+00:00", "calories": 300}
    )

    assert entry["id"]
    same_day = await repo.list_for_day("user-1", date(2026, 9, 16))
    assert [e["id"] for e in same_day] == [entry["id"]]
    assert await repo.list_for_day("user-2", date(2026, 9, 16)) == []

    updated = await repo.update("user-1", entry["id"], {"calories": 350})
    assert updated["calories"] == 350
    assert await repo.update("user-2", entry["id"], {"calories": 999}) is None

    assert await repo.delete("user-2", entry["id"]) is False
    assert await repo.delete("user-1", entry["id"]) is True
    assert await repo.get("user-1", entry["id"]) is None


async def test_food_repository_search_is_case_insensitive_substring_match():
    repo = InMemoryFoodRepository(SEED_FOODS)

    results = await repo.search("chick")

    assert any("Chicken" in food["name"] for food in results)
    assert await repo.search("nonexistent-food-xyz") == []
```

`backend/tests/test_deps.py`:
```python
import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.config import settings
from app.deps import get_current_user_id
from app.security import create_token


async def test_get_current_user_id_returns_subject_for_valid_token():
    token = create_token("user-123", settings.jwt_secret, "access")
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

    assert await get_current_user_id(credentials) == "user-123"


async def test_get_current_user_id_rejects_garbage_token():
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="garbage")

    with pytest.raises(HTTPException):
        await get_current_user_id(credentials)


async def test_get_current_user_id_rejects_refresh_token():
    token = create_token("user-123", settings.jwt_secret, "refresh")
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

    with pytest.raises(HTTPException):
        await get_current_user_id(credentials)
```

- [ ] **Step 2: Run to verify failure**

```bash
cd backend && pytest tests/test_memory_repositories.py tests/test_deps.py -v
```
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement**

`backend/app/config.py`:
```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    jwt_secret: str = "dev-secret-change-me"
    db_backend: str = "memory"  # "memory" or "cosmos"
    cosmos_connection_string: str | None = None
    cosmos_database_name: str = "health_app"
    google_oauth_client_id: str | None = None
    apple_oauth_bundle_id: str | None = None
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-sonnet-5"

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
```

`backend/app/db/__init__.py`: (empty file)

`backend/app/db/base.py`:
```python
from datetime import date
from typing import Optional, Protocol


class UserRepository(Protocol):
    async def get_by_email(self, email: str) -> Optional[dict]: ...
    async def get_by_id(self, user_id: str) -> Optional[dict]: ...
    async def create(self, user: dict) -> dict: ...


class MealEntryRepository(Protocol):
    async def create(self, entry: dict) -> dict: ...
    async def list_for_day(self, user_id: str, day: date) -> list[dict]: ...
    async def get(self, user_id: str, entry_id: str) -> Optional[dict]: ...
    async def update(self, user_id: str, entry_id: str, updates: dict) -> Optional[dict]: ...
    async def delete(self, user_id: str, entry_id: str) -> bool: ...


class FoodRepository(Protocol):
    async def search(self, query: str) -> list[dict]: ...
    async def get(self, food_id: str) -> Optional[dict]: ...
```

`backend/app/db/memory.py`:
```python
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
```

`backend/app/deps.py`:
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import settings
from .db.memory import (
    SEED_FOODS,
    InMemoryFoodRepository,
    InMemoryMealEntryRepository,
    InMemoryUserRepository,
)
from .security import decode_token

bearer_scheme = HTTPBearer()

_memory_user_repo = InMemoryUserRepository()
_memory_meal_entry_repo = InMemoryMealEntryRepository()
_food_repo = InMemoryFoodRepository(SEED_FOODS)


def get_user_repo():
    return _memory_user_repo


def get_meal_entry_repo():
    return _memory_meal_entry_repo


def get_food_repo():
    return _food_repo


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> str:
    try:
        return decode_token(credentials.credentials, settings.jwt_secret, "access")
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid or expired token"
        )
```

- [ ] **Step 4: Run to verify pass**

```bash
cd backend && pytest tests/test_memory_repositories.py tests/test_deps.py -v
```
Expected: `6 passed`.

- [ ] **Step 5: Commit**

```bash
git add backend/app/config.py backend/app/db backend/app/deps.py backend/tests/test_memory_repositories.py backend/tests/test_deps.py
git commit -m "$(cat <<'EOF'
Add settings, repository interfaces, in-memory repos, and shared deps

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: Auth router — register, login, refresh, me

**Files:**
- Create: `backend/app/auth/__init__.py`, `backend/app/auth/models.py`, `backend/app/auth/router.py`, `backend/tests/test_auth_router.py`
- Modify: `backend/app/main.py` (register the auth router), `backend/tests/conftest.py` (fresh repos per test + `auth_headers` fixture)

**Interfaces:**
- Consumes: `hash_password`, `verify_password`, `create_token`, `decode_token` (Task 2); `get_user_repo`, `get_current_user_id` (Task 3).
- Produces: `POST /auth/register`, `POST /auth/login`, `POST /auth/refresh`, `GET /auth/me`; the `auth_headers` pytest fixture (`auth_headers(email=..., password=...) -> dict`) used by every later router test.

- [ ] **Step 1: Write the failing tests**

`backend/tests/test_auth_router.py`:
```python
def test_register_then_login_returns_tokens(client):
    register = client.post(
        "/auth/register", json={"email": "user@example.com", "password": "password123"}
    )
    assert register.status_code == 201

    login = client.post(
        "/auth/login", json={"email": "user@example.com", "password": "password123"}
    )

    assert login.status_code == 200
    body = login.json()
    assert body["access_token"]
    assert body["refresh_token"]


def test_register_duplicate_email_is_rejected(client):
    client.post("/auth/register", json={"email": "dup@example.com", "password": "password123"})

    response = client.post(
        "/auth/register", json={"email": "dup@example.com", "password": "password123"}
    )

    assert response.status_code == 409


def test_login_with_wrong_password_is_rejected(client):
    client.post("/auth/register", json={"email": "user2@example.com", "password": "password123"})

    response = client.post(
        "/auth/login", json={"email": "user2@example.com", "password": "wrong"}
    )

    assert response.status_code == 401


def test_refresh_returns_new_token_pair(client):
    client.post("/auth/register", json={"email": "user3@example.com", "password": "password123"})
    login = client.post(
        "/auth/login", json={"email": "user3@example.com", "password": "password123"}
    )
    refresh_token = login.json()["refresh_token"]

    response = client.post("/auth/refresh", json={"refresh_token": refresh_token})

    assert response.status_code == 200
    assert response.json()["access_token"]


def test_me_returns_current_user(client, auth_headers):
    headers = auth_headers(email="user4@example.com")

    response = client.get("/auth/me", headers=headers)

    assert response.status_code == 200
    assert response.json()["email"] == "user4@example.com"


def test_me_without_token_is_rejected(client):
    response = client.get("/auth/me")

    assert response.status_code == 403
```

- [ ] **Step 2: Run to verify failure**

```bash
cd backend && pytest tests/test_auth_router.py -v
```
Expected: FAIL — `auth_headers` fixture and `/auth` routes don't exist yet.

- [ ] **Step 3: Implement**

`backend/app/auth/__init__.py`: (empty file)

`backend/app/auth/models.py`:
```python
from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class OAuthRequest(BaseModel):
    id_token: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: str
    email: str
```

`backend/app/auth/router.py`:
```python
from fastapi import APIRouter, Depends, HTTPException, status

from ..config import settings
from ..deps import get_current_user_id, get_user_repo
from ..security import create_token, decode_token, hash_password, verify_password
from .models import LoginRequest, RefreshRequest, RegisterRequest, TokenPair, UserOut

router = APIRouter()


def _token_pair(user_id: str) -> TokenPair:
    return TokenPair(
        access_token=create_token(user_id, settings.jwt_secret, "access"),
        refresh_token=create_token(user_id, settings.jwt_secret, "refresh"),
    )


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, user_repo=Depends(get_user_repo)):
    if await user_repo.get_by_email(body.email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="email already registered")
    await user_repo.create({"email": body.email, "password_hash": hash_password(body.password)})
    return {"status": "created"}


@router.post("/login", response_model=TokenPair)
async def login(body: LoginRequest, user_repo=Depends(get_user_repo)):
    user = await user_repo.get_by_email(body.email)
    if not user or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid email or password")
    return _token_pair(user["id"])


@router.post("/refresh", response_model=TokenPair)
async def refresh(body: RefreshRequest, user_repo=Depends(get_user_repo)):
    try:
        user_id = decode_token(body.refresh_token, settings.jwt_secret, "refresh")
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid or expired refresh token")
    if not await user_repo.get_by_id(user_id):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="user no longer exists")
    return _token_pair(user_id)


@router.get("/me", response_model=UserOut)
async def me(user_id: str = Depends(get_current_user_id), user_repo=Depends(get_user_repo)):
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="user no longer exists")
    return UserOut(id=user["id"], email=user["email"])
```

`backend/app/main.py`:
```python
from fastapi import FastAPI

from .auth.router import router as auth_router

app = FastAPI(title="Health App API")
app.include_router(auth_router, prefix="/auth", tags=["auth"])


@app.get("/health")
async def health():
    return {"status": "ok"}
```

`backend/tests/conftest.py`:
```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from fastapi.testclient import TestClient

from app import deps
from app.db.memory import SEED_FOODS, InMemoryFoodRepository, InMemoryMealEntryRepository, InMemoryUserRepository
from app.main import app


@pytest.fixture()
def client():
    user_repo = InMemoryUserRepository()
    meal_entry_repo = InMemoryMealEntryRepository()
    food_repo = InMemoryFoodRepository(SEED_FOODS)

    app.dependency_overrides[deps.get_user_repo] = lambda: user_repo
    app.dependency_overrides[deps.get_meal_entry_repo] = lambda: meal_entry_repo
    app.dependency_overrides[deps.get_food_repo] = lambda: food_repo

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
Expected: all tests pass (previous tasks' tests plus the 6 new ones).

- [ ] **Step 5: Commit**

```bash
git add backend/app/auth backend/app/main.py backend/tests/conftest.py backend/tests/test_auth_router.py
git commit -m "$(cat <<'EOF'
Add auth router: register, login, refresh, and me endpoints

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 5: OAuth sign-in (Google, Apple, and a fake for tests)

**Files:**
- Create: `backend/app/auth/oauth.py`
- Modify: `backend/app/auth/router.py` (add the OAuth endpoint), `backend/tests/test_auth_router.py` (add OAuth tests)

**Interfaces:**
- Consumes: `settings` (Task 3); `get_user_repo`, `_token_pair` (this file, Task 4).
- Produces: `POST /auth/oauth/{provider}`, `get_oauth_verifier(provider: str) -> OAuthVerifier | None` from `app.auth.oauth`.

- [ ] **Step 1: Write the failing tests**

Append to `backend/tests/test_auth_router.py`:
```python
def test_oauth_login_creates_user_on_first_sign_in(client):
    response = client.post("/auth/oauth/google", json={"id_token": "newuser@example.com"})

    assert response.status_code == 200
    assert response.json()["access_token"]


def test_oauth_login_reuses_existing_user(client):
    first = client.post("/auth/oauth/google", json={"id_token": "same@example.com"})
    second = client.post("/auth/oauth/google", json={"id_token": "same@example.com"})

    me1 = client.get("/auth/me", headers={"Authorization": f"Bearer {first.json()['access_token']}"})
    me2 = client.get("/auth/me", headers={"Authorization": f"Bearer {second.json()['access_token']}"})

    assert me1.json()["id"] == me2.json()["id"]


def test_oauth_login_rejects_invalid_token(client):
    response = client.post("/auth/oauth/google", json={"id_token": "invalid"})

    assert response.status_code == 401


def test_oauth_login_rejects_unknown_provider(client):
    response = client.post("/auth/oauth/facebook", json={"id_token": "someone@example.com"})

    assert response.status_code == 400
```

- [ ] **Step 2: Run to verify failure**

```bash
cd backend && pytest tests/test_auth_router.py -v -k oauth
```
Expected: FAIL — `/auth/oauth/{provider}` doesn't exist (404).

- [ ] **Step 3: Implement**

`backend/app/auth/oauth.py`:
```python
from typing import Optional, Protocol

import jwt
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token

from ..config import settings

APPLE_JWKS_URL = "https://appleid.apple.com/auth/keys"


class OAuthVerifier(Protocol):
    async def verify(self, id_token: str) -> str:
        """Returns the verified email address, or raises on an invalid token."""
        ...


class GoogleOAuthVerifier:
    def __init__(self, client_id: str):
        self._client_id = client_id

    async def verify(self, id_token: str) -> str:
        info = google_id_token.verify_oauth2_token(id_token, google_requests.Request(), self._client_id)
        return info["email"]


class AppleOAuthVerifier:
    def __init__(self, bundle_id: str):
        self._bundle_id = bundle_id
        self._jwks_client = jwt.PyJWKClient(APPLE_JWKS_URL)

    async def verify(self, id_token: str) -> str:
        signing_key = self._jwks_client.get_signing_key_from_jwt(id_token)
        payload = jwt.decode(
            id_token,
            signing_key.key,
            algorithms=["RS256"],
            audience=self._bundle_id,
            issuer="https://appleid.apple.com",
        )
        return payload["email"]


class FakeOAuthVerifier:
    """Test/dev double: the id_token IS the email, unless it's the literal string 'invalid'."""

    async def verify(self, id_token: str) -> str:
        if id_token == "invalid":
            raise ValueError("invalid token")
        return id_token


_verifiers: dict[str, OAuthVerifier] = {}
_built = False


def _build_verifiers() -> dict[str, OAuthVerifier]:
    verifiers: dict[str, OAuthVerifier] = {}
    verifiers["google"] = (
        GoogleOAuthVerifier(settings.google_oauth_client_id)
        if settings.google_oauth_client_id
        else FakeOAuthVerifier()
    )
    verifiers["apple"] = (
        AppleOAuthVerifier(settings.apple_oauth_bundle_id)
        if settings.apple_oauth_bundle_id
        else FakeOAuthVerifier()
    )
    return verifiers


def get_oauth_verifier(provider: str) -> Optional[OAuthVerifier]:
    global _verifiers, _built
    if not _built:
        _verifiers = _build_verifiers()
        _built = True
    return _verifiers.get(provider)
```

Add to `backend/app/auth/router.py` (new import + new route at the end of the file):
```python
from .oauth import get_oauth_verifier
from .models import OAuthRequest  # add OAuthRequest to the existing models import line instead of duplicating
```
Replace the existing `from .models import ...` line with:
```python
from .models import LoginRequest, OAuthRequest, RefreshRequest, RegisterRequest, TokenPair, UserOut
```
And append this route to the router:
```python
@router.post("/oauth/{provider}", response_model=TokenPair)
async def oauth_login(provider: str, body: OAuthRequest, user_repo=Depends(get_user_repo)):
    verifier = get_oauth_verifier(provider)
    if verifier is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"unsupported provider: {provider}")
    try:
        email = await verifier.verify(body.id_token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid oauth token")
    user = await user_repo.get_by_email(email)
    if not user:
        user = await user_repo.create({"email": email, "password_hash": ""})
    return _token_pair(user["id"])
```

- [ ] **Step 4: Run to verify pass**

```bash
cd backend && pytest tests/test_auth_router.py -v
```
Expected: all tests pass (default settings have no Google/Apple client id configured, so `FakeOAuthVerifier` is used).

- [ ] **Step 5: Commit**

```bash
git add backend/app/auth/oauth.py backend/app/auth/router.py backend/tests/test_auth_router.py
git commit -m "$(cat <<'EOF'
Add Google/Apple OAuth sign-in behind a swappable verifier interface

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 6: Foods search endpoint

**Files:**
- Create: `backend/app/meals/__init__.py`, `backend/app/meals/models.py`, `backend/app/meals/router.py`, `backend/tests/test_meals_router.py`
- Modify: `backend/app/main.py` (register the meals router)

**Interfaces:**
- Consumes: `get_current_user_id`, `get_food_repo` (Task 3).
- Produces: `GET /meals/foods/search?q=`; `FoodOut` model from `app.meals.models`, reused by later meals tasks.

- [ ] **Step 1: Write the failing test**

`backend/tests/test_meals_router.py`:
```python
def test_search_foods_matches_partial_case_insensitive_name(client, auth_headers):
    headers = auth_headers()

    response = client.get("/meals/foods/search", params={"q": "CHICK"}, headers=headers)

    assert response.status_code == 200
    names = [f["name"] for f in response.json()]
    assert any("Chicken" in name for name in names)


def test_search_foods_requires_auth(client):
    response = client.get("/meals/foods/search", params={"q": "chicken"})

    assert response.status_code == 403
```

- [ ] **Step 2: Run to verify failure**

```bash
cd backend && pytest tests/test_meals_router.py -v
```
Expected: FAIL — `/meals` routes don't exist (404).

- [ ] **Step 3: Implement**

`backend/app/meals/__init__.py`: (empty file)

`backend/app/meals/models.py`:
```python
from pydantic import BaseModel


class FoodOut(BaseModel):
    id: str
    name: str
    serving_size: float
    serving_unit: str
    calories_per_serving: float
    protein_g: float
    carbs_g: float
    fat_g: float
```

`backend/app/meals/router.py`:
```python
from fastapi import APIRouter, Depends

from ..deps import get_current_user_id, get_food_repo
from .models import FoodOut

router = APIRouter()


@router.get("/foods/search", response_model=list[FoodOut])
async def search_foods(
    q: str,
    user_id: str = Depends(get_current_user_id),
    food_repo=Depends(get_food_repo),
):
    return await food_repo.search(q)
```

`backend/app/main.py`:
```python
from fastapi import FastAPI

from .auth.router import router as auth_router
from .meals.router import router as meals_router

app = FastAPI(title="Health App API")
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(meals_router, prefix="/meals", tags=["meals"])


@app.get("/health")
async def health():
    return {"status": "ok"}
```

- [ ] **Step 4: Run to verify pass**

```bash
cd backend && pytest tests/test_meals_router.py -v
```
Expected: `2 passed`.

- [ ] **Step 5: Commit**

```bash
git add backend/app/meals backend/app/main.py backend/tests/test_meals_router.py
git commit -m "$(cat <<'EOF'
Add food search endpoint

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 7: Meal entry CRUD with ownership checks

**Files:**
- Modify: `backend/app/meals/models.py`, `backend/app/meals/router.py`, `backend/tests/test_meals_router.py`

**Interfaces:**
- Consumes: `get_current_user_id`, `get_meal_entry_repo` (Task 3).
- Produces: `POST /meals/entries`, `GET /meals/entries?day=`, `PATCH /meals/entries/{id}`, `DELETE /meals/entries/{id}`; `MealEntryCreate`, `MealEntryUpdate`, `MealEntryOut` models.

- [ ] **Step 1: Write the failing tests**

Append to `backend/tests/test_meals_router.py`:
```python
ENTRY_PAYLOAD = {
    "meal_slot": "breakfast",
    "source": "quick_add",
    "logged_at": "2026-09-16T08:00:00Z",
    "calories": 300,
    "protein_g": 20,
    "carbs_g": 30,
    "fat_g": 10,
}


def test_create_and_list_entry_for_day(client, auth_headers):
    headers = auth_headers()

    create = client.post("/meals/entries", json=ENTRY_PAYLOAD, headers=headers)
    assert create.status_code == 201

    listing = client.get("/meals/entries", params={"day": "2026-09-16"}, headers=headers)
    assert listing.status_code == 200
    assert len(listing.json()) == 1
    assert listing.json()[0]["calories"] == 300


def test_update_and_delete_own_entry(client, auth_headers):
    headers = auth_headers()
    entry_id = client.post("/meals/entries", json=ENTRY_PAYLOAD, headers=headers).json()["id"]

    update = client.patch(f"/meals/entries/{entry_id}", json={"calories": 450}, headers=headers)
    assert update.status_code == 200
    assert update.json()["calories"] == 450

    delete = client.delete(f"/meals/entries/{entry_id}", headers=headers)
    assert delete.status_code == 204

    listing = client.get("/meals/entries", params={"day": "2026-09-16"}, headers=headers)
    assert listing.json() == []


def test_user_cannot_read_or_modify_another_users_entry(client, auth_headers):
    headers_a = auth_headers(email="owner@example.com")
    headers_b = auth_headers(email="intruder@example.com")
    entry_id = client.post("/meals/entries", json=ENTRY_PAYLOAD, headers=headers_a).json()["id"]

    update = client.patch(f"/meals/entries/{entry_id}", json={"calories": 999}, headers=headers_b)
    assert update.status_code == 404

    delete = client.delete(f"/meals/entries/{entry_id}", headers=headers_b)
    assert delete.status_code == 404
```

- [ ] **Step 2: Run to verify failure**

```bash
cd backend && pytest tests/test_meals_router.py -v
```
Expected: FAIL — `/meals/entries` routes don't exist.

- [ ] **Step 3: Implement**

Append to `backend/app/meals/models.py`:
```python
from datetime import datetime
from typing import Literal, Optional

MealSlot = Literal["breakfast", "lunch", "dinner", "snack"]
EntrySource = Literal["search", "quick_add", "photo_ai"]


class MealEntryCreate(BaseModel):
    meal_slot: MealSlot
    source: EntrySource
    logged_at: datetime
    food_id: Optional[str] = None
    calories: float
    protein_g: float = 0
    carbs_g: float = 0
    fat_g: float = 0


class MealEntryUpdate(BaseModel):
    meal_slot: Optional[MealSlot] = None
    calories: Optional[float] = None
    protein_g: Optional[float] = None
    carbs_g: Optional[float] = None
    fat_g: Optional[float] = None


class MealEntryOut(MealEntryCreate):
    id: str
    user_id: str
    created_at: str
    updated_at: str
```
(This requires adding `from datetime import datetime` and `from typing import Literal, Optional` — combine with the existing `from pydantic import BaseModel` import at the top of the file rather than duplicating it.)

Replace `backend/app/meals/router.py` with:
```python
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status

from ..deps import get_current_user_id, get_food_repo, get_meal_entry_repo
from .models import FoodOut, MealEntryCreate, MealEntryOut, MealEntryUpdate

router = APIRouter()


@router.get("/foods/search", response_model=list[FoodOut])
async def search_foods(
    q: str,
    user_id: str = Depends(get_current_user_id),
    food_repo=Depends(get_food_repo),
):
    return await food_repo.search(q)


@router.post("/entries", response_model=MealEntryOut, status_code=status.HTTP_201_CREATED)
async def create_entry(
    body: MealEntryCreate,
    user_id: str = Depends(get_current_user_id),
    meal_entry_repo=Depends(get_meal_entry_repo),
):
    return await meal_entry_repo.create({**body.model_dump(mode="json"), "user_id": user_id})


@router.get("/entries", response_model=list[MealEntryOut])
async def list_entries(
    day: date,
    user_id: str = Depends(get_current_user_id),
    meal_entry_repo=Depends(get_meal_entry_repo),
):
    return await meal_entry_repo.list_for_day(user_id, day)


@router.patch("/entries/{entry_id}", response_model=MealEntryOut)
async def update_entry(
    entry_id: str,
    body: MealEntryUpdate,
    user_id: str = Depends(get_current_user_id),
    meal_entry_repo=Depends(get_meal_entry_repo),
):
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    updated = await meal_entry_repo.update(user_id, entry_id, updates)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="entry not found")
    return updated


@router.delete("/entries/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_entry(
    entry_id: str,
    user_id: str = Depends(get_current_user_id),
    meal_entry_repo=Depends(get_meal_entry_repo),
):
    if not await meal_entry_repo.delete(user_id, entry_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="entry not found")
```

- [ ] **Step 4: Run to verify pass**

```bash
cd backend && pytest tests/test_meals_router.py -v
```
Expected: `5 passed`.

- [ ] **Step 5: Commit**

```bash
git add backend/app/meals backend/tests/test_meals_router.py
git commit -m "$(cat <<'EOF'
Add meal entry CRUD endpoints with per-user ownership checks

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 8: Photo-AI nutrition estimate endpoint

**Files:**
- Create: `backend/app/meals/nutrition_estimator.py`
- Modify: `backend/app/meals/models.py`, `backend/app/meals/router.py`, `backend/tests/test_meals_router.py`

**Interfaces:**
- Consumes: `settings.anthropic_api_key`, `settings.anthropic_model` (Task 3); `get_current_user_id` (Task 3).
- Produces: `POST /meals/photo-estimate` → `PhotoEstimateOut`; `get_nutrition_estimator() -> NutritionEstimator`.

- [ ] **Step 1: Write the failing tests**

Append to `backend/tests/test_meals_router.py`:
```python
def test_photo_estimate_returns_estimate(client, auth_headers):
    headers = auth_headers()
    files = {"photo": ("meal.jpg", b"fake-image-bytes", "image/jpeg")}

    response = client.post("/meals/photo-estimate", headers=headers, files=files)

    assert response.status_code == 200
    body = response.json()
    assert body["calories"] > 0
    assert 0 <= body["confidence"] <= 1


def test_photo_estimate_rejects_unsupported_file_type(client, auth_headers):
    headers = auth_headers()
    files = {"photo": ("notes.txt", b"not an image", "text/plain")}

    response = client.post("/meals/photo-estimate", headers=headers, files=files)

    assert response.status_code == 400
```

- [ ] **Step 2: Run to verify failure**

```bash
cd backend && pytest tests/test_meals_router.py -v -k photo_estimate
```
Expected: FAIL — `/meals/photo-estimate` doesn't exist.

- [ ] **Step 3: Implement**

Append to `backend/app/meals/models.py`:
```python
class PhotoEstimateOut(BaseModel):
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float
    confidence: float
    description: str
```

`backend/app/meals/nutrition_estimator.py`:
```python
import base64
import json
from typing import Optional, Protocol

import anthropic

from ..config import settings
from .models import PhotoEstimateOut

ESTIMATE_PROMPT = (
    "You are a nutrition estimation assistant. Look at this photo of a meal and "
    "estimate its nutritional content. Respond with ONLY a JSON object with keys: "
    "calories (number), protein_g (number), carbs_g (number), fat_g (number), "
    "confidence (number between 0 and 1), description (a short string describing "
    "what you see). No prose, no markdown fences — just the JSON object."
)


class NutritionEstimator(Protocol):
    async def estimate(self, image_bytes: bytes, content_type: str) -> PhotoEstimateOut: ...


class ClaudeVisionEstimator:
    def __init__(self, api_key: str, model: str):
        self._client = anthropic.AsyncAnthropic(api_key=api_key)
        self._model = model

    async def estimate(self, image_bytes: bytes, content_type: str) -> PhotoEstimateOut:
        response = await self._client.messages.create(
            model=self._model,
            max_tokens=300,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": content_type,
                                "data": base64.b64encode(image_bytes).decode("ascii"),
                            },
                        },
                        {"type": "text", "text": ESTIMATE_PROMPT},
                    ],
                }
            ],
        )
        data = json.loads(response.content[0].text)
        return PhotoEstimateOut(**data)


class FakeNutritionEstimator:
    """Dev/test double: returns a fixed plausible estimate regardless of image content."""

    async def estimate(self, image_bytes: bytes, content_type: str) -> PhotoEstimateOut:
        return PhotoEstimateOut(
            calories=450, protein_g=30, carbs_g=40, fat_g=15,
            confidence=0.5, description="fake estimate used because no ANTHROPIC_API_KEY is configured",
        )


_estimator: Optional[NutritionEstimator] = None


def get_nutrition_estimator() -> NutritionEstimator:
    global _estimator
    if _estimator is None:
        _estimator = (
            ClaudeVisionEstimator(settings.anthropic_api_key, settings.anthropic_model)
            if settings.anthropic_api_key
            else FakeNutritionEstimator()
        )
    return _estimator
```

Add to `backend/app/meals/router.py` (new imports plus a new route at the end of the file):
```python
from fastapi import UploadFile  # add UploadFile to the existing fastapi import line instead of duplicating

from .nutrition_estimator import get_nutrition_estimator
from .models import PhotoEstimateOut  # add PhotoEstimateOut to the existing models import line
```
Append:
```python
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}


@router.post("/photo-estimate", response_model=PhotoEstimateOut)
async def photo_estimate(
    photo: UploadFile,
    user_id: str = Depends(get_current_user_id),
):
    content_type = photo.content_type or "image/jpeg"
    if content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="unsupported image type")
    estimator = get_nutrition_estimator()
    image_bytes = await photo.read()
    return await estimator.estimate(image_bytes, content_type)
```

- [ ] **Step 4: Run to verify pass**

```bash
cd backend && pytest tests/test_meals_router.py -v
```
Expected: `7 passed` (default test settings have no `ANTHROPIC_API_KEY`, so `FakeNutritionEstimator` is used).

- [ ] **Step 5: Commit**

```bash
git add backend/app/meals backend/tests/test_meals_router.py
git commit -m "$(cat <<'EOF'
Add photo-based nutrition estimate endpoint with a swappable estimator

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 9: Cosmos DB repositories and production wiring

**Files:**
- Create: `backend/app/db/cosmos.py`, `backend/tests/test_cosmos_repos.py`
- Modify: `backend/app/deps.py`, `backend/app/main.py`

**Interfaces:**
- Consumes: `settings` (Task 3); implements the `UserRepository`/`MealEntryRepository` Protocols from `app.db.base` (Task 3).
- Produces: `CosmosUserRepository`, `CosmosMealEntryRepository`, `get_cosmos_client()`, `init_cosmos(client, database_name)`.

- [ ] **Step 1: Write the failing tests**

`backend/tests/test_cosmos_repos.py`:
```python
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
```

- [ ] **Step 2: Run to verify failure**

```bash
cd backend && pytest tests/test_cosmos_repos.py -v
```
Expected: FAIL — `app.db.cosmos` doesn't exist.

- [ ] **Step 3: Implement**

`backend/app/db/cosmos.py`:
```python
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


async def init_cosmos(client: CosmosClient, database_name: str) -> None:
    database = await client.create_database_if_not_exists(database_name)
    await database.create_container_if_not_exists(id="users", partition_key=PartitionKey(path="/id"))
    await database.create_container_if_not_exists(
        id="meal_entries", partition_key=PartitionKey(path="/user_id")
    )


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
```

`backend/app/deps.py` — replace the `get_user_repo` / `get_meal_entry_repo` functions:
```python
from .config import settings
from .db.cosmos import CosmosMealEntryRepository, CosmosUserRepository, get_cosmos_client


def get_user_repo():
    if settings.db_backend == "cosmos":
        return CosmosUserRepository(get_cosmos_client(), settings.cosmos_database_name)
    return _memory_user_repo


def get_meal_entry_repo():
    if settings.db_backend == "cosmos":
        return CosmosMealEntryRepository(get_cosmos_client(), settings.cosmos_database_name)
    return _memory_meal_entry_repo
```
(Add the `from .db.cosmos import ...` line to the existing imports at the top of `deps.py`, and add `from .config import settings` if not already present — it already is, from Task 4's `get_current_user_id`.)

`backend/app/main.py`:
```python
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .auth.router import router as auth_router
from .config import settings
from .db.cosmos import get_cosmos_client, init_cosmos
from .meals.router import router as meals_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.db_backend == "cosmos":
        await init_cosmos(get_cosmos_client(), settings.cosmos_database_name)
    yield


app = FastAPI(title="Health App API", lifespan=lifespan)
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(meals_router, prefix="/meals", tags=["meals"])


@app.get("/health")
async def health():
    return {"status": "ok"}
```

- [ ] **Step 4: Run to verify pass**

```bash
cd backend && pytest tests/ -v
```
Expected: all tests pass. `db_backend` defaults to `"memory"`, so the full suite still runs with zero Azure connectivity — `init_cosmos` is only invoked when `DB_BACKEND=cosmos` is set.

- [ ] **Step 5: Commit**

```bash
git add backend/app/db/cosmos.py backend/app/deps.py backend/app/main.py backend/tests/test_cosmos_repos.py
git commit -m "$(cat <<'EOF'
Add Cosmos DB repositories and wire them in behind DB_BACKEND=cosmos

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 10: Dockerfile, env docs, and container smoke test

**Files:**
- Create: `backend/Dockerfile`, `backend/.env.example`, `backend/README.md`

**Interfaces:** none (packaging only).

- [ ] **Step 1: Create the Dockerfile**

`backend/Dockerfile`:
```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 2: Document environment variables**

`backend/.env.example`:
```
JWT_SECRET=change-me-to-a-long-random-value
DB_BACKEND=memory
COSMOS_CONNECTION_STRING=
COSMOS_DATABASE_NAME=health_app
GOOGLE_OAUTH_CLIENT_ID=
APPLE_OAUTH_BUNDLE_ID=
ANTHROPIC_API_KEY=
ANTHROPIC_MODEL=claude-sonnet-5
```

`backend/README.md`:
```markdown
# Health App backend

FastAPI service backing the health app's meal tracker (and future modules).

## Local development

    python -m venv .venv && source .venv/bin/activate
    pip install -r requirements.txt
    cp .env.example .env   # edit as needed; defaults run entirely in-memory
    uvicorn app.main:app --reload

## Tests

    pytest tests/ -v

Tests always run against the in-memory repositories and fake OAuth/nutrition
estimators — no Azure or Anthropic credentials are required.

## Container

    docker build -t health-app-backend .
    docker run -p 8000:8000 --env-file .env health-app-backend
    curl http://localhost:8000/health
```

- [ ] **Step 3: Manual verification**

Run:
```bash
cd backend
docker build -t health-app-backend .
docker run -d -p 8000:8000 --name health-app-backend-test health-app-backend
curl -sf http://localhost:8000/health
docker stop health-app-backend-test && docker rm health-app-backend-test
```
Expected: the `curl` prints `{"status":"ok"}` and both docker commands succeed.

- [ ] **Step 4: Commit**

```bash
git add backend/Dockerfile backend/.env.example backend/README.md
git commit -m "$(cat <<'EOF'
Add Dockerfile, env var documentation, and backend README

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 11: Client API client with token storage and refresh-on-401

**Files:**
- Create: `src/lib/api-client.ts`

**Interfaces:**
- Produces: `API_BASE_URL`, `getStoredTokens()`, `storeTokens(access, refresh)`, `clearTokens()`, `apiFetch<T>(path, options?) -> Promise<T>`, `UnauthorizedError` — used by every client task from Task 12 onward.

- [ ] **Step 1: Install the secure storage dependency**

```bash
npx expo install expo-secure-store
```

- [ ] **Step 2: Create the API client**

`src/lib/api-client.ts`:
```typescript
import * as SecureStore from "expo-secure-store";

const ACCESS_TOKEN_KEY = "health_app.access_token";
const REFRESH_TOKEN_KEY = "health_app.refresh_token";

export const API_BASE_URL =
  process.env.EXPO_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export async function getStoredTokens() {
  const [accessToken, refreshToken] = await Promise.all([
    SecureStore.getItemAsync(ACCESS_TOKEN_KEY),
    SecureStore.getItemAsync(REFRESH_TOKEN_KEY),
  ]);
  return { accessToken, refreshToken };
}

export async function storeTokens(accessToken: string, refreshToken: string) {
  await Promise.all([
    SecureStore.setItemAsync(ACCESS_TOKEN_KEY, accessToken),
    SecureStore.setItemAsync(REFRESH_TOKEN_KEY, refreshToken),
  ]);
}

export async function clearTokens() {
  await Promise.all([
    SecureStore.deleteItemAsync(ACCESS_TOKEN_KEY),
    SecureStore.deleteItemAsync(REFRESH_TOKEN_KEY),
  ]);
}

export class UnauthorizedError extends Error {}

async function refreshAccessToken(): Promise<string | null> {
  const { refreshToken } = await getStoredTokens();
  if (!refreshToken) return null;

  const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });
  if (!response.ok) return null;

  const data = await response.json();
  await storeTokens(data.access_token, data.refresh_token);
  return data.access_token as string;
}

export async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const { accessToken } = await getStoredTokens();
  const doFetch = (token: string | null) =>
    fetch(`${API_BASE_URL}${path}`, {
      ...options,
      headers: {
        ...(options.headers ?? {}),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
    });

  let response = await doFetch(accessToken);

  if (response.status === 401) {
    const newAccessToken = await refreshAccessToken();
    if (!newAccessToken) {
      await clearTokens();
      throw new UnauthorizedError("session expired");
    }
    response = await doFetch(newAccessToken);
  }

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body?.error?.message ?? `request failed: ${response.status}`);
  }

  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}
```

- [ ] **Step 3: Verify it compiles**

```bash
npx tsc --noEmit
```
Expected: no errors.

- [ ] **Step 4: Commit**

```bash
git add package.json package-lock.json src/lib/api-client.ts
git commit -m "$(cat <<'EOF'
Add API client with secure token storage and refresh-on-401

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 12: Auth context (`useAuth`)

**Files:**
- Create: `src/lib/auth-context.tsx`

**Interfaces:**
- Consumes: `apiFetch`, `storeTokens`, `clearTokens`, `getStoredTokens` (Task 11).
- Produces: `AuthProvider`, `useAuth() -> { user, isLoading, login, register, logout }` — used by Tasks 13-15.

- [ ] **Step 1: Create the auth context**

`src/lib/auth-context.tsx`:
```tsx
import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

import { apiFetch, clearTokens, getStoredTokens, storeTokens } from "./api-client";

type User = { id: string; email: string };

type AuthContextValue = {
  user: User | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

async function fetchCurrentUser(): Promise<User> {
  return apiFetch<User>("/auth/me");
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    (async () => {
      const { accessToken } = await getStoredTokens();
      if (accessToken) {
        try {
          setUser(await fetchCurrentUser());
        } catch {
          setUser(null);
        }
      }
      setIsLoading(false);
    })();
  }, []);

  const login = async (email: string, password: string) => {
    const tokens = await apiFetch<{ access_token: string; refresh_token: string }>("/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    await storeTokens(tokens.access_token, tokens.refresh_token);
    setUser(await fetchCurrentUser());
  };

  const register = async (email: string, password: string) => {
    await apiFetch("/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    await login(email, password);
  };

  const logout = async () => {
    await clearTokens();
    setUser(null);
  };

  const value = useMemo(() => ({ user, isLoading, login, register, logout }), [user, isLoading]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
```

- [ ] **Step 2: Verify it compiles**

```bash
npx tsc --noEmit
```
Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add src/lib/auth-context.tsx
git commit -m "$(cat <<'EOF'
Add AuthProvider/useAuth for shared client auth state

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 13: Login and register screens

**Files:**
- Create: `src/app/(auth)/_layout.tsx`, `src/app/(auth)/login.tsx`, `src/app/(auth)/register.tsx`

**Interfaces:**
- Consumes: `useAuth` (Task 12).
- Produces: routes `/login`, `/register` — consumed by Task 15's redirect logic.

- [ ] **Step 1: Create the auth route group layout**

`src/app/(auth)/_layout.tsx`:
```tsx
import { Stack } from "expo-router";

export default function AuthLayout() {
  return (
    <Stack screenOptions={{ headerShown: false }}>
      <Stack.Screen name="login" />
      <Stack.Screen name="register" />
    </Stack>
  );
}
```

- [ ] **Step 2: Create the login screen**

`src/app/(auth)/login.tsx`:
```tsx
import { useRouter, type Href } from "expo-router";
import { useState } from "react";
import { Button, Text, TextInput, View } from "react-native";

import { useAuth } from "@/lib/auth-context";

export default function LoginScreen() {
  const { login } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  const onSubmit = async () => {
    setError(null);
    try {
      await login(email, password);
      router.replace("/meal-tracker" as Href);
    } catch (err) {
      setError(err instanceof Error ? err.message : "login failed");
    }
  };

  return (
    <View style={{ flex: 1, justifyContent: "center", padding: 24, gap: 12 }}>
      <TextInput
        placeholder="Email"
        autoCapitalize="none"
        keyboardType="email-address"
        value={email}
        onChangeText={setEmail}
        style={{ borderWidth: 1, padding: 12, borderRadius: 8 }}
      />
      <TextInput
        placeholder="Password"
        secureTextEntry
        value={password}
        onChangeText={setPassword}
        style={{ borderWidth: 1, padding: 12, borderRadius: 8 }}
      />
      {error ? <Text style={{ color: "red" }}>{error}</Text> : null}
      <Button title="Log in" onPress={onSubmit} />
      <Button title="Need an account? Register" onPress={() => router.push("/register" as Href)} />
    </View>
  );
}
```

- [ ] **Step 3: Create the register screen**

`src/app/(auth)/register.tsx`:
```tsx
import { useRouter, type Href } from "expo-router";
import { useState } from "react";
import { Button, Text, TextInput, View } from "react-native";

import { useAuth } from "@/lib/auth-context";

export default function RegisterScreen() {
  const { register } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  const onSubmit = async () => {
    setError(null);
    try {
      await register(email, password);
      router.replace("/meal-tracker" as Href);
    } catch (err) {
      setError(err instanceof Error ? err.message : "registration failed");
    }
  };

  return (
    <View style={{ flex: 1, justifyContent: "center", padding: 24, gap: 12 }}>
      <TextInput
        placeholder="Email"
        autoCapitalize="none"
        keyboardType="email-address"
        value={email}
        onChangeText={setEmail}
        style={{ borderWidth: 1, padding: 12, borderRadius: 8 }}
      />
      <TextInput
        placeholder="Password"
        secureTextEntry
        value={password}
        onChangeText={setPassword}
        style={{ borderWidth: 1, padding: 12, borderRadius: 8 }}
      />
      {error ? <Text style={{ color: "red" }}>{error}</Text> : null}
      <Button title="Register" onPress={onSubmit} />
      <Button title="Already have an account? Log in" onPress={() => router.push("/login" as Href)} />
    </View>
  );
}
```

- [ ] **Step 4: Manual verification**

Note: this screen references `/meal-tracker`, which doesn't exist until Task 16 renames it — that's expected; full end-to-end login can't be verified until then. For now:

```bash
npx tsc --noEmit
```
Expected: no errors (the `as Href` casts bypass typed-route checking for not-yet-existing routes).

- [ ] **Step 5: Commit**

```bash
git add src/app/\(auth\)
git commit -m "$(cat <<'EOF'
Add login and register screens

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 14: Rename `calorie-ai-tools` to `meal-tracker`

**Files:**
- Move: `src/app/calorie-ai-tools/_layout.tsx` → `src/app/meal-tracker/_layout.tsx`
- Move: `src/app/calorie-ai-tools/index.tsx` → `src/app/meal-tracker/index.tsx`
- Move: `src/app/calorie-ai-tools/camera.tsx` → `src/app/meal-tracker/camera.tsx`
- Move: `src/modules/calorie_camera/CalorieAiTools.tsx` → `src/modules/meal_tracker/CalorieAiTools.tsx`
- Move: `src/modules/calorie_camera/CalorieCamera.tsx` → `src/modules/meal_tracker/CalorieCamera.tsx`

**Interfaces:** none new — this is a pure rename; import paths that reference the moved files must be updated in place.

- [ ] **Step 1: Move the directories**

```bash
git mv src/app/calorie-ai-tools src/app/meal-tracker
git mv src/modules/calorie_camera src/modules/meal_tracker
```

- [ ] **Step 2: Update the import path in the moved route**

`src/app/meal-tracker/index.tsx` — change the import to point at the new module path:
```tsx
import CalorieAiTools from "@/modules/meal_tracker/CalorieAiTools";
import { SafeAreaView } from "react-native";

export default function MealTrackerRoute() {
  return (
    <SafeAreaView style={{ flex: 1 }}>
      <CalorieAiTools />
    </SafeAreaView>
  );
}
```

`src/app/meal-tracker/_layout.tsx` — update the title:
```tsx
import { Stack } from "expo-router";

export default function MealTrackerLayout() {
  return (
    <Stack>
      <Stack.Screen name="index" options={{ title: "Meal Tracker" }} />
      <Stack.Screen name="camera" options={{ title: "Calorie Camera" }} />
    </Stack>
  );
}
```

`src/modules/meal_tracker/CalorieAiTools.tsx` — update the route path used by the "Take a Photo" button:
```tsx
import { useRouter, type Href } from "expo-router";
import { Button, View } from "react-native";

export default function CalorieAiTools() {
  const router = useRouter();

  return (
    <View>
      <Button title="Take a Photo" onPress={() => router.push("/meal-tracker/camera" as Href)} />
      <Button title="View History" onPress={() => {}} />
      <Button title="Settings" onPress={() => {}} />
    </View>
  );
}
```

- [ ] **Step 3: Manual verification**

```bash
npx expo start
```
In the running app, navigate to `/meal-tracker` and confirm the three-button stub screen still renders, and tapping "Take a Photo" navigates to the camera stub without a red-box error.

- [ ] **Step 4: Commit**

```bash
git add -A src/app/meal-tracker src/modules/meal_tracker
git commit -m "$(cat <<'EOF'
Rename calorie-ai-tools/calorie_camera to meal-tracker/meal_tracker

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 15: Wire AuthProvider into the root layout and redirect on auth state

**Files:**
- Modify: `src/app/_layout.tsx`, `src/app/index.tsx`

**Interfaces:**
- Consumes: `AuthProvider`, `useAuth` (Task 12); routes `/login` (Task 13) and `/meal-tracker` (Task 14).

- [ ] **Step 1: Wrap the root layout in `AuthProvider`**

`src/app/_layout.tsx`:
```tsx
import { Stack } from "expo-router";
import { View } from "react-native";

import { AuthProvider } from "@/lib/auth-context";

export default function RootLayout() {
  return (
    <AuthProvider>
      <View style={{ flex: 1 }}>
        <Stack screenOptions={{ headerShown: false }} />
      </View>
    </AuthProvider>
  );
}
```

- [ ] **Step 2: Redirect based on auth state in the index route**

`src/app/index.tsx`:
```tsx
import { Redirect, type Href } from "expo-router";

import { useAuth } from "@/lib/auth-context";

export default function Home() {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return null;
  }

  return <Redirect href={(user ? "/meal-tracker" : "/login") as Href} />;
}
```

- [ ] **Step 3: Manual verification**

```bash
npx expo start
```
- With no stored session: app should land on the login screen.
- Register a new account: app should redirect to `/meal-tracker` and show the stub buttons.
- Force-quit and relaunch the app: it should go straight to `/meal-tracker` without showing login again (session persisted via `expo-secure-store`).

- [ ] **Step 4: Commit**

```bash
git add src/app/_layout.tsx src/app/index.tsx
git commit -m "$(cat <<'EOF'
Wire AuthProvider into the root layout with auth-based redirect

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 16: Meal tracker API bindings

**Files:**
- Create: `src/modules/meal_tracker/types.ts`, `src/modules/meal_tracker/api.ts`

**Interfaces:**
- Consumes: `apiFetch` (Task 11).
- Produces: `FoodOut`, `MealEntry`, `PhotoEstimate` types; `searchFoods(query)`, `createEntry(entry)`, `listEntriesForDay(day)`, `updateEntry(id, updates)`, `deleteEntry(id)`, `estimateFromPhoto(uri)` — used by Tasks 17-18.

- [ ] **Step 1: Define the shared types**

`src/modules/meal_tracker/types.ts`:
```typescript
export type MealSlot = "breakfast" | "lunch" | "dinner" | "snack";
export type EntrySource = "search" | "quick_add" | "photo_ai";

export type FoodOut = {
  id: string;
  name: string;
  serving_size: number;
  serving_unit: string;
  calories_per_serving: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
};

export type MealEntry = {
  id: string;
  user_id: string;
  meal_slot: MealSlot;
  source: EntrySource;
  logged_at: string;
  food_id?: string;
  calories: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
  created_at: string;
  updated_at: string;
};

export type MealEntryInput = {
  meal_slot: MealSlot;
  source: EntrySource;
  logged_at: string;
  food_id?: string;
  calories: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
};

export type PhotoEstimate = {
  calories: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
  confidence: number;
  description: string;
};
```

- [ ] **Step 2: Implement the API bindings**

`src/modules/meal_tracker/api.ts`:
```typescript
import { apiFetch } from "@/lib/api-client";

import type { FoodOut, MealEntry, MealEntryInput, PhotoEstimate } from "./types";

export function searchFoods(query: string): Promise<FoodOut[]> {
  return apiFetch<FoodOut[]>(`/meals/foods/search?q=${encodeURIComponent(query)}`);
}

export function listEntriesForDay(day: string): Promise<MealEntry[]> {
  return apiFetch<MealEntry[]>(`/meals/entries?day=${day}`);
}

export function createEntry(entry: MealEntryInput): Promise<MealEntry> {
  return apiFetch<MealEntry>("/meals/entries", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(entry),
  });
}

export function updateEntry(id: string, updates: Partial<MealEntryInput>): Promise<MealEntry> {
  return apiFetch<MealEntry>(`/meals/entries/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(updates),
  });
}

export function deleteEntry(id: string): Promise<void> {
  return apiFetch<void>(`/meals/entries/${id}`, { method: "DELETE" });
}

export async function estimateFromPhoto(photoUri: string): Promise<PhotoEstimate> {
  const formData = new FormData();
  formData.append("photo", {
    uri: photoUri,
    name: "meal.jpg",
    type: "image/jpeg",
  } as unknown as Blob);

  return apiFetch<PhotoEstimate>("/meals/photo-estimate", {
    method: "POST",
    body: formData,
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
git add src/modules/meal_tracker/types.ts src/modules/meal_tracker/api.ts
git commit -m "$(cat <<'EOF'
Add meal tracker API bindings and shared types

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 17: Diary screen (today's entries + totals)

**Files:**
- Modify: `src/app/meal-tracker/index.tsx` (replaces the stub menu with the real diary)

**Interfaces:**
- Consumes: `listEntriesForDay`, `deleteEntry` (Task 16).
- Produces: the `/meal-tracker` screen that Task 18's add-entry screen and Task 19's confirm screen navigate back to.

- [ ] **Step 1: Replace the stub with a real diary screen**

`src/app/meal-tracker/index.tsx`:
```tsx
import { useFocusEffect, useRouter, type Href } from "expo-router";
import { useCallback, useState } from "react";
import { Button, FlatList, SafeAreaView, Text, View } from "react-native";

import { deleteEntry, listEntriesForDay } from "@/modules/meal_tracker/api";
import type { MealEntry } from "@/modules/meal_tracker/types";

function todayIsoDate(): string {
  return new Date().toISOString().slice(0, 10);
}

export default function MealTrackerRoute() {
  const router = useRouter();
  const [entries, setEntries] = useState<MealEntry[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const load = useCallback(async () => {
    setIsLoading(true);
    try {
      setEntries(await listEntriesForDay(todayIsoDate()));
    } finally {
      setIsLoading(false);
    }
  }, []);

  useFocusEffect(
    useCallback(() => {
      load();
    }, [load])
  );

  const totals = entries.reduce(
    (acc, e) => ({
      calories: acc.calories + e.calories,
      protein_g: acc.protein_g + e.protein_g,
      carbs_g: acc.carbs_g + e.carbs_g,
      fat_g: acc.fat_g + e.fat_g,
    }),
    { calories: 0, protein_g: 0, carbs_g: 0, fat_g: 0 }
  );

  return (
    <SafeAreaView style={{ flex: 1, padding: 16 }}>
      <Text style={{ fontSize: 20, fontWeight: "600" }}>Today</Text>
      <Text>
        {Math.round(totals.calories)} kcal · P {Math.round(totals.protein_g)}g · C{" "}
        {Math.round(totals.carbs_g)}g · F {Math.round(totals.fat_g)}g
      </Text>

      <FlatList
        data={entries}
        keyExtractor={(item) => item.id}
        refreshing={isLoading}
        onRefresh={load}
        ListEmptyComponent={<Text>No entries yet today.</Text>}
        renderItem={({ item }) => (
          <View style={{ flexDirection: "row", justifyContent: "space-between", paddingVertical: 8 }}>
            <Text>
              {item.meal_slot}: {Math.round(item.calories)} kcal
            </Text>
            <Button
              title="Delete"
              onPress={async () => {
                await deleteEntry(item.id);
                load();
              }}
            />
          </View>
        )}
      />

      <Button title="Add Entry" onPress={() => router.push("/meal-tracker/add-entry" as Href)} />
    </SafeAreaView>
  );
}
```

- [ ] **Step 2: Manual verification**

```bash
npx expo start
```
Log in, land on `/meal-tracker`, confirm it shows "Today", the zeroed totals line, and "No entries yet today." with no crash. (The "Add Entry" button will 404 until Task 18.)

- [ ] **Step 3: Commit**

```bash
git add src/app/meal-tracker/index.tsx
git commit -m "$(cat <<'EOF'
Replace meal tracker stub with a real diary screen showing today's entries

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 18: Add-entry screen (search + quick add)

**Files:**
- Create: `src/app/meal-tracker/add-entry.tsx`

**Interfaces:**
- Consumes: `searchFoods`, `createEntry` (Task 16).

- [ ] **Step 1: Create the add-entry screen**

`src/app/meal-tracker/add-entry.tsx`:
```tsx
import { useRouter, type Href } from "expo-router";
import { useState } from "react";
import { Button, FlatList, SafeAreaView, Text, TextInput, View } from "react-native";

import { createEntry, searchFoods } from "@/modules/meal_tracker/api";
import type { FoodOut, MealSlot } from "@/modules/meal_tracker/types";

const MEAL_SLOTS: MealSlot[] = ["breakfast", "lunch", "dinner", "snack"];

export default function AddEntryScreen() {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<FoodOut[]>([]);
  const [mealSlot, setMealSlot] = useState<MealSlot>("breakfast");
  const [quickAddCalories, setQuickAddCalories] = useState("");

  const onSearch = async (text: string) => {
    setQuery(text);
    setResults(text.length >= 2 ? await searchFoods(text) : []);
  };

  const logFood = async (food: FoodOut) => {
    await createEntry({
      meal_slot: mealSlot,
      source: "search",
      logged_at: new Date().toISOString(),
      food_id: food.id,
      calories: food.calories_per_serving,
      protein_g: food.protein_g,
      carbs_g: food.carbs_g,
      fat_g: food.fat_g,
    });
    router.back();
  };

  const logQuickAdd = async () => {
    const calories = Number(quickAddCalories);
    if (!Number.isFinite(calories) || calories <= 0) return;
    await createEntry({
      meal_slot: mealSlot,
      source: "quick_add",
      logged_at: new Date().toISOString(),
      calories,
      protein_g: 0,
      carbs_g: 0,
      fat_g: 0,
    });
    router.back();
  };

  return (
    <SafeAreaView style={{ flex: 1, padding: 16, gap: 12 }}>
      <View style={{ flexDirection: "row", gap: 8 }}>
        {MEAL_SLOTS.map((slot) => (
          <Button
            key={slot}
            title={slot}
            color={slot === mealSlot ? "#208AEF" : undefined}
            onPress={() => setMealSlot(slot)}
          />
        ))}
      </View>

      <Button
        title="Take a Photo"
        onPress={() => router.push("/meal-tracker/camera" as Href)}
      />

      <TextInput
        placeholder="Search foods"
        value={query}
        onChangeText={onSearch}
        style={{ borderWidth: 1, padding: 12, borderRadius: 8 }}
      />
      <FlatList
        data={results}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => (
          <Button title={`${item.name} (${item.calories_per_serving} kcal)`} onPress={() => logFood(item)} />
        )}
      />

      <Text>Quick add (calories only)</Text>
      <TextInput
        placeholder="e.g. 250"
        keyboardType="numeric"
        value={quickAddCalories}
        onChangeText={setQuickAddCalories}
        style={{ borderWidth: 1, padding: 12, borderRadius: 8 }}
      />
      <Button title="Log Quick Add" onPress={logQuickAdd} />
    </SafeAreaView>
  );
}
```

- [ ] **Step 2: Manual verification**

```bash
npx expo start
```
From `/meal-tracker`, tap "Add Entry". Search "chick" and confirm "Chicken Breast, cooked" appears; tap it and confirm it returns to the diary with a new breakfast entry. Then quick-add "250" calories and confirm a second entry appears and totals update.

- [ ] **Step 3: Commit**

```bash
git add src/app/meal-tracker/add-entry.tsx
git commit -m "$(cat <<'EOF'
Add add-entry screen with food search and quick-add logging

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 19: Photo-AI capture and confirm-estimate flow

**Files:**
- Modify: `src/app/meal-tracker/camera.tsx`
- Create: `src/app/meal-tracker/confirm-estimate.tsx`
- Modify: `src/app/meal-tracker/_layout.tsx` (register the new screen)

**Interfaces:**
- Consumes: `estimateFromPhoto`, `createEntry` (Task 16).

- [ ] **Step 1: Install the image picker dependency**

```bash
npx expo install expo-image-picker
```

- [ ] **Step 2: Implement the camera capture screen**

`src/app/meal-tracker/camera.tsx`:
```tsx
import * as ImagePicker from "expo-image-picker";
import { useRouter, type Href } from "expo-router";
import { useEffect } from "react";
import { SafeAreaView, Text } from "react-native";

export default function CameraScreen() {
  const router = useRouter();

  useEffect(() => {
    (async () => {
      const permission = await ImagePicker.requestCameraPermissionsAsync();
      if (!permission.granted) {
        router.back();
        return;
      }

      const result = await ImagePicker.launchCameraAsync({ quality: 0.7 });
      if (result.canceled) {
        router.back();
        return;
      }

      router.replace({
        pathname: "/meal-tracker/confirm-estimate" as Href,
        params: { photoUri: result.assets[0].uri },
      });
    })();
  }, [router]);

  return (
    <SafeAreaView style={{ flex: 1, justifyContent: "center", alignItems: "center" }}>
      <Text>Opening camera…</Text>
    </SafeAreaView>
  );
}
```

- [ ] **Step 3: Implement the confirm-estimate screen**

`src/app/meal-tracker/confirm-estimate.tsx`:
```tsx
import { useLocalSearchParams, useRouter } from "expo-router";
import { useEffect, useState } from "react";
import { Button, Image, SafeAreaView, Text, TextInput, View } from "react-native";

import { createEntry, estimateFromPhoto } from "@/modules/meal_tracker/api";
import type { PhotoEstimate } from "@/modules/meal_tracker/types";

export default function ConfirmEstimateScreen() {
  const router = useRouter();
  const { photoUri } = useLocalSearchParams<{ photoUri: string }>();
  const [estimate, setEstimate] = useState<PhotoEstimate | null>(null);
  const [calories, setCalories] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const result = await estimateFromPhoto(photoUri);
        setEstimate(result);
        setCalories(String(Math.round(result.calories)));
      } catch (err) {
        setError(err instanceof Error ? err.message : "estimate failed");
      }
    })();
  }, [photoUri]);

  const confirm = async () => {
    if (!estimate) return;
    await createEntry({
      meal_slot: "snack",
      source: "photo_ai",
      logged_at: new Date().toISOString(),
      calories: Number(calories) || 0,
      protein_g: estimate.protein_g,
      carbs_g: estimate.carbs_g,
      fat_g: estimate.fat_g,
    });
    router.dismissAll();
  };

  return (
    <SafeAreaView style={{ flex: 1, padding: 16, gap: 12 }}>
      <Image source={{ uri: photoUri }} style={{ width: "100%", height: 240, borderRadius: 8 }} />
      {error ? <Text style={{ color: "red" }}>{error}</Text> : null}
      {estimate ? (
        <View style={{ gap: 8 }}>
          <Text>{estimate.description}</Text>
          <Text>Confidence: {Math.round(estimate.confidence * 100)}%</Text>
          <Text>Calories (edit if needed):</Text>
          <TextInput
            keyboardType="numeric"
            value={calories}
            onChangeText={setCalories}
            style={{ borderWidth: 1, padding: 12, borderRadius: 8 }}
          />
          <Button title="Log This Meal" onPress={confirm} />
        </View>
      ) : (
        <Text>Estimating…</Text>
      )}
    </SafeAreaView>
  );
}
```

- [ ] **Step 4: Register the new screen in the meal-tracker stack**

`src/app/meal-tracker/_layout.tsx`:
```tsx
import { Stack } from "expo-router";

export default function MealTrackerLayout() {
  return (
    <Stack>
      <Stack.Screen name="index" options={{ title: "Meal Tracker" }} />
      <Stack.Screen name="add-entry" options={{ title: "Add Entry" }} />
      <Stack.Screen name="camera" options={{ title: "Calorie Camera" }} />
      <Stack.Screen name="confirm-estimate" options={{ title: "Confirm Estimate" }} />
    </Stack>
  );
}
```

- [ ] **Step 5: Manual verification**

```bash
npx expo start
```
From `/meal-tracker/add-entry`, tap "Take a Photo", grant camera permission, take a photo of anything. Confirm it navigates to the confirm-estimate screen, shows "Estimating…" then a filled-in calorie/macro estimate (the backend's `FakeNutritionEstimator` unless `ANTHROPIC_API_KEY` is configured), edit the calorie field, tap "Log This Meal", and confirm it returns to the diary with a new entry and updated totals.

- [ ] **Step 6: Commit**

```bash
git add package.json package-lock.json src/app/meal-tracker
git commit -m "$(cat <<'EOF'
Wire camera capture through photo-AI estimate to a confirm-and-log screen

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Self-Review Notes

- **Spec coverage:** Platform spec's auth (password + OAuth), JWT conventions, repository/Cosmos pattern, and client structure are covered by Tasks 1-15. Meal-tracker spec's food search, diary CRUD, and editable photo-AI estimate are covered by Tasks 6-8 and 16-19. Explicitly deferred (per the spec's own "open assumptions" and this plan's Global Constraints): barcode scanning, custom user-created foods/recipes, live Open Food Facts integration, calculated daily goals — none of these are silently dropped, they're named as follow-up work.
- **Type consistency:** `MealEntryInput`/`MealEntryCreate` field names match between backend (`meal_slot`, `source`, `logged_at`, `food_id`, `calories`, `protein_g`, `carbs_g`, `fat_g`) and client types across Tasks 7, 16, 18, 19. `PhotoEstimateOut`/`PhotoEstimate` fields match between Task 8 and Task 16/19.
- **Ownership/security:** every meals endpoint requires `get_current_user_id`; entry read/update/delete all re-check `user_id` inside the repository layer before returning data, tested explicitly in Task 7.
