from typing import Optional

from pydantic import BaseModel


class ExerciseCreate(BaseModel):
    name: str
    category: str
    is_bodyweight: bool = False


class ExerciseOut(ExerciseCreate):
    id: str
    created_by_user_id: Optional[str] = None
