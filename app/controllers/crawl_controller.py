from functools import lru_cache
from typing import cast

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import HttpUrl

from app.clients.amazon_client import AmazonClient
from app.clients.redis_client import RedisClient
from app.repositories.word_repository import RedisClientPort, WordRepository
from app.schemas.crawl import CrawlResponse, TopWordsResponse
from app.services.crawl_service import CrawlService

router = APIRouter()


@lru_cache
def get_crawl_service() -> CrawlService:
    redis_client = RedisClient()
    repository = WordRepository(redis_client=cast(RedisClientPort, redis_client))
    amazon_client = AmazonClient()
    return CrawlService(word_repository=repository, amazon_client=amazon_client)


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


@router.post("/crawl")
def crawl_url(
    product_url: HttpUrl = Query(alias="productUrl"),
    service: CrawlService = Depends(get_crawl_service),
) -> CrawlResponse:
    return _crawl_product_url(product_url=product_url, service=service)


@router.get("/words/top")
def get_top_words(
    limit: int = Query(default=10, ge=1, le=100),
    service: CrawlService = Depends(get_crawl_service),
) -> TopWordsResponse:
    try:
        result = service.get_top_words(limit=limit)
        return TopWordsResponse.model_validate(result)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
