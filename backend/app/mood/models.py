from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator

MAX_LABELS = 20
MAX_LABEL_LENGTH = 40
MAX_NOTE_LENGTH = 2000


def _check_scale(value: Optional[int], name: str) -> Optional[int]:
    if value is not None and not 1 <= value <= 5:
        raise ValueError(f"{name} must be between 1 and 5")
    return value


def _check_labels(value: Optional[list[str]], name: str) -> Optional[list[str]]:
    if value is None:
        return value
    if len(value) > MAX_LABELS:
        raise ValueError(f"{name} must have at most {MAX_LABELS} entries")
    cleaned = [label.strip() for label in value]
    if any(not label or len(label) > MAX_LABEL_LENGTH for label in cleaned):
        raise ValueError(f"each entry in {name} must be 1 to {MAX_LABEL_LENGTH} characters")
    return cleaned


def _check_note(value: Optional[str]) -> Optional[str]:
    if value is not None and len(value) > MAX_NOTE_LENGTH:
        raise ValueError(f"note must be at most {MAX_NOTE_LENGTH} characters")
    return value


class MoodEntryCreate(BaseModel):
    """A daily check-in. Only mood_score is required; the rest is the fuller check-in."""

    logged_at: datetime
    mood_score: int
    # Fuller check-in, all 1-5 (energy: 1 drained .. 5 energised; stress: 1 calm .. 5 very stressed;
    # sleep_quality: 1 awful .. 5 great). Absent on quick check-ins and on entries from older app versions.
    energy: Optional[int] = None
    stress: Optional[int] = None
    sleep_quality: Optional[int] = None
    # Specific feelings (e.g. "calm", "anxious") and what influenced the day (e.g. "work", "exercise").
    emotions: list[str] = []
    tags: list[str] = []
    note: Optional[str] = None

    @field_validator("mood_score")
    @classmethod
    def score_in_range(cls, value: int) -> int:
        return _check_scale(value, "mood_score")

    @field_validator("energy")
    @classmethod
    def energy_in_range(cls, value: Optional[int]) -> Optional[int]:
        return _check_scale(value, "energy")

    @field_validator("stress")
    @classmethod
    def stress_in_range(cls, value: Optional[int]) -> Optional[int]:
        return _check_scale(value, "stress")

    @field_validator("sleep_quality")
    @classmethod
    def sleep_in_range(cls, value: Optional[int]) -> Optional[int]:
        return _check_scale(value, "sleep_quality")

    @field_validator("emotions")
    @classmethod
    def emotions_valid(cls, value: list[str]) -> list[str]:
        return _check_labels(value, "emotions")

    @field_validator("tags")
    @classmethod
    def tags_valid(cls, value: list[str]) -> list[str]:
        return _check_labels(value, "tags")

    @field_validator("note")
    @classmethod
    def note_length(cls, value: Optional[str]) -> Optional[str]:
        return _check_note(value)


class MoodEntryUpdate(BaseModel):
    mood_score: Optional[int] = None
    energy: Optional[int] = None
    stress: Optional[int] = None
    sleep_quality: Optional[int] = None
    emotions: Optional[list[str]] = None
    tags: Optional[list[str]] = None
    note: Optional[str] = None

    @field_validator("mood_score")
    @classmethod
    def score_in_range(cls, value: Optional[int]) -> Optional[int]:
        return _check_scale(value, "mood_score")

    @field_validator("energy")
    @classmethod
    def energy_in_range(cls, value: Optional[int]) -> Optional[int]:
        return _check_scale(value, "energy")

    @field_validator("stress")
    @classmethod
    def stress_in_range(cls, value: Optional[int]) -> Optional[int]:
        return _check_scale(value, "stress")

    @field_validator("sleep_quality")
    @classmethod
    def sleep_in_range(cls, value: Optional[int]) -> Optional[int]:
        return _check_scale(value, "sleep_quality")

    @field_validator("emotions")
    @classmethod
    def emotions_valid(cls, value: Optional[list[str]]) -> Optional[list[str]]:
        return _check_labels(value, "emotions")

    @field_validator("tags")
    @classmethod
    def tags_valid(cls, value: Optional[list[str]]) -> Optional[list[str]]:
        return _check_labels(value, "tags")

    @field_validator("note")
    @classmethod
    def note_length(cls, value: Optional[str]) -> Optional[str]:
        return _check_note(value)


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
