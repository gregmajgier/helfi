import math
from datetime import date, datetime, timedelta, timezone
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Path, Query, UploadFile, status

from ..deps import get_current_user_id, get_favorite_repo, get_food_repo, get_meal_entry_repo
from ..ratelimit import estimate_limiter
from . import nutrition
from .models import (
    NUTRIENT_FIELDS,
    CopyEntriesIn,
    DayTotals,
    FoodCreate,
    FoodOut,
    FoodUpdate,
    LogFoodIn,
    MealDescriptionIn,
    MealEntryCreate,
    MealEntryOut,
    MealEntryUpdate,
    PhotoEstimateOut,
    StatsOut,
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


MAX_STATS_DAYS = 92
MAX_COPY_ENTRIES = 100
RECENT_WINDOW_DAYS = 60
MAX_FAVORITES = 200


async def _accessible_food(food_repo, food_id: str, user_id: str) -> dict:
    food = await food_repo.get(food_id)
    if not food or food.get("created_by_user_id") not in (None, user_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="food not found")
    return food


@router.get("/foods/search", response_model=list[FoodOut])
async def search_foods(
    q: str = Query(min_length=2, max_length=80),
    user_id: str = Depends(get_current_user_id),
    food_repo=Depends(get_food_repo),
):
    return await food_repo.search(q, user_id)


@router.get("/foods/mine", response_model=list[FoodOut])
async def list_my_foods(
    user_id: str = Depends(get_current_user_id),
    food_repo=Depends(get_food_repo),
):
    return await food_repo.list_for_user(user_id)


@router.get("/foods/favorites", response_model=list[FoodOut])
async def list_favorites(
    user_id: str = Depends(get_current_user_id),
    food_repo=Depends(get_food_repo),
    favorite_repo=Depends(get_favorite_repo),
):
    favorites = await favorite_repo.list_for_user(user_id, field="created_at")
    foods = []
    for favorite in reversed(favorites):
        food = await food_repo.get(favorite["food_id"])
        if food and food.get("created_by_user_id") in (None, user_id):
            foods.append(food)
    return foods


@router.put("/foods/{food_id}/favorite", status_code=status.HTTP_204_NO_CONTENT)
async def add_favorite(
    food_id: str,
    user_id: str = Depends(get_current_user_id),
    food_repo=Depends(get_food_repo),
    favorite_repo=Depends(get_favorite_repo),
):
    await _accessible_food(food_repo, food_id, user_id)
    if len(await favorite_repo.list_for_user(user_id)) >= MAX_FAVORITES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="too many favorites")
    await favorite_repo.put({"id": f"{user_id}:{food_id}", "user_id": user_id, "food_id": food_id})


@router.delete("/foods/{food_id}/favorite", status_code=status.HTTP_204_NO_CONTENT)
async def remove_favorite(
    food_id: str,
    user_id: str = Depends(get_current_user_id),
    favorite_repo=Depends(get_favorite_repo),
):
    await favorite_repo.delete(user_id, f"{user_id}:{food_id}")


OPEN_FOOD_FACTS_URL = "https://world.openfoodfacts.org/api/v2/product/{barcode}.json"


# Open Food Facts is crowd-edited. Anything we cache from it becomes a shared food served to every
# user, so values are range-checked per 100 g before being stored. Bad products are treated as not found.
_OFF_MAX_NAME_LENGTH = 120
_OFF_MAX_KCAL_PER_100G = 900  # pure fat is about 900
_OFF_MAX_GRAMS_PER_100G = 100
_OFF_MAX_SODIUM_G_PER_100G = 40  # pure salt is about 39 g sodium per 100 g


def _off_number(nutriments: dict, key: str, maximum: float, required: bool = False) -> Optional[float]:
    """A finite, non-negative number within `maximum`, 0 when absent, None when present but invalid."""
    value = nutriments.get(key)
    if value is None:
        return None if required else 0.0
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    if not math.isfinite(number) or number < 0 or number > maximum:
        return None
    return number


