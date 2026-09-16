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
