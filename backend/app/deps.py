from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import settings
from .db.cosmos import (
    CosmosFoodRepository,
    CosmosMealEntryRepository,
    CosmosUserRepository,
    get_cosmos_client,
)
from .db.memory import (
    SEED_EXERCISES,
    SEED_FOODS,
    InMemoryExerciseRepository,
    InMemoryFoodRepository,
    InMemoryMealEntryRepository,
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
    return _memory_workout_repo


def get_exercise_repo():
    return _exercise_repo


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> str:
    try:
        return decode_token(credentials.credentials, settings.jwt_secret, "access")
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid or expired token"
        )
