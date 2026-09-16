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
