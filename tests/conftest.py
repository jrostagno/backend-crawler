from collections.abc import Iterator

import httpx
import pytest
from fastapi.testclient import TestClient

from app.clients.amazon_client import AmazonClient
from app.controllers.crawl_controller import get_crawl_service, get_rate_limiter
from app.repositories.word_repository import WordRepository
from app.services.crawl_service import CrawlService
from main import app

class FakePipeline:
    """Pipeline en memoria para simular operaciones batch de Redis."""

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
    """Redis fake en memoria para tests de flujo sin infraestructura externa."""

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
    """Cliente fake que expone API compatible con WordRepository."""

    def __init__(self) -> None:
        self.client = FakeRedis()


class AllowAllRateLimiter:
    """Rate limiter fake que siempre permite requests."""

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


class DummyResponse:
    """Minimal fake response compatible with AmazonClient."""

    def __init__(self, text: str, status_code: int = 200) -> None:
        self.text = text
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                f"{self.status_code} error",
                request=httpx.Request("GET", "https://www.amazon.com"),
                response=httpx.Response(self.status_code),
            )


@pytest.fixture
def test_client() -> Iterator[TestClient]:
    """
    Entrega un cliente FastAPI con servicio real (service + repository + client),
    reemplazando Redis y rate limiter por fakes para test controlado.
    """
    service = CrawlService(
        word_repository=WordRepository(redis_client=FakeRedisClient()),
        amazon_client=AmazonClient(),
    )

    app.dependency_overrides[get_crawl_service] = lambda: service
    app.dependency_overrides[get_rate_limiter] = lambda: AllowAllRateLimiter()

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
def mock_httpx_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mockea httpx.get para simular HTML válido de Amazon sin red externa."""
    html = """
    <html>
      <div id="productDescription">Camera rápida con gran batería y lente nítida</div>
    </html>
    """

    def fake_get(
        url: str,
        timeout: float,
        headers: dict[str, str],
        follow_redirects: bool,
    ) -> DummyResponse:
        _ = (url, timeout, headers, follow_redirects)
        return DummyResponse(text=html, status_code=200)

    monkeypatch.setattr("app.clients.amazon_client.httpx.get", fake_get)


@pytest.fixture
def mock_httpx_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mockea httpx.get para simular caída de red del proveedor externo."""

    def fake_get(*args: object, **kwargs: object) -> DummyResponse:
        _ = (args, kwargs)
        raise httpx.ConnectError("network down")

    monkeypatch.setattr("app.clients.amazon_client.httpx.get", fake_get)
    # Evita esperas por retries durante tests de error.
    monkeypatch.setattr("app.clients.amazon_client.time.sleep", lambda *_: None)
