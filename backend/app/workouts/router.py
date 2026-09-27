from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status

from ..deps import get_current_user_id, get_exercise_repo, get_workout_repo
from .models import (
    ExerciseCreate,
    ExerciseOut,
    WorkoutCreate,
    WorkoutOut,
    WorkoutType,
    WorkoutUpdate,
)

router = APIRouter()


@router.get("/exercises", response_model=list[ExerciseOut])
async def search_exercises(
    q: str,
    user_id: str = Depends(get_current_user_id),
    exercise_repo=Depends(get_exercise_repo),
):
    return await exercise_repo.search(q)


@router.post("/exercises", response_model=ExerciseOut, status_code=status.HTTP_201_CREATED)
async def create_exercise(
    body: ExerciseCreate,
    user_id: str = Depends(get_current_user_id),
    exercise_repo=Depends(get_exercise_repo),
):
    return await exercise_repo.create({**body.model_dump(), "created_by_user_id": user_id})


@router.get("", response_model=list[WorkoutOut])
async def list_workouts(
    type: Optional[WorkoutType] = None,
    user_id: str = Depends(get_current_user_id),
    workout_repo=Depends(get_workout_repo),
):
    return await workout_repo.list_for_user(user_id, workout_type=type)


@router.post("", response_model=WorkoutOut, status_code=status.HTTP_201_CREATED)
async def create_workout(
    body: WorkoutCreate,
    user_id: str = Depends(get_current_user_id),
    workout_repo=Depends(get_workout_repo),
):
    return await workout_repo.create(
        {**body.model_dump(mode="json"), "user_id": user_id, "source": "manual"}
    )


@router.patch("/{workout_id}", response_model=WorkoutOut)
async def update_workout(
    workout_id: str,
    body: WorkoutUpdate,
    user_id: str = Depends(get_current_user_id),
    workout_repo=Depends(get_workout_repo),
):
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    updated = await workout_repo.update(user_id, workout_id, updates)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="workout not found")
    return updated


@router.delete("/{workout_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workout(
    workout_id: str,
    user_id: str = Depends(get_current_user_id),
    workout_repo=Depends(get_workout_repo),
):
    if not await workout_repo.delete(user_id, workout_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="workout not found")
