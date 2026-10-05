import time
from collections import defaultdict, deque

from fastapi import HTTPException, status



class SlidingWindowLimiter:
    """Per-key sliding window limiter. In-process, so the limit is per replica."""

    def __init__(self, max_calls: int, window_s: float):
        self.max_calls = max_calls
        self.window_s = window_s
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def check(self, key: str) -> None:
        now = time.monotonic()
        hits = self._hits[key]
        while hits and now - hits[0] > self.window_s:
            hits.popleft()
        if len(hits) >= self.max_calls:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="rate limit exceeded",
                headers={"Retry-After": str(int(self.window_s - (now - hits[0])) + 1)},
            )
        hits.append(now)

    def reset(self) -> None:
        self._hits.clear()


# LLM-backed estimate endpoints cost money per call.
estimate_limiter = SlidingWindowLimiter(max_calls=30, window_s=3600)
