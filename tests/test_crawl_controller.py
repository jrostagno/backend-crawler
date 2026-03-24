import unittest

from fastapi.testclient import TestClient

from main import app
from app.controllers.crawl_controller import get_crawl_service, get_rate_limiter


class FakeService:
    def process_url(self, url: str) -> dict[str, object]:
        return {
            "status": "processed",
            "url": url,
            "new_words": 5,
            "description": "sample description",
        }

    def get_top_words(self, limit: int = 10) -> dict[str, object]:
        return {"limit": limit, "words": [{"word": "camera", "count": 5}]}


class AllowAllRateLimiter:
    def check(
        self,
        *,
        route_key: str,
        client_id: str,
        limit: int,
        window_seconds: int,
    ) -> tuple[bool, int]:
        _ = (route_key, client_id, limit, window_seconds)
        return True, 1


class BlockAllRateLimiter:
    def check(
        self,
        *,
        route_key: str,
        client_id: str,
        limit: int,
        window_seconds: int,
    ) -> tuple[bool, int]:
        _ = (route_key, client_id, limit, window_seconds)
        return False, 42


class TestCrawlController(unittest.TestCase):
    def setUp(self) -> None:
        app.dependency_overrides[get_crawl_service] = lambda: FakeService()
        app.dependency_overrides[get_rate_limiter] = lambda: AllowAllRateLimiter()
        self.client = TestClient(app)

    def tearDown(self) -> None:
        app.dependency_overrides.clear()

    def test_crawl_accepts_product_url_query_param_on_crawl_path(self) -> None:
        response = self.client.post(
            "/crawl",
            params={"productUrl": "https://www.amazon.com/gp/product/B00VVOCSOU"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "processed")
        self.assertEqual(data["new_words"], 5)
        self.assertEqual(data["description"], "sample description")

    def test_top_words_returns_data(self) -> None:
        response = self.client.get("/words/top", params={"limit": 1})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"limit": 1, "words": [{"word": "camera", "count": 5}]})

    def test_rate_limit_returns_429_on_crawl(self) -> None:
        app.dependency_overrides[get_rate_limiter] = lambda: BlockAllRateLimiter()

        response = self.client.post(
            "/crawl",
            params={"productUrl": "https://www.amazon.com/gp/product/B00VVOCSOU"},
        )

        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.json()["detail"], "Rate limit exceeded")
        self.assertEqual(response.headers.get("retry-after"), "42")

    def test_rate_limit_returns_429_on_top_words(self) -> None:
        app.dependency_overrides[get_rate_limiter] = lambda: BlockAllRateLimiter()

        response = self.client.get("/words/top")

        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.json()["detail"], "Rate limit exceeded")
        self.assertEqual(response.headers.get("retry-after"), "42")


if __name__ == "__main__":
    unittest.main()
