from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import settings
from .db.cosmos import (
    CosmosDocRepository,
    CosmosExerciseRepository,
    CosmosFoodRepository,
    CosmosJournalEntryRepository,
    CosmosMealEntryRepository,
    CosmosMoodEntryRepository,
    CosmosScreenTimeRuleRepository,
    CosmosScreenTimeUsageRepository,
    CosmosUserRepository,
    CosmosWorkoutRepository,
    get_cosmos_client,
)
from .db.memory import (
    SEED_EXERCISES,
    SEED_FOODS,
    InMemoryDocRepository,
    InMemoryExerciseRepository,
    InMemoryFoodRepository,
    InMemoryJournalEntryRepository,
    InMemoryMealEntryRepository,
    InMemoryMoodEntryRepository,
    InMemoryScreenTimeRuleRepository,
    InMemoryScreenTimeUsageRepository,
    InMemoryUserRepository,
    InMemoryWorkoutRepository,
)
from .security import decode_token

bearer_scheme = HTTPBearer()

_memory_user_repo = InMemoryUserRepository()
_memory_meal_entry_repo = InMemoryMealEntryRepository()
_food_repo = InMemoryFoodRepository(SEED_FOODS)
_memory_workout_repo = InMemoryWorkoutRepository()
_exercise_repo = InMemoryExerciseRepository(SEED_EXERCISES)
_memory_mood_entry_repo = InMemoryMoodEntryRepository()
_memory_journal_entry_repo = InMemoryJournalEntryRepository()
_memory_screentime_rule_repo = InMemoryScreenTimeRuleRepository()
_memory_screentime_usage_repo = InMemoryScreenTimeUsageRepository()

_memory_doc_repos: dict[str, InMemoryDocRepository] = {}


def _doc_repo(container_name: str):
    if settings.db_backend == "cosmos":
        return CosmosDocRepository(get_cosmos_client(), settings.cosmos_database_name, container_name)
    return _memory_doc_repos.setdefault(container_name, InMemoryDocRepository())


def get_profile_repo():
    return _doc_repo("profiles")


def get_weight_repo():
    return _doc_repo("weight_entries")


def get_favorite_repo():
    return _doc_repo("favorites")


def get_recipe_repo():
    return _doc_repo("recipes")


def get_plan_repo():
    return _doc_repo("meal_plan")


def get_shopping_repo():
    return _doc_repo("shopping_items")


def get_water_repo():
    return _doc_repo("water_entries")


def get_fasting_repo():
    return _doc_repo("fasting_sessions")


def get_user_repo():
    if settings.db_backend == "cosmos":
        return CosmosUserRepository(get_cosmos_client(), settings.cosmos_database_name)
    return _memory_user_repo


def get_meal_entry_repo():
    if settings.db_backend == "cosmos":
        return CosmosMealEntryRepository(get_cosmos_client(), settings.cosmos_database_name)
    return _memory_meal_entry_repo


def get_food_repo():
    if settings.db_backend == "cosmos":
        return CosmosFoodRepository(get_cosmos_client(), settings.cosmos_database_name)
    return _food_repo


def get_workout_repo():
    if settings.db_backend == "cosmos":
        return CosmosWorkoutRepository(get_cosmos_client(), settings.cosmos_database_name)
    return _memory_workout_repo


def get_exercise_repo():
    if settings.db_backend == "cosmos":
        return CosmosExerciseRepository(get_cosmos_client(), settings.cosmos_database_name)
    return _exercise_repo


def get_mood_entry_repo():
    if settings.db_backend == "cosmos":
        return CosmosMoodEntryRepository(get_cosmos_client(), settings.cosmos_database_name)
    return _memory_mood_entry_repo


def get_journal_entry_repo():
    if settings.db_backend == "cosmos":
        return CosmosJournalEntryRepository(get_cosmos_client(), settings.cosmos_database_name)
    return _memory_journal_entry_repo


def get_screentime_rule_repo():
    if settings.db_backend == "cosmos":
        return CosmosScreenTimeRuleRepository(get_cosmos_client(), settings.cosmos_database_name)
    return _memory_screentime_rule_repo


def get_screentime_usage_repo():
    if settings.db_backend == "cosmos":
        return CosmosScreenTimeUsageRepository(get_cosmos_client(), settings.cosmos_database_name)
    return _memory_screentime_usage_repo


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> str:
    try:
        return decode_token(credentials.credentials, settings.jwt_secret, "access")
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid or expired token"
        )
