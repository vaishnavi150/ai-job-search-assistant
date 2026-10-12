"""In-memory sliding-window rate limiter.

Good enough for a single instance (Render free tier runs one); counters reset
on restart. If the app is ever scaled to several instances, move this to
Redis or the database.
"""
import threading
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request, status


class RateLimiter:
    # Above this many tracked keys, expired ones are swept so memory stays
    # bounded under a flood of distinct IPs/emails.
    SWEEP_THRESHOLD = 10_000

    def __init__(self, max_events: int, window_seconds: int):
        self.max_events = max_events
        self.window = window_seconds
        self._events: dict[str, deque] = defaultdict(deque)
        self._lock = threading.Lock()

    def _prune(self, key: str, now: float) -> deque:
        q = self._events[key]
        while q and q[0] <= now - self.window:
            q.popleft()
        return q

    def _sweep(self, now: float) -> None:
        for key in [k for k, q in self._events.items() if not q or q[-1] <= now - self.window]:
            del self._events[key]

    def retry_after(self, key: str) -> int:
        """Seconds until `key` may try again, or 0 if it isn't limited."""
        now = time.monotonic()
        with self._lock:
            if key not in self._events:
                return 0
            q = self._prune(key, now)
            if not q:
                del self._events[key]
                return 0
            if len(q) < self.max_events:
                return 0
            return max(1, int(q[0] + self.window - now))

    def hit(self, key: str) -> None:
        now = time.monotonic()
        with self._lock:
            if len(self._events) >= self.SWEEP_THRESHOLD:
                self._sweep(now)
            self._prune(key, now).append(now)

    def reset(self, key: str) -> None:
        with self._lock:
            self._events.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._events.clear()


def client_ip(request: Request) -> str:
    """Best-effort real client IP, used only for rate limiting.

    On Render every request arrives from Render's proxy, so the socket address
    is the same for all users. Render sits behind Cloudflare, which sets
    CF-Connecting-IP itself (overwriting any client-supplied value); failing
    that, the rightmost X-Forwarded-For entry is the one the proxy appended.
    The leftmost entries are client-controlled and never trusted. Locally the
    socket address is used, since those headers would be spoofable.
    """
    from app.config import settings

    if settings.is_production:
        for header in ("cf-connecting-ip", "true-client-ip"):
            value = request.headers.get(header, "").strip()
            if value:
                return value
        forwarded = [h.strip() for h in request.headers.get("x-forwarded-for", "").split(",") if h.strip()]
        if forwarded:
            return forwarded[-1]
    return request.client.host if request.client else "unknown"


def enforce(limiter: RateLimiter, key: str, message: str) -> None:
    wait = limiter.retry_after(key)
    if wait:
        minutes = max(1, round(wait / 60))
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"{message} Try again in about {minutes} minute{'s' if minutes != 1 else ''}.",
            headers={"Retry-After": str(wait)},
        )


# Failed logins: per account (unspoofable) and per IP (catches spraying).
login_failures_by_email = RateLimiter(max_events=5, window_seconds=15 * 60)
login_attempts_by_ip = RateLimiter(max_events=30, window_seconds=15 * 60)
register_by_ip = RateLimiter(max_events=10, window_seconds=60 * 60)
reset_requests_by_email = RateLimiter(max_events=3, window_seconds=60 * 60)
reset_requests_by_ip = RateLimiter(max_events=10, window_seconds=60 * 60)
reset_attempts_by_ip = RateLimiter(max_events=20, window_seconds=15 * 60)
password_change_by_user = RateLimiter(max_events=5, window_seconds=15 * 60)

ALL_LIMITERS = [
    login_failures_by_email, login_attempts_by_ip, register_by_ip,
    reset_requests_by_email, reset_requests_by_ip, reset_attempts_by_ip,
    password_change_by_user,
]
