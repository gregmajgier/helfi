"""Deterministic meal plan generator: fills each slot with the recipe whose
portion lands closest to that slot's share of the daily calorie target."""
from datetime import date, timedelta

SLOT_SHARE = {"breakfast": 0.25, "lunch": 0.35, "dinner": 0.30, "snack": 0.10}
SLOT_ORDER = ("breakfast", "lunch", "dinner", "snack")
REPEAT_WINDOW_DAYS = 3
MIN_SERVINGS, MAX_SERVINGS = 0.5, 2.5
# Every earlier use nudges a recipe down so the whole library gets rotated through.
USE_PENALTY = 0.08
RECENT_PENALTY = 0.6


def _portion(per_serving_kcal: float, slot_target: float) -> float:
    servings = round(slot_target / per_serving_kcal * 2) / 2
    return min(max(servings, MIN_SERVINGS), MAX_SERVINGS)


def generate(recipes: list[dict], start: date, days: int, daily_calories: float) -> list[dict]:
    """Returns [{day, meal_slot, recipe, servings}] in day/slot order."""
    ordered = sorted(recipes, key=lambda r: r["id"])
    plan: list[dict] = []
    used_on: dict[str, list[int]] = {}  # recipe id -> day indexes it was used
    for day_index in range(days):
        day = start + timedelta(days=day_index)
        for slot in SLOT_ORDER:
            candidates = [r for r in ordered if slot in r["meal_types"] and r["per_serving"]["calories"] > 0]
            if not candidates:
                continue
            slot_target = daily_calories * SLOT_SHARE[slot]
            best, best_score, best_servings = None, None, 1.0
            for index, recipe in enumerate(candidates):
                kcal = recipe["per_serving"]["calories"]
                servings = _portion(kcal, slot_target)
                error = abs(servings * kcal - slot_target) / slot_target
                recent = sum(1 for d in used_on.get(recipe["id"], []) if day_index - d <= REPEAT_WINDOW_DAYS)
                # The rotation term is tiny: it only breaks ties so days differ.
                rotation = ((index - day_index) % len(candidates)) * 0.001
                total_uses = len(used_on.get(recipe["id"], []))
                score = error + RECENT_PENALTY * (recent > 0) + USE_PENALTY * total_uses + rotation
                if best_score is None or score < best_score:
                    best, best_score, best_servings = recipe, score, servings
            used_on.setdefault(best["id"], []).append(day_index)
            plan.append({"day": day, "meal_slot": slot, "recipe": best, "servings": best_servings})
    return plan
