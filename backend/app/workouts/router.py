from fastapi import APIRouter, Depends, status

from ..deps import get_current_user_id, get_exercise_repo
from .models import ExerciseCreate, ExerciseOut

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
