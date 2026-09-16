from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel


class FoodOut(BaseModel):
    id: str
    name: str
    serving_size: float
    serving_unit: str
    calories_per_serving: float
    protein_g: float
    carbs_g: float
    fat_g: float


MealSlot = Literal["breakfast", "lunch", "dinner", "snack"]
EntrySource = Literal["search", "quick_add", "photo_ai"]


class MealEntryCreate(BaseModel):
    meal_slot: MealSlot
    source: EntrySource
    logged_at: datetime
    food_id: Optional[str] = None
    calories: float
    protein_g: float = 0
    carbs_g: float = 0
    fat_g: float = 0


class MealEntryUpdate(BaseModel):
    meal_slot: Optional[MealSlot] = None
    calories: Optional[float] = None
    protein_g: Optional[float] = None
    carbs_g: Optional[float] = None
    fat_g: Optional[float] = None


class MealEntryOut(MealEntryCreate):
    id: str
    user_id: str
    created_at: str
    updated_at: str
