from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

# Every nutrient column that scales with portion size. Order is the display order.
NUTRIENT_FIELDS = (
    "calories",
    "protein_g",
    "carbs_g",
    "fat_g",
    "fiber_g",
    "sugar_g",
    "saturated_fat_g",
    "sodium_mg",
)


class FoodCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    brand: Optional[str] = Field(default=None, max_length=80)
    serving_size: float = Field(gt=0, le=10000)
    serving_unit: str = Field(min_length=1, max_length=20)
    calories_per_serving: float = Field(ge=0, le=20000)
    protein_g: float = Field(default=0, ge=0, le=5000)
    carbs_g: float = Field(default=0, ge=0, le=5000)
    fat_g: float = Field(default=0, ge=0, le=5000)
    fiber_g: float = Field(default=0, ge=0, le=5000)
    sugar_g: float = Field(default=0, ge=0, le=5000)
    saturated_fat_g: float = Field(default=0, ge=0, le=5000)
    sodium_mg: float = Field(default=0, ge=0, le=100000)
    barcode: Optional[str] = None


class FoodUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    brand: Optional[str] = Field(default=None, max_length=80)
    serving_size: Optional[float] = Field(default=None, gt=0, le=10000)
    serving_unit: Optional[str] = Field(default=None, min_length=1, max_length=20)
    calories_per_serving: Optional[float] = Field(default=None, ge=0, le=20000)
    protein_g: Optional[float] = Field(default=None, ge=0, le=5000)
    carbs_g: Optional[float] = Field(default=None, ge=0, le=5000)
    fat_g: Optional[float] = Field(default=None, ge=0, le=5000)
    fiber_g: Optional[float] = Field(default=None, ge=0, le=5000)
    sugar_g: Optional[float] = Field(default=None, ge=0, le=5000)
    saturated_fat_g: Optional[float] = Field(default=None, ge=0, le=5000)
    sodium_mg: Optional[float] = Field(default=None, ge=0, le=100000)


class FoodOut(FoodCreate):
    id: str
    created_by_user_id: Optional[str] = None


MealSlot = Literal["breakfast", "lunch", "dinner", "snack"]
# "quick_add" is kept for backward compatibility with entries created before
# that logging path was removed from the client; never written by new code.
EntrySource = Literal[
    "search",
    "quick_add",
    "photo_ai",
    "description_ai",
    "barcode",
    "custom",
    "recipe",
    "plan",
]


class MealEntryCreate(BaseModel):
    meal_slot: MealSlot
    source: EntrySource
    logged_at: datetime
    # Local calendar day the user sees the entry under. Falls back to the date
    # in logged_at for older clients; always populated server-side on write.
    day: Optional[date] = None
    food_id: Optional[str] = None
    name: Optional[str] = Field(default=None, max_length=120)
    amount: Optional[float] = Field(default=None, gt=0, le=100000)
    unit: Optional[str] = Field(default=None, max_length=20)
    calories: float = Field(ge=0, le=20000)
    protein_g: float = Field(default=0, ge=0, le=5000)
    carbs_g: float = Field(default=0, ge=0, le=5000)
    fat_g: float = Field(default=0, ge=0, le=5000)
    fiber_g: float = Field(default=0, ge=0, le=5000)
    sugar_g: float = Field(default=0, ge=0, le=5000)
    saturated_fat_g: float = Field(default=0, ge=0, le=5000)
    sodium_mg: float = Field(default=0, ge=0, le=100000)


class MealEntryUpdate(BaseModel):
    meal_slot: Optional[MealSlot] = None
    name: Optional[str] = Field(default=None, max_length=120)
    # Changing the amount rescales every nutrient proportionally, server-side.
    amount: Optional[float] = Field(default=None, gt=0, le=100000)
    calories: Optional[float] = Field(default=None, ge=0, le=20000)
    protein_g: Optional[float] = Field(default=None, ge=0, le=5000)
    carbs_g: Optional[float] = Field(default=None, ge=0, le=5000)
    fat_g: Optional[float] = Field(default=None, ge=0, le=5000)
    fiber_g: Optional[float] = Field(default=None, ge=0, le=5000)
    sugar_g: Optional[float] = Field(default=None, ge=0, le=5000)
    saturated_fat_g: Optional[float] = Field(default=None, ge=0, le=5000)
    sodium_mg: Optional[float] = Field(default=None, ge=0, le=100000)


class MealEntryOut(MealEntryCreate):
    id: str
    user_id: str
    created_at: str
    updated_at: str


class LogFoodIn(BaseModel):
    """Log a database food by amount; the server computes the nutrition."""

    food_id: str
    amount: float = Field(gt=0, le=100000)
    meal_slot: MealSlot
    day: date
    logged_at: Optional[datetime] = None


class CopyEntriesIn(BaseModel):
    from_day: date
    to_day: date
    from_slot: Optional[MealSlot] = None
    to_slot: Optional[MealSlot] = None


class DayTotals(BaseModel):
    day: date
    calories: float = 0
    protein_g: float = 0
    carbs_g: float = 0
    fat_g: float = 0
    fiber_g: float = 0
    sugar_g: float = 0
    saturated_fat_g: float = 0
    sodium_mg: float = 0
    entries: int = 0


class StatsOut(BaseModel):
    start: date
    end: date
    days: list[DayTotals]
    logged_days: int
    average_calories: float
    average_protein_g: float
    average_carbs_g: float
    average_fat_g: float


class PhotoEstimateOut(BaseModel):
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float
    confidence: float
    description: str


class MealDescriptionIn(BaseModel):
    description: str = Field(max_length=500)