def _food_from_open_food_facts(product, barcode: str) -> Optional[dict]:
    if not isinstance(product, dict):
        return None
    nutriments = product.get("nutriments")
    if not isinstance(nutriments, dict):
        return None
    raw_name = product.get("product_name") or product.get("generic_name")
    if not isinstance(raw_name, str):
        return None
    name = " ".join(raw_name.split())
    if not name or len(name) > _OFF_MAX_NAME_LENGTH or not name.isprintable():
        return None

    calories = _off_number(nutriments, "energy-kcal_100g", _OFF_MAX_KCAL_PER_100G, required=True)
    protein = _off_number(nutriments, "proteins_100g", _OFF_MAX_GRAMS_PER_100G)
    carbs = _off_number(nutriments, "carbohydrates_100g", _OFF_MAX_GRAMS_PER_100G)
    fat = _off_number(nutriments, "fat_100g", _OFF_MAX_GRAMS_PER_100G)
    fiber = _off_number(nutriments, "fiber_100g", _OFF_MAX_GRAMS_PER_100G)
    sugar = _off_number(nutriments, "sugars_100g", _OFF_MAX_GRAMS_PER_100G)
    saturated = _off_number(nutriments, "saturated-fat_100g", _OFF_MAX_GRAMS_PER_100G)
    # Open Food Facts reports sodium in grams per 100 g.
    sodium_g = _off_number(nutriments, "sodium_100g", _OFF_MAX_SODIUM_G_PER_100G)
    values = [calories, protein, carbs, fat, fiber, sugar, saturated, sodium_g]
    if any(v is None for v in values):
        return None
    # 100 g cannot hold more than ~100 g of macros (small slack for rounding in the source data).
    if protein + carbs + fat > _OFF_MAX_GRAMS_PER_100G * 1.05:
        return None

    return {
        "name": name,
        "serving_size": 100,
        "serving_unit": "g",
        "calories_per_serving": calories,
        "protein_g": protein,
        "carbs_g": carbs,
        "fat_g": fat,
        "fiber_g": fiber,
        "sugar_g": sugar,
        "saturated_fat_g": saturated,
        "sodium_mg": round(sodium_g * 1000, 1),
        "barcode": barcode,
        "created_by_user_id": None,
    }


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

    try:
        payload = response.json()
    except ValueError:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="barcode lookup unavailable")
    if response.status_code != 200 or not isinstance(payload, dict) or payload.get("status") != 1:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="product not found")

    food = _food_from_open_food_facts(payload.get("product"), barcode)
    if food is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="product missing nutrition data")
    return await food_repo.create(food)


@router.get("/foods/{food_id}", response_model=FoodOut)
async def get_food(
    food_id: str,
    user_id: str = Depends(get_current_user_id),
    food_repo=Depends(get_food_repo),
):
    return await _accessible_food(food_repo, food_id, user_id)


@router.patch("/foods/{food_id}", response_model=FoodOut)
async def update_custom_food(
    food_id: str,
    body: FoodUpdate,
    user_id: str = Depends(get_current_user_id),
    food_repo=Depends(get_food_repo),
):
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    updated = await food_repo.update(food_id, user_id, updates)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="food not found")
    return updated


@router.delete("/foods/{food_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_custom_food(
    food_id: str,
    user_id: str = Depends(get_current_user_id),
    food_repo=Depends(get_food_repo),
    favorite_repo=Depends(get_favorite_repo),
):
    if not await food_repo.delete(food_id, user_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="food not found")
    await favorite_repo.delete(user_id, f"{user_id}:{food_id}")


def _entry_day(entry: dict) -> str:
    return entry.get("day") or entry["logged_at"][:10]


@router.post("/entries", response_model=MealEntryOut, status_code=status.HTTP_201_CREATED)
async def create_entry(
    body: MealEntryCreate,
    user_id: str = Depends(get_current_user_id),
    meal_entry_repo=Depends(get_meal_entry_repo),
):
    data = body.model_dump(mode="json")
    data["day"] = data["day"] or data["logged_at"][:10]
    return await meal_entry_repo.create({**data, "user_id": user_id})


@router.post("/entries/from-food", response_model=MealEntryOut, status_code=status.HTTP_201_CREATED)
async def log_food(
    body: LogFoodIn,
    user_id: str = Depends(get_current_user_id),
    food_repo=Depends(get_food_repo),
    meal_entry_repo=Depends(get_meal_entry_repo),
):
    food = await _accessible_food(food_repo, body.food_id, user_id)
    logged_at = body.logged_at or datetime.now(timezone.utc)
    source = "custom" if food.get("created_by_user_id") else ("barcode" if food.get("barcode") else "search")
    entry = {
        "user_id": user_id,
        "meal_slot": body.meal_slot,
        "source": source,
        "logged_at": logged_at.isoformat(),
        "day": body.day.isoformat(),
        "food_id": food["id"],
        "name": food["name"],
        "amount": body.amount,
        "unit": food["serving_unit"],
        **nutrition.nutrients_for_amount(food, body.amount),
    }
    return await meal_entry_repo.create(entry)


