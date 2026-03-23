import hashlib
from typing import Protocol, TypedDict, cast

from app.core.settings import settings


class RedisPipelinePort(Protocol):
    def zincrby(self, key: str, amount: int, member: str) -> None: ...
    def execute(self) -> None: ...


class RedisCommandsPort(Protocol):
    def set(self, key: str, value: str, nx: bool = False) -> bool | None: ...
    def pipeline(self) -> RedisPipelinePort: ...
    def zrevrange(
        self, key: str, start: int, stop: int, withscores: bool = False
    ) -> list[tuple[str, float]]: ...


class RedisClientPort(Protocol):
    @property
    def client(self) -> RedisCommandsPort: ...


class TopWord(TypedDict):
    word: str
    count: int


class WordRepository:
    """Persistence wrapper for word counts and crawl dedup state."""

    def __init__(self, redis_client: RedisClientPort) -> None:
        self._redis_client = redis_client

    def mark_url_seen(self, url: str) -> bool:
        """Mark URL as seen once; returns True when URL is new."""
        url_hash = hashlib.sha256(url.encode("utf-8")).hexdigest()
        redis_key = f"{settings.redis_seen_prefix}:{url_hash}"
        was_set = self._redis_client.client.set(redis_key, "1", nx=True)
        return bool(was_set)

    def increment_word_counts(self, words: list[str]) -> None:
        """Increment per-word counters in Redis sorted set."""
        if not words:
            return

        pipeline = self._redis_client.client.pipeline()
        for word in words:
            pipeline.zincrby(settings.redis_word_scores_key, 1, word)
        pipeline.execute()

    def top_words(self, limit: int) -> list[TopWord]:
        """Fetch top words ordered by frequency desc."""
        if limit <= 0:
            return []

        raw = cast(
            list[tuple[str, float]],
            self._redis_client.client.zrevrange(
                settings.redis_word_scores_key,
                0,
                limit - 1,
                withscores=True,
            ),
        )
        return [{"word": word, "count": int(score)} for word, score in raw]
