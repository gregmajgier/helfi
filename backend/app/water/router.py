from datetime import date, datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from ..deps import get_current_user_id, get_profile_repo, get_water_repo
from ..profile.calc import compute_targets

router = APIRouter()

DEFAULT_GOAL_ML = 2000
MAX_DAILY_ML = 20000


class WaterIn(BaseModel):
    day: date
    amount_ml: int = Field(gt=0, le=5000)
    logged_at: Optional[datetime] = None


class WaterEntryOut(BaseModel):
    id: str
    day: date
    amount_ml: int
    logged_at: str


class WaterDayOut(BaseModel):
    day: date
    total_ml: int
    goal_ml: int
    entries: list[WaterEntryOut]


async def _goal_ml(profile_repo, user_id: str) -> int:
    profile = await profile_repo.get(user_id, user_id)
    if not profile:
        return DEFAULT_GOAL_ML
    return compute_targets(profile, datetime.now(timezone.utc).year)["water_ml"]


async def _day(water_repo, profile_repo, user_id: str, day: date) -> WaterDayOut:
    entries = await water_repo.list_for_user(user_id, field="day", gte=day.isoformat(), lte=day.isoformat())
    entries.sort(key=lambda e: e["logged_at"])
    return WaterDayOut(
        day=day,
        total_ml=sum(e["amount_ml"] for e in entries),
        goal_ml=await _goal_ml(profile_repo, user_id),
        entries=entries,
    )


@router.get("", response_model=WaterDayOut)
async def get_water(
    day: date,
    user_id: str = Depends(get_current_user_id),
    water_repo=Depends(get_water_repo),
    profile_repo=Depends(get_profile_repo),
):
    return await _day(water_repo, profile_repo, user_id, day)


@router.post("", response_model=WaterDayOut, status_code=status.HTTP_201_CREATED)
async def add_water(
    body: WaterIn,
    user_id: str = Depends(get_current_user_id),
    water_repo=Depends(get_water_repo),
    profile_repo=Depends(get_profile_repo),
):
    current = await _day(water_repo, profile_repo, user_id, body.day)
    if current.total_ml + body.amount_ml > MAX_DAILY_ML:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="daily water limit exceeded")
    logged_at = body.logged_at or datetime.now(timezone.utc)
    await water_repo.create(
        {
            "user_id": user_id,
            "day": body.day.isoformat(),
            "amount_ml": body.amount_ml,
            "logged_at": logged_at.isoformat(),
        }
    )
    return await _day(water_repo, profile_repo, user_id, body.day)


@router.delete("/{entry_id}", response_model=WaterDayOut)
async def delete_water(
    entry_id: str,
    user_id: str = Depends(get_current_user_id),
    water_repo=Depends(get_water_repo),
    profile_repo=Depends(get_profile_repo),
):
    entry = await water_repo.get(user_id, entry_id)
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="water entry not found")
    await water_repo.delete(user_id, entry_id)
    return await _day(water_repo, profile_repo, user_id, date.fromisoformat(entry["day"]))
