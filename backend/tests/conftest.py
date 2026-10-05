import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from fastapi.testclient import TestClient

from app import deps
from app.db.memory import (
    SEED_EXERCISES,
    SEED_FOODS,
    InMemoryDocRepository,
    InMemoryExerciseRepository,
    InMemoryFoodRepository,
    InMemoryJournalEntryRepository,
    InMemoryMealEntryRepository,
    InMemoryMoodEntryRepository,
    InMemoryScreenTimeRuleRepository,
    InMemoryUserRepository,
    InMemoryWorkoutRepository,
)
from app.main import app


def _provide(repo):
    # A real closure: a lambda default would be read by FastAPI as a query
    # parameter and deep-copied per request.
    return lambda: repo


@pytest.fixture()
def client():
    user_repo = InMemoryUserRepository()
    meal_entry_repo = InMemoryMealEntryRepository()
    food_repo = InMemoryFoodRepository(SEED_FOODS)
    workout_repo = InMemoryWorkoutRepository()
    exercise_repo = InMemoryExerciseRepository(SEED_EXERCISES)
    mood_entry_repo = InMemoryMoodEntryRepository()
    journal_entry_repo = InMemoryJournalEntryRepository()
    screentime_rule_repo = InMemoryScreenTimeRuleRepository()

    for getter in (
        deps.get_profile_repo,
        deps.get_weight_repo,
        deps.get_favorite_repo,
        deps.get_recipe_repo,
        deps.get_plan_repo,
        deps.get_shopping_repo,
        deps.get_water_repo,
        deps.get_fasting_repo,
    ):
        app.dependency_overrides[getter] = _provide(InMemoryDocRepository())

    app.dependency_overrides[deps.get_user_repo] = lambda: user_repo
    app.dependency_overrides[deps.get_meal_entry_repo] = lambda: meal_entry_repo
    app.dependency_overrides[deps.get_food_repo] = lambda: food_repo
    app.dependency_overrides[deps.get_workout_repo] = lambda: workout_repo
    app.dependency_overrides[deps.get_exercise_repo] = lambda: exercise_repo
    app.dependency_overrides[deps.get_mood_entry_repo] = lambda: mood_entry_repo
    app.dependency_overrides[deps.get_journal_entry_repo] = lambda: journal_entry_repo
    app.dependency_overrides[deps.get_screentime_rule_repo] = lambda: screentime_rule_repo

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


@pytest.fixture(autouse=True)
def _reset_rate_limiters():
    from app.ratelimit import estimate_limiter

    estimate_limiter.reset()
    yield
    estimate_limiter.reset()
