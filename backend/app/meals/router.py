from datetime import date

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status

from ..deps import get_current_user_id, get_food_repo, get_meal_entry_repo
from .models import FoodOut, MealEntryCreate, MealEntryOut, MealEntryUpdate, PhotoEstimateOut
from .nutrition_estimator import get_nutrition_estimator

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


ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_PHOTO_BYTES = 10 * 1024 * 1024


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
    if len(image_bytes) > MAX_PHOTO_BYTES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="photo too large")
    return await estimator.estimate(image_bytes, content_type)
