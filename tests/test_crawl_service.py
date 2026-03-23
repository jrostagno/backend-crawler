import unittest

from app.services.crawl_service import CrawlService


class FakeRepository:
    def __init__(self, is_new: bool = True) -> None:
        self.is_new = is_new
        self.increment_calls: list[list[str]] = []
        self.top = [{"word": "camera", "count": 3}]

    def mark_url_seen(self, url: str) -> bool:
        _ = url
        return self.is_new

    def increment_word_counts(self, words: list[str]) -> None:
        self.increment_calls.append(words)

    def top_words(self, limit: int) -> list[dict[str, int]]:
        return self.top[:limit]


class FakeAmazonClient:
    def fetch_description(self, url: str) -> str:
        _ = url
        return "The camera is fast and camera quality is great."


class TestCrawlService(unittest.TestCase):
    def test_process_url_processed(self) -> None:
        repository = FakeRepository(is_new=True)
        service = CrawlService(word_repository=repository, amazon_client=FakeAmazonClient())

        result = service.process_url("https://www.amazon.com/gp/product/B00VVOCSOU")

        self.assertEqual(result["status"], "processed")
        self.assertGreater(result["new_words"], 0)
        self.assertEqual(len(repository.increment_calls), 1)

    def test_process_url_already_seen(self) -> None:
        repository = FakeRepository(is_new=False)
        service = CrawlService(word_repository=repository, amazon_client=FakeAmazonClient())

        result = service.process_url("https://www.amazon.com/gp/product/B00VVOCSOU")

        self.assertEqual(result, {"status": "already_seen", "url": "https://www.amazon.com/gp/product/B00VVOCSOU", "new_words": 0})
        self.assertEqual(repository.increment_calls, [])

    def test_rejects_non_amazon_url(self) -> None:
        repository = FakeRepository()
        service = CrawlService(word_repository=repository, amazon_client=FakeAmazonClient())

        with self.assertRaises(ValueError):
            service.process_url("https://example.com/product")

    def test_top_words(self) -> None:
        repository = FakeRepository()
        service = CrawlService(word_repository=repository, amazon_client=FakeAmazonClient())

        result = service.get_top_words(limit=1)
        self.assertEqual(result, {"limit": 1, "words": [{"word": "camera", "count": 3}]})


if __name__ == "__main__":
    unittest.main()
