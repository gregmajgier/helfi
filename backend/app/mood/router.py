from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status

from ..deps import get_current_user_id, get_journal_entry_repo, get_mood_entry_repo
from .models import (
    JournalEntryCreate,
    JournalEntryOut,
    JournalEntryUpdate,
    MoodEntryCreate,
    MoodEntryOut,
    MoodEntryUpdate,
)
from .prompts import prompt_for_today

router = APIRouter()


@router.get("/entries", response_model=list[MoodEntryOut])
async def list_mood_entries(
    start: Optional[date] = None,
    end: Optional[date] = None,
    user_id: str = Depends(get_current_user_id),
    mood_entry_repo=Depends(get_mood_entry_repo),
):
    return await mood_entry_repo.list_for_user(user_id, start=start, end=end)


@router.post("/entries", response_model=MoodEntryOut, status_code=status.HTTP_201_CREATED)
async def create_mood_entry(
    body: MoodEntryCreate,
    user_id: str = Depends(get_current_user_id),
    mood_entry_repo=Depends(get_mood_entry_repo),
):
    return await mood_entry_repo.create({**body.model_dump(mode="json"), "user_id": user_id})


@router.patch("/entries/{entry_id}", response_model=MoodEntryOut)
async def update_mood_entry(
    entry_id: str,
    body: MoodEntryUpdate,
    user_id: str = Depends(get_current_user_id),
    mood_entry_repo=Depends(get_mood_entry_repo),
):
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    updated = await mood_entry_repo.update(user_id, entry_id, updates)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="mood entry not found")
    return updated


@router.delete("/entries/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_mood_entry(
    entry_id: str,
    user_id: str = Depends(get_current_user_id),
    mood_entry_repo=Depends(get_mood_entry_repo),
):
    if not await mood_entry_repo.delete(user_id, entry_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="mood entry not found")


@router.get("/journal", response_model=list[JournalEntryOut])
async def list_journal_entries(
    user_id: str = Depends(get_current_user_id),
    journal_entry_repo=Depends(get_journal_entry_repo),
):
    return await journal_entry_repo.list_for_user(user_id)


@router.post("/journal", response_model=JournalEntryOut, status_code=status.HTTP_201_CREATED)
async def create_journal_entry(
    body: JournalEntryCreate,
    user_id: str = Depends(get_current_user_id),
    journal_entry_repo=Depends(get_journal_entry_repo),
):
    return await journal_entry_repo.create({**body.model_dump(mode="json"), "user_id": user_id})


@router.patch("/journal/{entry_id}", response_model=JournalEntryOut)
async def update_journal_entry(
    entry_id: str,
    body: JournalEntryUpdate,
    user_id: str = Depends(get_current_user_id),
    journal_entry_repo=Depends(get_journal_entry_repo),
):
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    updated = await journal_entry_repo.update(user_id, entry_id, updates)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="journal entry not found")
    return updated


@router.delete("/journal/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_journal_entry(
    entry_id: str,
    user_id: str = Depends(get_current_user_id),
    journal_entry_repo=Depends(get_journal_entry_repo),
):
    if not await journal_entry_repo.delete(user_id, entry_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="journal entry not found")


@router.get("/prompts")
async def get_todays_prompt(user_id: str = Depends(get_current_user_id)):
    return {"prompt": prompt_for_today()}
