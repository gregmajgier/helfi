from fastapi import APIRouter, Depends, HTTPException, status

from ..deps import get_current_user_id, get_screentime_rule_repo
from .models import ScreenTimeRuleCreate, ScreenTimeRuleOut, ScreenTimeRuleUpdate

router = APIRouter()


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
