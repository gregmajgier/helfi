from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator


class MoodEntryCreate(BaseModel):
    logged_at: datetime
    mood_score: int
    tags: list[str] = []
    note: Optional[str] = None

    @field_validator("mood_score")
    @classmethod
    def score_in_range(cls, value: int) -> int:
        if not 1 <= value <= 5:
            raise ValueError("mood_score must be between 1 and 5")
        return value


class MoodEntryUpdate(BaseModel):
    mood_score: Optional[int] = None
    tags: Optional[list[str]] = None
    note: Optional[str] = None

    @field_validator("mood_score")
    @classmethod
    def score_in_range(cls, value: Optional[int]) -> Optional[int]:
        if value is not None and not 1 <= value <= 5:
            raise ValueError("mood_score must be between 1 and 5")
        return value


class MoodEntryOut(MoodEntryCreate):
    id: str
    user_id: str
    created_at: str
    updated_at: str


class JournalEntryCreate(BaseModel):
    written_at: datetime
    prompt: Optional[str] = None
    body: str

    @field_validator("body")
    @classmethod
    def body_not_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("body must not be empty")
        return value


class JournalEntryUpdate(BaseModel):
    body: Optional[str] = None

    @field_validator("body")
    @classmethod
    def body_not_empty(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and not value.strip():
            raise ValueError("body must not be empty")
        return value


class JournalEntryOut(JournalEntryCreate):
    id: str
    user_id: str
    created_at: str
    updated_at: str
