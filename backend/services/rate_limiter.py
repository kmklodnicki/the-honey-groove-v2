"""Simple in-memory rate limiter using sliding window."""

import time
from collections import defaultdict
from fastapi import HTTPException, Request


class RateLimiter:
    def __init__(self):
        self._store: dict[str, list[float]] = defaultdict(list)

    def check(self, key: str, max_requests: int, window_seconds: int):
        now = time.time()
        cutoff = now - window_seconds
        self._store[key] = [t for t in self._store[key] if t > cutoff]
        if len(self._store[key]) >= max_requests:
            raise HTTPException(status_code=429, detail="Too many attempts. Please try again in a few minutes.")
        self._store[key].append(now)


rate_limiter = RateLimiter()


def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"
