import time
from typing import Protocol


class RedisRateLimitCommandsPort(Protocol):
    def incr(self, key: str) -> int: ...
    def expire(self, key: str, time: int) -> bool: ...


class RedisRateLimitClientPort(Protocol):
    @property
    def client(self) -> RedisRateLimitCommandsPort: ...


class RateLimiterPort(Protocol):
    def check(
        self,
        *,
        route_key: str,
        client_id: str,
        limit: int,
        window_seconds: int,
    ) -> tuple[bool, int]: ...


class RedisRateLimiter:
    """Simple fixed-window rate limiter backed by Redis."""

    def __init__(self, redis_client: RedisRateLimitClientPort) -> None:
        self._redis_client = redis_client

    def check(
        self,
        *,
        route_key: str,
        client_id: str,
        limit: int,
        window_seconds: int,
    ) -> tuple[bool, int]:
        now = int(time.time())
        window_bucket = now // window_seconds
        key = f"crawler:ratelimit:{route_key}:{client_id}:{window_bucket}"

        count = int(self._redis_client.client.incr(key))
        if count == 1:
            self._redis_client.client.expire(key, window_seconds)

        retry_after = max(1, window_seconds - (now % window_seconds))
        return count <= limit, retry_after