@router.get("/entries", response_model=list[MealEntryOut])
async def list_entries(
    day: date,
    user_id: str = Depends(get_current_user_id),
    meal_entry_repo=Depends(get_meal_entry_repo),
):
    return await meal_entry_repo.list_for_day(user_id, day)


@router.post("/entries/copy", response_model=list[MealEntryOut], status_code=status.HTTP_201_CREATED)
async def copy_entries(
    body: CopyEntriesIn,
    user_id: str = Depends(get_current_user_id),
    meal_entry_repo=Depends(get_meal_entry_repo),
):
    source = await meal_entry_repo.list_for_day(user_id, body.from_day)
    if body.from_slot:
        source = [e for e in source if e["meal_slot"] == body.from_slot]
    if len(source) > MAX_COPY_ENTRIES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="too many entries to copy")
    copies = []
    for entry in source:
        clone = {
            k: v
            for k, v in entry.items()
            if k not in ("id", "created_at", "updated_at")
        }
        clone["day"] = body.to_day.isoformat()
        clone["logged_at"] = f"{body.to_day.isoformat()}{entry['logged_at'][10:]}"
        if body.to_slot:
            clone["meal_slot"] = body.to_slot
        copies.append(await meal_entry_repo.create(clone))
    return copies


@router.get("/entries/recent", response_model=list[MealEntryOut])
async def recent_entries(
    limit: int = Query(default=20, ge=1, le=50),
    today: date | None = None,
    user_id: str = Depends(get_current_user_id),
    meal_entry_repo=Depends(get_meal_entry_repo),
):
    """Most recently logged distinct foods, newest first, for one-tap re-logging."""
    end = today or datetime.now(timezone.utc).date()
    entries = await meal_entry_repo.list_range(user_id, end - timedelta(days=RECENT_WINDOW_DAYS), end)
    seen, recent = set(), []
    for entry in sorted(entries, key=lambda e: e["logged_at"], reverse=True):
        if not entry.get("name"):
            continue
        key = entry.get("food_id") or entry["name"].lower()
        if key in seen:
            continue
        seen.add(key)
        recent.append(entry)
        if len(recent) >= limit:
            break
    return recent


@router.get("/entries/stats", response_model=StatsOut)
async def entry_stats(
    start: date,
    end: date,
    user_id: str = Depends(get_current_user_id),
    meal_entry_repo=Depends(get_meal_entry_repo),
):
    if end < start or (end - start).days >= MAX_STATS_DAYS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid date range")
    entries = await meal_entry_repo.list_range(user_id, start, end)
    by_day: dict[str, dict] = {}
    for entry in entries:
        bucket = by_day.setdefault(_entry_day(entry), {**nutrition.empty(), "entries": 0})
        for field in NUTRIENT_FIELDS:
            bucket[field] += float(entry.get(field, 0) or 0)
        bucket["entries"] += 1
    days = []
    cursor = start
    while cursor <= end:
        bucket = by_day.get(cursor.isoformat(), {**nutrition.empty(), "entries": 0})
        days.append(DayTotals(day=cursor, **{k: round(v, 1) for k, v in bucket.items()}))
        cursor += timedelta(days=1)
    logged = [d for d in days if d.entries > 0]
    n = len(logged) or 1
    return StatsOut(
        start=start,
        end=end,
        days=days,
        logged_days=len(logged),
        average_calories=round(sum(d.calories for d in logged) / n, 1),
        average_protein_g=round(sum(d.protein_g for d in logged) / n, 1),
        average_carbs_g=round(sum(d.carbs_g for d in logged) / n, 1),
        average_fat_g=round(sum(d.fat_g for d in logged) / n, 1),
    )


@router.patch("/entries/{entry_id}", response_model=MealEntryOut)
async def update_entry(
    entry_id: str,
    body: MealEntryUpdate,
    user_id: str = Depends(get_current_user_id),
    meal_entry_repo=Depends(get_meal_entry_repo),
):
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if "amount" in updates:
        current = await meal_entry_repo.get(user_id, entry_id)
        if not current:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="entry not found")
        old_amount = current.get("amount")
        if not old_amount:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="entry has no amount to scale")
        scaled = nutrition.scale(current, updates["amount"] / old_amount)
        # Explicit nutrient values in the same request win over the scaled ones.
        updates = {**scaled, **updates}
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
