"""Calorie, macro and water targets. Pure functions, no I/O."""
from typing import Optional

ACTIVITY_MULTIPLIERS = {
    "sedentary": 1.2,
    "light": 1.375,
    "moderate": 1.55,
    "active": 1.725,
    "very_active": 1.9,
}

# kcal in a kilogram of body mass change, the usual planning figure.
KCAL_PER_KG = 7700
MIN_CALORIES = {"male": 1500, "female": 1200}

# (protein %, carbs %, fat %) of calories
DEFAULT_MACRO_SPLIT = {
    "lose": (30, 40, 30),
    "maintain": (25, 50, 25),
    "build": (30, 45, 25),
}


def bmr(sex: str, weight_kg: float, height_cm: float, age: int) -> float:
    """Mifflin-St Jeor."""
    return 10 * weight_kg + 6.25 * height_cm - 5 * age + (5 if sex == "male" else -161)


def daily_delta(goal: str, weekly_change_kg: float) -> float:
    if goal == "maintain":
        return 0.0
    magnitude = weekly_change_kg * KCAL_PER_KG / 7
    return -magnitude if goal == "lose" else magnitude


def water_goal_ml(weight_kg: float) -> int:
    ml = round(weight_kg * 35 / 50) * 50
    return max(1500, min(4000, ml))


def compute_targets(profile: dict, current_year: int) -> dict:
    age = current_year - profile["birth_year"]
    base = bmr(profile["sex"], profile["weight_kg"], profile["height_cm"], age)
    tdee = base * ACTIVITY_MULTIPLIERS[profile["activity_level"]]
    delta = daily_delta(profile["goal"], profile.get("weekly_change_kg") or 0)

    warnings: list[str] = []
    override: Optional[float] = profile.get("calorie_override")
    if override:
        calories = float(override)
    else:
        calories = tdee + delta
        floor = MIN_CALORIES[profile["sex"]]
        if calories < floor:
            calories = floor
            warnings.append(
                f"Target raised to {floor} kcal, the minimum we recommend without medical supervision."
            )
    calories = round(calories)

    split = profile.get("macro_split") or dict(
        zip(("protein_pct", "carbs_pct", "fat_pct"), DEFAULT_MACRO_SPLIT[profile["goal"]])
    )
    protein_g = round(calories * split["protein_pct"] / 100 / 4)
    carbs_g = round(calories * split["carbs_pct"] / 100 / 4)
    fat_g = round(calories * split["fat_pct"] / 100 / 9)

    return {
        "bmr": round(base),
        "tdee": round(tdee),
        "daily_delta": round(delta),
        "calories": calories,
        "protein_g": protein_g,
        "carbs_g": carbs_g,
        "fat_g": fat_g,
        "macro_split": split,
        "water_ml": int(profile.get("water_goal_ml_override") or water_goal_ml(profile["weight_kg"])),
        # Guideline limits used by the nutrient breakdown screen.
        "fiber_g": round(14 * calories / 1000),
        "sugar_g_limit": round(calories * 0.10 / 4),
        "saturated_fat_g_limit": round(calories * 0.10 / 9),
        "sodium_mg_limit": 2300,
        "warnings": warnings,
    }


def trend_kg_per_week(points: list[tuple[int, float]]) -> Optional[float]:
    """Least-squares slope over (day_number, kg) points; None if too little data."""
    if len(points) < 3:
        return None
    xs = [p[0] for p in points]
    if max(xs) - min(xs) < 7:
        return None
    n = len(points)
    mean_x = sum(xs) / n
    mean_y = sum(p[1] for p in points) / n
    denominator = sum((x - mean_x) ** 2 for x in xs)
    if denominator == 0:
        return None
    slope_per_day = sum((x - mean_x) * (y - mean_y) for x, y in points) / denominator
    return round(slope_per_day * 7, 2)
