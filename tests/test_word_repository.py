import unittest

from app.core.settings import settings
from app.repositories.word_repository import WordRepository


class FakePipeline:
    def __init__(self, redis_client: "FakeRedis") -> None:
        self._redis_client = redis_client
        self._ops: list[tuple[str, int, str]] = []

    def zincrby(self, key: str, amount: int, member: str) -> None:
        self._ops.append((key, amount, member))

    def execute(self) -> None:
        for key, amount, member in self._ops:
            bucket = self._redis_client.sorted_sets.setdefault(key, {})
            bucket[member] = bucket.get(member, 0) + amount


class FakeRedis:
    def __init__(self) -> None:
        self.kv: dict[str, str] = {}
        self.sorted_sets: dict[str, dict[str, int]] = {}

    def set(self, key: str, value: str, nx: bool = False) -> bool | None:
        if nx and key in self.kv:
            return None
        self.kv[key] = value
        return True

    def pipeline(self) -> FakePipeline:
        return FakePipeline(self)

    def zrevrange(
        self,
        key: str,
        start: int,
        stop: int,
        withscores: bool = False,
    ) -> list[tuple[str, float]]:
        _ = withscores
        items = list(self.sorted_sets.get(key, {}).items())
        items.sort(key=lambda item: item[1], reverse=True)
        sliced = items[start : stop + 1]
        return [(word, float(score)) for word, score in sliced]


class FakeRedisClient:
    def __init__(self) -> None:
        self.client = FakeRedis()


class TestWordRepository(unittest.TestCase):
    def test_mark_url_seen_deduplicates(self) -> None:
        repository = WordRepository(redis_client=FakeRedisClient())
        url = "https://www.amazon.com/gp/product/B00VVOCSOU"

        self.assertTrue(repository.mark_url_seen(url))
        self.assertFalse(repository.mark_url_seen(url))

    def test_increment_and_top_words(self) -> None:
        repository = WordRepository(redis_client=FakeRedisClient())
        repository.increment_word_counts(["camera", "camera", "light"])

        top = repository.top_words(limit=2)
        self.assertEqual(top, [{"word": "camera", "count": 2}, {"word": "light", "count": 1}])

    def test_top_words_with_invalid_limit(self) -> None:
        repository = WordRepository(redis_client=FakeRedisClient())
        self.assertEqual(repository.top_words(limit=0), [])

    def test_word_scores_are_saved_under_configured_key(self) -> None:
        client = FakeRedisClient()
        repository = WordRepository(redis_client=client)
        repository.increment_word_counts(["camera"])

        self.assertIn(settings.redis_word_scores_key, client.client.sorted_sets)


if __name__ == "__main__":
    unittest.main()
