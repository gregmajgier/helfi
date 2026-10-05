import json
from pathlib import Path
from typing import Optional

from ..meals import nutrition

_CURATED_PATH = Path(__file__).parent / "data" / "curated_recipes.json"


def _with_totals(recipe: dict, curated: bool) -> dict:
    totals = nutrition.total(recipe["ingredients"])
    per_serving = nutrition.scale(totals, 1 / recipe["servings"])
    return {**recipe, "curated": curated, "totals": totals, "per_serving": per_serving}


CURATED: dict[str, dict] = {
    r["id"]: _with_totals(r, True) for r in json.loads(_CURATED_PATH.read_text())
}


def present(recipe: dict) -> dict:
    """Stored (user) recipes get their totals recomputed from ingredients on every read."""
    return _with_totals(recipe, False)


async def load_recipe(recipe_repo, user_id: str, recipe_id: str) -> Optional[dict]:
    """A curated recipe or one of the user's own; None for anyone else's."""
    if recipe_id in CURATED:
        return CURATED[recipe_id]
    stored = await recipe_repo.get(user_id, recipe_id)
    return present(stored) if stored else None
