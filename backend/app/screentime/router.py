from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..deps import get_current_user_id, get_screentime_rule_repo, get_screentime_usage_repo
from ..ratelimit import SlidingWindowLimiter
from .models import (
    ScreenTimeRuleCreate,
    ScreenTimeRuleOut,
    ScreenTimeRuleUpdate,
    ScreenTimeUsageOut,
    ScreenTimeUsageUpsert,
)

router = APIRouter()

MAX_DAYS_BACK = 400
MAX_RANGE_DAYS = 366
# Usage sync runs at most every 15 minutes per device; 60/hour leaves headroom for multiple devices.
usage_limiter = SlidingWindowLimiter(max_calls=60, window_s=3600)


@router.get("/rules", response_model=list[ScreenTimeRuleOut])
async def list_rules(
    user_id: str = Depends(get_current_user_id),
    screentime_rule_repo=Depends(get_screentime_rule_repo),
):
    return await screentime_rule_repo.list_for_user(user_id)


@router.post("/rules", response_model=ScreenTimeRuleOut, status_code=status.HTTP_201_CREATED)
async def create_rule(
    body: ScreenTimeRuleCreate,
    user_id: str = Depends(get_current_user_id),
    screentime_rule_repo=Depends(get_screentime_rule_repo),
):
    return await screentime_rule_repo.create({**body.model_dump(mode="json"), "user_id": user_id})


@router.patch("/rules/{rule_id}", response_model=ScreenTimeRuleOut)
async def update_rule(
    rule_id: str,
    body: ScreenTimeRuleUpdate,
    user_id: str = Depends(get_current_user_id),
    screentime_rule_repo=Depends(get_screentime_rule_repo),
):
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    updated = await screentime_rule_repo.update(user_id, rule_id, updates)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="rule not found")
    return updated


@router.delete("/rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rule(
    rule_id: str,
    user_id: str = Depends(get_current_user_id),
    screentime_rule_repo=Depends(get_screentime_rule_repo),
):
    if not await screentime_rule_repo.delete(user_id, rule_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="rule not found")


@router.put("/usage/{day}", response_model=ScreenTimeUsageOut)
async def upsert_usage(
    day: date,
    body: ScreenTimeUsageUpsert,
    user_id: str = Depends(get_current_user_id),
    usage_repo=Depends(get_screentime_usage_repo),
):
    usage_limiter.check(user_id)
    today = date.today()
    if day > today + timedelta(days=1):
        # One day of slack covers timezones ahead of the server's UTC date.
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="date must not be in the future")
    if day < today - timedelta(days=MAX_DAYS_BACK):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"date must be within {MAX_DAYS_BACK} days"
        )
    return await usage_repo.upsert(user_id, day, body.total_minutes, body.dumb_minutes)


@router.get("/usage", response_model=list[ScreenTimeUsageOut])
async def list_usage(
    start: date = Query(...),
    end: date = Query(...),
    user_id: str = Depends(get_current_user_id),
    usage_repo=Depends(get_screentime_usage_repo),
):
    if end < start:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="end must not be before start")
    if (end - start).days + 1 > MAX_RANGE_DAYS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"range must not exceed {MAX_RANGE_DAYS} days"
        )
    return await usage_repo.list_range(user_id, start, end)
