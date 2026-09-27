from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, field_validator, model_validator


class ExerciseCreate(BaseModel):
    name: str
    category: str
    is_bodyweight: bool = False


class ExerciseOut(ExerciseCreate):
    id: str
    created_by_user_id: Optional[str] = None


WorkoutType = Literal["strength", "calisthenics", "running", "cycling"]
WorkoutSource = Literal["manual"]

STRENGTH_TYPES = {"strength", "calisthenics"}
CARDIO_TYPES = {"running", "cycling"}


class ExerciseSet(BaseModel):
    reps: int
    weight_kg: Optional[float] = None
    bodyweight: Optional[bool] = None

    @field_validator("reps")
    @classmethod
    def reps_must_be_positive(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("reps must be greater than 0")
        return value

    @field_validator("weight_kg")
    @classmethod
    def weight_must_be_non_negative(cls, value: Optional[float]) -> Optional[float]:
        if value is not None and value < 0:
            raise ValueError("weight_kg must not be negative")
        return value


class WorkoutExercise(BaseModel):
    exercise_id: str
    sets: list[ExerciseSet]


class WorkoutCreate(BaseModel):
    type: WorkoutType
    started_at: datetime
    duration_s: int
    exercises: Optional[list[WorkoutExercise]] = None
    distance_m: Optional[float] = None
    avg_pace_s_per_km: Optional[float] = None
    elevation_gain_m: Optional[float] = None

    @field_validator("duration_s")
    @classmethod
    def duration_must_be_positive(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("duration_s must be greater than 0")
        return value

    @field_validator("distance_m")
    @classmethod
    def distance_must_be_positive(cls, value: Optional[float]) -> Optional[float]:
        if value is not None and value <= 0:
            raise ValueError("distance_m must be greater than 0")
        return value

    @model_validator(mode="after")
    def check_type_specific_fields(self) -> "WorkoutCreate":
        if self.type in STRENGTH_TYPES and not self.exercises:
            raise ValueError(f"{self.type} workouts require at least one exercise")
        if self.type in CARDIO_TYPES and self.distance_m is None:
            raise ValueError(f"{self.type} workouts require distance_m")
        return self


class WorkoutUpdate(BaseModel):
    # Deliberately narrower than WorkoutCreate: exercises/distance_m/type are
    # not editable here, so an update can never violate the type-specific
    # invariants enforced above (e.g. clearing a strength workout's exercises)
    # after the workout has already been validated once at creation.
    duration_s: Optional[int] = None
    avg_pace_s_per_km: Optional[float] = None
    elevation_gain_m: Optional[float] = None

    @field_validator("duration_s")
    @classmethod
    def duration_must_be_positive(cls, value: Optional[int]) -> Optional[int]:
        if value is not None and value <= 0:
            raise ValueError("duration_s must be greater than 0")
        return value


class WorkoutOut(WorkoutCreate):
    id: str
    user_id: str
    source: WorkoutSource  # always "manual" in v1; server-assigned, never client input
    created_at: str
    updated_at: str
