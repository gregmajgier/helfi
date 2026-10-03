from typing import Optional

from pydantic import BaseModel, field_validator


class ScreenTimeRuleCreate(BaseModel):
    name: str
    apps_or_categories: list[str]
    daily_limit_minutes: Optional[int] = None
    enabled: bool = True

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("name must not be empty")
        return value

    @field_validator("apps_or_categories")
    @classmethod
    def categories_not_empty(cls, value: list[str]) -> list[str]:
        if not value:
            raise ValueError("apps_or_categories must have at least one entry")
        return value

    @field_validator("daily_limit_minutes")
    @classmethod
    def limit_must_be_positive(cls, value: Optional[int]) -> Optional[int]:
        if value is not None and value <= 0:
            raise ValueError("daily_limit_minutes must be greater than 0")
        return value


class ScreenTimeRuleUpdate(BaseModel):
    name: Optional[str] = None
    apps_or_categories: Optional[list[str]] = None
    daily_limit_minutes: Optional[int] = None
    enabled: Optional[bool] = None

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and not value.strip():
            raise ValueError("name must not be empty")
        return value

    @field_validator("daily_limit_minutes")
    @classmethod
    def limit_must_be_positive(cls, value: Optional[int]) -> Optional[int]:
        if value is not None and value <= 0:
            raise ValueError("daily_limit_minutes must be greater than 0")
        return value


class ScreenTimeRuleOut(ScreenTimeRuleCreate):
    id: str
    user_id: str
    created_at: str
    updated_at: str
