from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import settings
from .db.cosmos import CosmosMealEntryRepository, CosmosUserRepository, get_cosmos_client
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
    if settings.db_backend == "cosmos":
        return CosmosUserRepository(get_cosmos_client(), settings.cosmos_database_name)
    return _memory_user_repo


def get_meal_entry_repo():
    if settings.db_backend == "cosmos":
        return CosmosMealEntryRepository(get_cosmos_client(), settings.cosmos_database_name)
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
