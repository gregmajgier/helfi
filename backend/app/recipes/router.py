from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..deps import get_current_user_id, get_meal_entry_repo, get_recipe_repo
from ..meals import nutrition
from ..meals.models import MealEntryOut, MealSlot
from .models import LogRecipeIn, RecipeIn, RecipeOut
from .service import CURATED, load_recipe, present

router = APIRouter()

MAX_USER_RECIPES = 300


def _not_found():
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="recipe not found")


def _body(recipe: RecipeIn, user_id: str) -> dict:
    return {**recipe.model_dump(mode="json"), "user_id": user_id}


@router.get("", response_model=list[RecipeOut])
async def list_recipes(
    q: Optional[str] = Query(default=None, max_length=80),
    meal_type: Optional[MealSlot] = None,
    mine: bool = False,
    user_id: str = Depends(get_current_user_id),
    recipe_repo=Depends(get_recipe_repo),
):
    own = [present(r) for r in await recipe_repo.list_for_user(user_id)]
    recipes = own if mine else own + list(CURATED.values())
    if q:
        recipes = [r for r in recipes if q.lower() in r["name"].lower()]
    if meal_type:
        recipes = [r for r in recipes if meal_type in r["meal_types"]]
    return sorted(recipes, key=lambda r: (r["curated"], r["name"].lower()))


@router.post("", response_model=RecipeOut, status_code=status.HTTP_201_CREATED)
async def create_recipe(
    body: RecipeIn,
    user_id: str = Depends(get_current_user_id),
    recipe_repo=Depends(get_recipe_repo),
):
    if len(await recipe_repo.list_for_user(user_id)) >= MAX_USER_RECIPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="recipe limit reached")
    return present(await recipe_repo.create(_body(body, user_id)))


@router.get("/{recipe_id}", response_model=RecipeOut)
async def get_recipe(
    recipe_id: str,
    user_id: str = Depends(get_current_user_id),
    recipe_repo=Depends(get_recipe_repo),
):
    recipe = await load_recipe(recipe_repo, user_id, recipe_id)
    if not recipe:
        raise _not_found()
    return recipe


@router.put("/{recipe_id}", response_model=RecipeOut)
async def replace_recipe(
    recipe_id: str,
    body: RecipeIn,
    user_id: str = Depends(get_current_user_id),
    recipe_repo=Depends(get_recipe_repo),
):
    if recipe_id in CURATED:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="curated recipes are read-only")
    updated = await recipe_repo.update(user_id, recipe_id, _body(body, user_id))
    if not updated:
        raise _not_found()
    return present(updated)


@router.delete("/{recipe_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_recipe(
    recipe_id: str,
    user_id: str = Depends(get_current_user_id),
    recipe_repo=Depends(get_recipe_repo),
):
    if recipe_id in CURATED:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="curated recipes are read-only")
    if not await recipe_repo.delete(user_id, recipe_id):
        raise _not_found()


@router.post("/{recipe_id}/copy", response_model=RecipeOut, status_code=status.HTTP_201_CREATED)
async def copy_recipe(
    recipe_id: str,
    user_id: str = Depends(get_current_user_id),
    recipe_repo=Depends(get_recipe_repo),
):
    source = await load_recipe(recipe_repo, user_id, recipe_id)
    if not source:
        raise _not_found()
    data = RecipeIn(**{k: source[k] for k in RecipeIn.model_fields})
    return present(await recipe_repo.create(_body(data, user_id)))


@router.post("/{recipe_id}/log", response_model=MealEntryOut, status_code=status.HTTP_201_CREATED)
async def log_recipe(
    recipe_id: str,
    body: LogRecipeIn,
    user_id: str = Depends(get_current_user_id),
    recipe_repo=Depends(get_recipe_repo),
    meal_entry_repo=Depends(get_meal_entry_repo),
):
    recipe = await load_recipe(recipe_repo, user_id, recipe_id)
    if not recipe:
        raise _not_found()
    logged_at = body.logged_at or datetime.now(timezone.utc)
    entry = {
        "user_id": user_id,
        "meal_slot": body.meal_slot,
        "source": "recipe",
        "logged_at": logged_at.isoformat(),
        "day": body.day.isoformat(),
        "name": recipe["name"],
        "amount": body.servings,
        "unit": "serving",
        **nutrition.scale(recipe["per_serving"], body.servings),
    }
    return await meal_entry_repo.create(entry)
