from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field

from ..meals.models import MealSlot


class IngredientIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    amount: float = Field(gt=0, le=100000)
    unit: str = Field(min_length=1, max_length=20)
    food_id: Optional[str] = None
    # Nutrition for the whole amount (not per 100 g).
    calories: float = Field(default=0, ge=0, le=20000)
    protein_g: float = Field(default=0, ge=0, le=5000)
    carbs_g: float = Field(default=0, ge=0, le=5000)
    fat_g: float = Field(default=0, ge=0, le=5000)
    fiber_g: float = Field(default=0, ge=0, le=5000)
    sugar_g: float = Field(default=0, ge=0, le=5000)
    saturated_fat_g: float = Field(default=0, ge=0, le=5000)
    sodium_mg: float = Field(default=0, ge=0, le=100000)


class RecipeIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    servings: float = Field(gt=0, le=100)
    meal_types: list[MealSlot] = Field(default_factory=list, max_length=4)
    prep_minutes: Optional[int] = Field(default=None, ge=0, le=1440)
    ingredients: list[IngredientIn] = Field(min_length=1, max_length=60)
    instructions: list[str] = Field(default_factory=list, max_length=30)


class Nutrients(BaseModel):
    calories: float = 0
    protein_g: float = 0
    carbs_g: float = 0
    fat_g: float = 0
    fiber_g: float = 0
    sugar_g: float = 0
    saturated_fat_g: float = 0
    sodium_mg: float = 0


class RecipeOut(RecipeIn):
    id: str
    curated: bool = False
    totals: Nutrients
    per_serving: Nutrients


class LogRecipeIn(BaseModel):
    servings: float = Field(gt=0, le=100)
    meal_slot: MealSlot
    day: date
    logged_at: Optional[datetime] = None
