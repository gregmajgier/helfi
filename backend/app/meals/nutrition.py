from .models import NUTRIENT_FIELDS

# Food records use "calories_per_serving"; entries and recipes use "calories".
_FOOD_TO_ENTRY = {"calories_per_serving": "calories"}


def food_nutrients(food: dict) -> dict:
    """Nutrition of one serving (serving_size serving_unit) of a food."""
    out = {}
    for field in NUTRIENT_FIELDS:
        source = "calories_per_serving" if field == "calories" else field
        out[field] = float(food.get(source, 0) or 0)
    return out


def scale(nutrients: dict, factor: float) -> dict:
    return {field: round(float(nutrients.get(field, 0) or 0) * factor, 2) for field in NUTRIENT_FIELDS}


def nutrients_for_amount(food: dict, amount: float) -> dict:
    return scale(food_nutrients(food), amount / food["serving_size"])


def add(a: dict, b: dict) -> dict:
    return {field: round(float(a.get(field, 0) or 0) + float(b.get(field, 0) or 0), 2) for field in NUTRIENT_FIELDS}


def empty() -> dict:
    return {field: 0.0 for field in NUTRIENT_FIELDS}


def total(items: list[dict]) -> dict:
    result = empty()
    for item in items:
        result = add(result, item)
    return result
