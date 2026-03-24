from functools import lru_cache
from typing import cast

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import HttpUrl

from app.clients.amazon_client import AmazonClient
from app.clients.redis_client import RedisClient
from app.core.rate_limiter import RateLimiterPort, RedisRateLimiter
from app.core.settings import settings
from app.repositories.word_repository import RedisClientPort, WordRepository
from app.schemas.crawl import CrawlResponse, TopWordsResponse
from app.services.crawl_service import CrawlService

router = APIRouter()


@lru_cache
def get_redis_client() -> RedisClient:
    return RedisClient()


@lru_cache
def get_crawl_service() -> CrawlService:
    redis_client = get_redis_client()
    repository = WordRepository(redis_client=cast(RedisClientPort, redis_client))
    amazon_client = AmazonClient()
    return CrawlService(word_repository=repository, amazon_client=amazon_client)


@lru_cache
def get_rate_limiter() -> RateLimiterPort:
    return RedisRateLimiter(redis_client=get_redis_client())


@router.get("/")
def read_root() -> dict[str, str]:
    return {"message": "API is running"}


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


def _crawl_product_url(
    product_url: HttpUrl,
    service: CrawlService,
) -> CrawlResponse:
    try:
        result = service.process_url(str(product_url))
        return CrawlResponse.model_validate(result)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except RuntimeError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error


def _client_identifier(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def _enforce_rate_limit(
    *,
    request: Request,
    rate_limiter: RateLimiterPort,
    route_key: str,
    limit: int,
) -> None:
    allowed, retry_after = rate_limiter.check(
        route_key=route_key,
        client_id=_client_identifier(request),
        limit=limit,
        window_seconds=settings.rate_limit_window_seconds,
    )
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded",
            headers={"Retry-After": str(retry_after)},
        )


@router.post("/crawl")
def crawl_url(
    request: Request,
    product_url: HttpUrl = Query(alias="productUrl"),
    service: CrawlService = Depends(get_crawl_service),
    rate_limiter: RateLimiterPort = Depends(get_rate_limiter),
) -> CrawlResponse:
    _enforce_rate_limit(
        request=request,
        rate_limiter=rate_limiter,
        route_key="crawl",
        limit=settings.rate_limit_crawl_per_minute,
    )
    return _crawl_product_url(product_url=product_url, service=service)


@router.get("/words/top")
def get_top_words(
    request: Request,
    limit: int = Query(default=10, ge=1, le=100),
    service: CrawlService = Depends(get_crawl_service),
    rate_limiter: RateLimiterPort = Depends(get_rate_limiter),
) -> TopWordsResponse:
    _enforce_rate_limit(
        request=request,
        rate_limiter=rate_limiter,
        route_key="words_top",
        limit=settings.rate_limit_top_words_per_minute,
    )
    try:
        result = service.get_top_words(limit=limit)
        return TopWordsResponse.model_validate(result)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
