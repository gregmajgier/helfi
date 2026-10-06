from datetime import date, datetime, timezone
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

Sex = Literal["male", "female"]
ActivityLevel = Literal["sedentary", "light", "moderate", "active", "very_active"]
Goal = Literal["lose", "maintain", "build"]


class MacroSplit(BaseModel):
    protein_pct: int = Field(ge=10, le=60)
    carbs_pct: int = Field(ge=10, le=70)
    fat_pct: int = Field(ge=10, le=60)

    @model_validator(mode="after")
    def sums_to_100(self):
        if self.protein_pct + self.carbs_pct + self.fat_pct != 100:
            raise ValueError("macro split must add up to 100")
        return self


class ProfileIn(BaseModel):
    sex: Sex
    birth_year: int = Field(ge=1900)
    height_cm: float = Field(ge=100, le=250)
    weight_kg: float = Field(ge=30, le=300)
    activity_level: ActivityLevel
    goal: Goal
    goal_weight_kg: Optional[float] = Field(default=None, ge=30, le=300)
    # Magnitude only; the sign comes from `goal`. Capped at 1 kg/week for safety.
    weekly_change_kg: float = Field(default=0.5, ge=0, le=1)
    calorie_override: Optional[int] = Field(default=None, ge=800, le=6000)
    macro_split: Optional[MacroSplit] = None
    water_goal_ml_override: Optional[int] = Field(default=None, ge=500, le=8000)

    @field_validator("birth_year")
    @classmethod
    def plausible_age(cls, value: int) -> int:
        if value > datetime.now(timezone.utc).year - 13:
            raise ValueError("must be at least 13 years old")
        return value


class ProfileOut(ProfileIn):
    user_id: str
    updated_at: str


class TargetsOut(BaseModel):
    bmr: int
    tdee: int
    daily_delta: int
    calories: int
    protein_g: int
    carbs_g: int
    fat_g: int
    macro_split: MacroSplit
    water_ml: int
    fiber_g: int
    sugar_g_limit: int
    saturated_fat_g_limit: int
    sodium_mg_limit: int
    warnings: list[str]


class WeightIn(BaseModel):
    day: date
    weight_kg: float = Field(ge=30, le=300)


class WeightOut(WeightIn):
    id: str


class ForecastOut(BaseModel):
    current_kg: float
    goal_kg: Optional[float] = None
    planned_weekly_change_kg: float
    planned_eta: Optional[date] = None
    trend_kg_per_week: Optional[float] = None
    trend_eta: Optional[date] = None
    reached: bool = False
