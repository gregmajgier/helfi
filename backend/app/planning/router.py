from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..deps import (
    get_current_user_id,
    get_food_repo,
    get_meal_entry_repo,
    get_plan_repo,
    get_profile_repo,
    get_recipe_repo,
    get_shopping_repo,
)
from ..meals import nutrition
from ..meals.models import MealEntryOut
from ..profile.calc import compute_targets
from ..recipes.service import CURATED, load_recipe, present
from . import generator
from .models import (
    ApplyPlanIn,
    DateRangeIn,
    GeneratePlanIn,
    PlanItemIn,
    PlanItemOut,
    ShoppingItemIn,
    ShoppingItemOut,
    ShoppingPatch,
)

plan_router = APIRouter()
shopping_router = APIRouter()

MAX_RANGE_DAYS = 31
MAX_PLAN_ITEMS = 600
MAX_SHOPPING_ITEMS = 300
DEFAULT_CALORIES = 2000


def _check_range(start: date, end: date) -> None:
    if end < start or (end - start).days >= MAX_RANGE_DAYS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid date range")


def _scaled_ingredients(recipe: dict, servings: float) -> list[dict]:
    factor = servings / recipe["servings"]
    return [
        {"name": i["name"], "amount": round(i["amount"] * factor, 1), "unit": i["unit"]}
        for i in recipe["ingredients"]
    ]


def _recipe_item(user_id: str, day: date, slot: str, recipe: dict, servings: float) -> dict:
    return {
        "user_id": user_id,
        "day": day.isoformat(),
        "meal_slot": slot,
        "name": recipe["name"],
        "recipe_id": recipe["id"],
        "food_id": None,
        "amount": servings,
        "unit": "serving",
        **nutrition.scale(recipe["per_serving"], servings),
        "ingredients": _scaled_ingredients(recipe, servings),
    }


def _sorted(items: list[dict]) -> list[dict]:
    order = {slot: i for i, slot in enumerate(generator.SLOT_ORDER)}
    return sorted(items, key=lambda i: (i["day"], order[i["meal_slot"]], i["created_at"]))


async def _range(plan_repo, user_id: str, start: date, end: date) -> list[dict]:
    return _sorted(
        await plan_repo.list_for_user(user_id, field="day", gte=start.isoformat(), lte=end.isoformat())
    )


@plan_router.get("", response_model=list[PlanItemOut])
async def get_plan(
    start: date,
    end: date,
    user_id: str = Depends(get_current_user_id),
    plan_repo=Depends(get_plan_repo),
):
    _check_range(start, end)
    return await _range(plan_repo, user_id, start, end)


@plan_router.post("", response_model=PlanItemOut, status_code=status.HTTP_201_CREATED)
async def add_plan_item(
    body: PlanItemIn,
    user_id: str = Depends(get_current_user_id),
    plan_repo=Depends(get_plan_repo),
    recipe_repo=Depends(get_recipe_repo),
    food_repo=Depends(get_food_repo),
):
    if len(await plan_repo.list_for_user(user_id)) >= MAX_PLAN_ITEMS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="plan is full")
    if body.recipe_id:
        recipe = await load_recipe(recipe_repo, user_id, body.recipe_id)
        if not recipe:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="recipe not found")
        item = _recipe_item(user_id, body.day, body.meal_slot, recipe, body.servings)
    else:
        food = await food_repo.get(body.food_id)
        if not food or food.get("created_by_user_id") not in (None, user_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="food not found")
        item = {
            "user_id": user_id,
            "day": body.day.isoformat(),
            "meal_slot": body.meal_slot,
            "name": food["name"],
            "recipe_id": None,
            "food_id": food["id"],
            "amount": body.amount,
            "unit": food["serving_unit"],
            **nutrition.nutrients_for_amount(food, body.amount),
            "ingredients": [{"name": food["name"], "amount": body.amount, "unit": food["serving_unit"]}],
        }
    return await plan_repo.create(item)


@plan_router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_plan_item(
    item_id: str, user_id: str = Depends(get_current_user_id), plan_repo=Depends(get_plan_repo)
):
    if not await plan_repo.delete(user_id, item_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="plan item not found")


@plan_router.post("/clear")
async def clear_plan(
    body: DateRangeIn,
    user_id: str = Depends(get_current_user_id),
    plan_repo=Depends(get_plan_repo),
):
    _check_range(body.start, body.end)
    items = await _range(plan_repo, user_id, body.start, body.end)
    for item in items:
        await plan_repo.delete(user_id, item["id"])
    return {"deleted": len(items)}


@plan_router.post("/apply", response_model=list[MealEntryOut], status_code=status.HTTP_201_CREATED)
async def apply_plan(
    body: ApplyPlanIn,
    user_id: str = Depends(get_current_user_id),
    plan_repo=Depends(get_plan_repo),
    meal_entry_repo=Depends(get_meal_entry_repo),
):
    """Copies the planned meals of a day (or one slot) into the diary."""
    items = await _range(plan_repo, user_id, body.day, body.day)
    if body.meal_slot:
        items = [i for i in items if i["meal_slot"] == body.meal_slot]
    noon = datetime.combine(body.day, datetime.min.time(), tzinfo=timezone.utc) + timedelta(hours=12)
    entries = []
    for item in items:
        entries.append(
            await meal_entry_repo.create(
                {
                    "user_id": user_id,
                    "meal_slot": item["meal_slot"],
                    "source": "plan",
                    "logged_at": noon.isoformat(),
                    "day": item["day"],
                    "food_id": item.get("food_id"),
                    "name": item["name"],
                    "amount": item["amount"],
                    "unit": item["unit"],
                    **{f: item.get(f, 0) for f in nutrition.NUTRIENT_FIELDS},
                }
            )
        )
    return entries


