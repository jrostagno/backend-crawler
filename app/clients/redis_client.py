from redis import Redis

from app.core.settings import settings


class RedisClient:
    """Thin Redis client abstraction for repositories."""

    def __init__(self) -> None:
        self._client: Redis = Redis.from_url(settings.redis_url, decode_responses=True)

    @property
    def client(self) -> Redis:
        return self._client
