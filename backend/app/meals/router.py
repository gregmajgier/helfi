from datetime import date

import httpx
from fastapi import APIRouter, Depends, HTTPException, Path, UploadFile, status

from ..deps import get_current_user_id, get_food_repo, get_meal_entry_repo
from ..ratelimit import estimate_limiter
from .models import (
    FoodCreate,
    FoodOut,
    MealDescriptionIn,
    MealEntryCreate,
    MealEntryOut,
    MealEntryUpdate,
    PhotoEstimateOut,
)
from .nutrition_estimator import get_nutrition_estimator

router = APIRouter()


@router.post("/foods", response_model=FoodOut, status_code=status.HTTP_201_CREATED)
async def create_custom_food(
    body: FoodCreate,
    user_id: str = Depends(get_current_user_id),
    food_repo=Depends(get_food_repo),
):
    # barcode is never client-writable here: it would let a user's custom food
    # shadow or poison a real product's barcode for every other user who later
    # scans it. Barcodes only ever come from our own seed data or a verified
    # Open Food Facts lookup (see lookup_barcode below).
    data = body.model_dump()
    data.pop("barcode", None)
    return await food_repo.create({**data, "barcode": None, "created_by_user_id": user_id})


OPEN_FOOD_FACTS_URL = "https://world.openfoodfacts.org/api/v2/product/{barcode}.json"


@router.get("/foods/barcode/{barcode}", response_model=FoodOut)
async def lookup_barcode(
    barcode: str = Path(pattern=r"^\d{8,14}$"),
    user_id: str = Depends(get_current_user_id),
    food_repo=Depends(get_food_repo),
):
    local = await food_repo.get_by_barcode(barcode)
    if local:
        return local

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(OPEN_FOOD_FACTS_URL.format(barcode=barcode))
    except httpx.HTTPError:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="barcode lookup unavailable")

    payload = response.json()
    if response.status_code != 200 or payload.get("status") != 1:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="product not found")

    product = payload["product"]
    nutriments = product.get("nutriments", {})
    name = product.get("product_name") or product.get("generic_name")
    calories = nutriments.get("energy-kcal_100g")
    if not name or calories is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="product missing nutrition data")

    food = {
        "name": name,
        "serving_size": 100,
        "serving_unit": "g",
        "calories_per_serving": calories,
        "protein_g": nutriments.get("proteins_100g", 0) or 0,
        "carbs_g": nutriments.get("carbohydrates_100g", 0) or 0,
        "fat_g": nutriments.get("fat_100g", 0) or 0,
        "barcode": barcode,
        "created_by_user_id": None,
    }
    return await food_repo.create(food)


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
    estimate_limiter.check(user_id)
    content_type = photo.content_type or "image/jpeg"
    if content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="unsupported image type")
    estimator = get_nutrition_estimator()
    image_bytes = await photo.read()
    if len(image_bytes) > MAX_PHOTO_BYTES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="photo too large")
    return await estimator.estimate(image_bytes, content_type)


@router.post("/estimate-from-description", response_model=PhotoEstimateOut)
async def estimate_from_description(
    body: MealDescriptionIn,
    user_id: str = Depends(get_current_user_id),
):
    estimate_limiter.check(user_id)
    if not body.description.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="description is required")
    estimator = get_nutrition_estimator()
    return await estimator.estimate_from_text(body.description)
