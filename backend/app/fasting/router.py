from datetime import datetime, timedelta, timezone
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from ..deps import get_current_user_id, get_fasting_repo

router = APIRouter()

PROTOCOL_HOURS = {"12:12": 12, "14:10": 14, "16:8": 16, "18:6": 18, "20:4": 20}
Protocol = Literal["12:12", "14:10", "16:8", "18:6", "20:4", "custom"]


class StartFastIn(BaseModel):
    protocol: Protocol = "16:8"
    # Required for the custom protocol, ignored otherwise.
    target_hours: Optional[float] = Field(default=None, gt=0, le=72)
    # Allows backfilling a fast you forgot to start, never into the future.
    started_at: Optional[datetime] = None


class EndFastIn(BaseModel):
    ended_at: Optional[datetime] = None


class FastOut(BaseModel):
    id: str
    protocol: Protocol
    target_hours: float
    started_at: str
    ended_at: Optional[str] = None
    elapsed_hours: float
    completed: bool


class FastingStatsOut(BaseModel):
    total: int
    completed: int
    average_hours: float
    longest_hours: float
    current_streak: int


class FastingHistoryOut(BaseModel):
    sessions: list[FastOut]
    stats: FastingStatsOut


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _aware(value: datetime) -> datetime:
    # Stored as UTC so ISO strings sort and compare correctly in queries.
    return (value if value.tzinfo else value.replace(tzinfo=timezone.utc)).astimezone(timezone.utc)


def _present(session: dict, now: datetime) -> FastOut:
    started = datetime.fromisoformat(session["started_at"])
    ended = datetime.fromisoformat(session["ended_at"]) if session.get("ended_at") else now
    elapsed = max((ended - started).total_seconds() / 3600, 0)
    return FastOut(
        id=session["id"],
        protocol=session["protocol"],
        target_hours=session["target_hours"],
        started_at=session["started_at"],
        ended_at=session.get("ended_at"),
        elapsed_hours=round(elapsed, 2),
        completed=elapsed >= session["target_hours"],
    )


async def _active(fasting_repo, user_id: str) -> Optional[dict]:
    for session in await fasting_repo.list_for_user(user_id, field="started_at"):
        if not session.get("ended_at"):
            return session
    return None


@router.post("/start", response_model=FastOut, status_code=status.HTTP_201_CREATED)
async def start_fast(
    body: StartFastIn,
    user_id: str = Depends(get_current_user_id),
    fasting_repo=Depends(get_fasting_repo),
):
    now = _now()
    if await _active(fasting_repo, user_id):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="a fast is already running")
    if body.protocol == "custom":
        if body.target_hours is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="target_hours is required")
        target = body.target_hours
    else:
        target = PROTOCOL_HOURS[body.protocol]
    started = _aware(body.started_at) if body.started_at else now
    if started > now + timedelta(minutes=2):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="start time is in the future")
    session = await fasting_repo.create(
        {
            "user_id": user_id,
            "protocol": body.protocol,
            "target_hours": target,
            "started_at": started.isoformat(),
            "ended_at": None,
        }
    )
    return _present(session, now)


@router.post("/end", response_model=FastOut)
async def end_fast(
    body: EndFastIn,
    user_id: str = Depends(get_current_user_id),
    fasting_repo=Depends(get_fasting_repo),
):
    now = _now()
    session = await _active(fasting_repo, user_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="no fast is running")
    ended = _aware(body.ended_at) if body.ended_at else now
    if ended > now + timedelta(minutes=2) or ended < datetime.fromisoformat(session["started_at"]):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid end time")
    updated = await fasting_repo.update(user_id, session["id"], {"ended_at": ended.isoformat()})
    return _present(updated, now)


@router.get("/current", response_model=Optional[FastOut])
async def current_fast(
    user_id: str = Depends(get_current_user_id), fasting_repo=Depends(get_fasting_repo)
):
    session = await _active(fasting_repo, user_id)
    return _present(session, _now()) if session else None


def _streak(finished: list[FastOut]) -> int:
    """Consecutive most-recent completed fasts, stopping at the first missed target."""
    count = 0
    for session in sorted(finished, key=lambda s: s.started_at, reverse=True):
        if not session.completed:
            break
        count += 1
    return count


@router.get("/history", response_model=FastingHistoryOut)
async def fasting_history(
    days: int = Query(default=30, ge=1, le=365),
    user_id: str = Depends(get_current_user_id),
    fasting_repo=Depends(get_fasting_repo),
):
    now = _now()
    since = (now - timedelta(days=days)).isoformat()
    sessions = await fasting_repo.list_for_user(user_id, field="started_at", gte=since)
    presented = [_present(s, now) for s in sessions]
    finished = [s for s in presented if s.ended_at]
    completed = [s for s in finished if s.completed]
    stats = FastingStatsOut(
        total=len(finished),
        completed=len(completed),
        average_hours=round(sum(s.elapsed_hours for s in finished) / len(finished), 1) if finished else 0,
        longest_hours=max((s.elapsed_hours for s in finished), default=0),
        current_streak=_streak(finished),
    )
    return FastingHistoryOut(sessions=list(reversed(presented)), stats=stats)


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_fast(
    session_id: str,
    user_id: str = Depends(get_current_user_id),
    fasting_repo=Depends(get_fasting_repo),
):
    if not await fasting_repo.delete(user_id, session_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="fast not found")
