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
