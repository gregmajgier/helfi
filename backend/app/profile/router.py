from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..deps import get_current_user_id, get_profile_repo, get_weight_repo
from .calc import compute_targets, trend_kg_per_week
from .models import ForecastOut, ProfileIn, ProfileOut, TargetsOut, WeightIn, WeightOut

router = APIRouter()


def _today() -> date:
    return datetime.now(timezone.utc).date()


async def _require_profile(profile_repo, user_id: str) -> dict:
    profile = await profile_repo.get(user_id, user_id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="profile not set up")
    return profile


@router.get("", response_model=ProfileOut)
async def get_profile(
    user_id: str = Depends(get_current_user_id), profile_repo=Depends(get_profile_repo)
):
    return await _require_profile(profile_repo, user_id)


@router.put("", response_model=ProfileOut)
async def put_profile(
    body: ProfileIn,
    user_id: str = Depends(get_current_user_id),
    profile_repo=Depends(get_profile_repo),
    weight_repo=Depends(get_weight_repo),
):
    # One profile document per user, keyed by the user id.
    saved = await profile_repo.put({**body.model_dump(mode="json"), "id": user_id, "user_id": user_id})
    if not await weight_repo.list_for_user(user_id):
        await weight_repo.create({"user_id": user_id, "day": _today().isoformat(), "weight_kg": body.weight_kg})
    return saved


@router.get("/targets", response_model=TargetsOut)
async def get_targets(
    user_id: str = Depends(get_current_user_id), profile_repo=Depends(get_profile_repo)
):
    profile = await _require_profile(profile_repo, user_id)
    return compute_targets(profile, _today().year)


@router.post("/weight", response_model=WeightOut, status_code=status.HTTP_201_CREATED)
async def log_weight(
    body: WeightIn,
    user_id: str = Depends(get_current_user_id),
    profile_repo=Depends(get_profile_repo),
    weight_repo=Depends(get_weight_repo),
):
    if body.day > _today() + timedelta(days=1):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="date is in the future")
    # One weigh-in per day: replace an existing one rather than stacking.
    for existing in await weight_repo.list_for_user(user_id, field="day", gte=body.day.isoformat(), lte=body.day.isoformat()):
        await weight_repo.delete(user_id, existing["id"])
    saved = await weight_repo.create({"user_id": user_id, "day": body.day.isoformat(), "weight_kg": body.weight_kg})
    await _sync_profile_weight(user_id, profile_repo, weight_repo)
    return saved


async def _sync_profile_weight(user_id: str, profile_repo, weight_repo) -> None:
    """Keep the profile's current weight equal to the most recent weigh-in."""
    profile = await profile_repo.get(user_id, user_id)
    entries = await weight_repo.list_for_user(user_id, field="day")
    if profile and entries:
        await profile_repo.update(user_id, user_id, {"weight_kg": entries[-1]["weight_kg"]})


@router.get("/weight", response_model=list[WeightOut])
async def list_weight(
    days: int = Query(default=90, ge=1, le=730),
    user_id: str = Depends(get_current_user_id),
    weight_repo=Depends(get_weight_repo),
):
    since = (_today() - timedelta(days=days)).isoformat()
    return await weight_repo.list_for_user(user_id, field="day", gte=since)


@router.delete("/weight/{weight_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_weight(
    weight_id: str,
    user_id: str = Depends(get_current_user_id),
    profile_repo=Depends(get_profile_repo),
    weight_repo=Depends(get_weight_repo),
):
    if not await weight_repo.delete(user_id, weight_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="weigh-in not found")
    await _sync_profile_weight(user_id, profile_repo, weight_repo)


@router.get("/forecast", response_model=ForecastOut)
async def get_forecast(
    user_id: str = Depends(get_current_user_id),
    profile_repo=Depends(get_profile_repo),
    weight_repo=Depends(get_weight_repo),
):
    profile = await _require_profile(profile_repo, user_id)
    today = _today()
    since = (today - timedelta(days=28)).isoformat()
    recent = await weight_repo.list_for_user(user_id, field="day", gte=since)
    points = [((date.fromisoformat(w["day"]) - today).days, w["weight_kg"]) for w in recent]
    current = recent[-1]["weight_kg"] if recent else profile["weight_kg"]

    goal_kg = profile.get("goal_weight_kg")
    weekly = profile.get("weekly_change_kg") or 0
    direction = {"lose": -1, "build": 1, "maintain": 0}[profile["goal"]]
    trend = trend_kg_per_week(points)

    reached = goal_kg is not None and (
        (direction < 0 and current <= goal_kg) or (direction > 0 and current >= goal_kg)
    )
    planned_eta = trend_eta = None
    if goal_kg is not None and direction and not reached:
        if weekly > 0:
            planned_eta = today + timedelta(days=round(abs(current - goal_kg) / weekly * 7))
        if trend and (trend < 0) == (direction < 0) and abs(trend) > 0.05:
            trend_eta = today + timedelta(days=round(abs(current - goal_kg) / abs(trend) * 7))

    return ForecastOut(
        current_kg=current,
        goal_kg=goal_kg,
        planned_weekly_change_kg=weekly if direction else 0,
        planned_eta=planned_eta,
        trend_kg_per_week=trend,
        trend_eta=trend_eta,
        reached=reached,
    )