@plan_router.post("/generate", response_model=list[PlanItemOut], status_code=status.HTTP_201_CREATED)
async def generate_plan(
    body: GeneratePlanIn,
    user_id: str = Depends(get_current_user_id),
    plan_repo=Depends(get_plan_repo),
    recipe_repo=Depends(get_recipe_repo),
    profile_repo=Depends(get_profile_repo),
):
    end = body.start + timedelta(days=body.days - 1)
    calories = body.calorie_target
    if not calories:
        profile = await profile_repo.get(user_id, user_id)
        calories = (
            compute_targets(profile, datetime.now(timezone.utc).year)["calories"]
            if profile
            else DEFAULT_CALORIES
        )
    recipes = list(CURATED.values()) + [present(r) for r in await recipe_repo.list_for_user(user_id)]
    slots = generator.generate(recipes, body.start, body.days, calories)
    existing = await plan_repo.list_for_user(user_id)
    replaced = (
        [i for i in existing if body.start.isoformat() <= i["day"] <= end.isoformat()] if body.replace else []
    )
    # Check the cap before touching anything so a rejected request changes nothing.
    if len(existing) - len(replaced) + len(slots) > MAX_PLAN_ITEMS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="plan is full")
    for item in replaced:
        await plan_repo.delete(user_id, item["id"])
    created = []
    for slot in slots:
        created.append(
            await plan_repo.create(
                _recipe_item(user_id, slot["day"], slot["meal_slot"], slot["recipe"], slot["servings"])
            )
        )
    return _sorted(created)


# ---------------------------------------------------------------- shopping


def _key(name: str, unit: str | None) -> str:
    return f"{name.strip().lower()}|{(unit or '').strip().lower()}"


async def _shopping_list(shopping_repo, user_id: str) -> list[dict]:
    items = await shopping_repo.list_for_user(user_id)
    return sorted(items, key=lambda i: (i["checked"], i["name"].lower()))


@shopping_router.get("", response_model=list[ShoppingItemOut])
async def get_shopping_list(
    user_id: str = Depends(get_current_user_id), shopping_repo=Depends(get_shopping_repo)
):
    return await _shopping_list(shopping_repo, user_id)


@shopping_router.post("", response_model=ShoppingItemOut, status_code=status.HTTP_201_CREATED)
async def add_shopping_item(
    body: ShoppingItemIn,
    user_id: str = Depends(get_current_user_id),
    shopping_repo=Depends(get_shopping_repo),
):
    if len(await shopping_repo.list_for_user(user_id)) >= MAX_SHOPPING_ITEMS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="shopping list is full")
    return await shopping_repo.create(
        {
            "user_id": user_id,
            "name": body.name.strip(),
            "amount": body.amount,
            "unit": body.unit,
            "checked": False,
            "source": "manual",
            "key": _key(body.name, body.unit),
        }
    )


@shopping_router.post("/generate", response_model=list[ShoppingItemOut])
async def generate_shopping_list(
    body: DateRangeIn,
    user_id: str = Depends(get_current_user_id),
    plan_repo=Depends(get_plan_repo),
    shopping_repo=Depends(get_shopping_repo),
):
    """Rebuilds the plan-sourced part of the list; manual items and ticks survive."""
    _check_range(body.start, body.end)
    needed: dict[str, dict] = {}
    for plan_item in await _range(plan_repo, user_id, body.start, body.end):
        for ingredient in plan_item.get("ingredients", []):
            key = _key(ingredient["name"], ingredient["unit"])
            row = needed.setdefault(
                key, {"name": ingredient["name"], "unit": ingredient["unit"], "amount": 0.0}
            )
            row["amount"] += ingredient["amount"]

    existing = await shopping_repo.list_for_user(user_id)
    manual_count = sum(1 for i in existing if i["source"] != "plan")
    if manual_count + len(needed) > MAX_SHOPPING_ITEMS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="too many ingredients for one shopping list; choose a shorter date range",
        )
    ticked = {i["key"] for i in existing if i["source"] == "plan" and i["checked"]}
    for item in existing:
        if item["source"] == "plan":
            await shopping_repo.delete(user_id, item["id"])
    for key, row in needed.items():
        await shopping_repo.create(
            {
                "user_id": user_id,
                "name": row["name"],
                "unit": row["unit"],
                "amount": round(row["amount"], 1),
                "checked": key in ticked,
                "source": "plan",
                "key": key,
            }
        )
    return await _shopping_list(shopping_repo, user_id)


@shopping_router.post("/clear-checked", response_model=list[ShoppingItemOut])
async def clear_checked(
    user_id: str = Depends(get_current_user_id), shopping_repo=Depends(get_shopping_repo)
):
    for item in await shopping_repo.list_for_user(user_id):
        if item["checked"]:
            await shopping_repo.delete(user_id, item["id"])
    return await _shopping_list(shopping_repo, user_id)


@shopping_router.patch("/{item_id}", response_model=ShoppingItemOut)
async def check_shopping_item(
    item_id: str,
    body: ShoppingPatch,
    user_id: str = Depends(get_current_user_id),
    shopping_repo=Depends(get_shopping_repo),
):
    updated = await shopping_repo.update(user_id, item_id, {"checked": body.checked})
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="item not found")
    return updated


@shopping_router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_shopping_item(
    item_id: str,
    user_id: str = Depends(get_current_user_id),
    shopping_repo=Depends(get_shopping_repo),
):
    if not await shopping_repo.delete(user_id, item_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="item not found")
