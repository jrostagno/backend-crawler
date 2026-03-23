import unittest

from fastapi.testclient import TestClient

from main import app
from app.controllers.crawl_controller import get_crawl_service


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


class TestCrawlController(unittest.TestCase):
    def setUp(self) -> None:
        app.dependency_overrides[get_crawl_service] = lambda: FakeService()
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

    def test_crawl_accepts_product_url_query_param_on_root_path(self) -> None:
        response = self.client.post(
            "/",
            params={"productUrl": "https://www.amazon.com/gp/product/B00VVOCSOU"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "processed")
        self.assertEqual(data["new_words"], 5)
        self.assertEqual(data["description"], "sample description")


if __name__ == "__main__":
    unittest.main()
