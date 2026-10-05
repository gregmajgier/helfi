from datetime import date
from typing import Optional

from pydantic import BaseModel, Field, model_validator

from ..meals.models import MealSlot


class PlanItemIn(BaseModel):
    day: date
    meal_slot: MealSlot
    recipe_id: Optional[str] = None
    servings: Optional[float] = Field(default=None, gt=0, le=100)
    food_id: Optional[str] = None
    amount: Optional[float] = Field(default=None, gt=0, le=100000)

    @model_validator(mode="after")
    def exactly_one_kind(self):
        is_recipe = self.recipe_id is not None
        is_food = self.food_id is not None
        if is_recipe == is_food:
            raise ValueError("provide either recipe_id or food_id")
        if is_recipe and self.servings is None:
            raise ValueError("servings is required for a recipe")
        if is_food and self.amount is None:
            raise ValueError("amount is required for a food")
        return self


class PlanIngredient(BaseModel):
    name: str
    amount: float
    unit: str


class PlanItemOut(BaseModel):
    id: str
    day: date
    meal_slot: MealSlot
    name: str
    recipe_id: Optional[str] = None
    food_id: Optional[str] = None
    amount: float
    unit: str
    calories: float = 0
    protein_g: float = 0
    carbs_g: float = 0
    fat_g: float = 0
    fiber_g: float = 0
    sugar_g: float = 0
    saturated_fat_g: float = 0
    sodium_mg: float = 0
    ingredients: list[PlanIngredient] = []


class DateRangeIn(BaseModel):
    start: date
    end: date


class ApplyPlanIn(BaseModel):
    day: date
    meal_slot: Optional[MealSlot] = None


class GeneratePlanIn(BaseModel):
    start: date
    days: int = Field(default=7, ge=1, le=14)
    calorie_target: Optional[int] = Field(default=None, ge=800, le=6000)
    replace: bool = True


class ShoppingItemIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    amount: Optional[float] = Field(default=None, gt=0, le=100000)
    unit: Optional[str] = Field(default=None, max_length=20)


class ShoppingPatch(BaseModel):
    checked: bool


class ShoppingItemOut(BaseModel):
    id: str
    name: str
    amount: Optional[float] = None
    unit: Optional[str] = None
    checked: bool = False
    source: str = "manual"
