from urllib.parse import urlparse
from typing import Mapping, NotRequired, Protocol, Sequence, TypedDict

from app.core.text_processing import tokenize_text


class WordRepositoryPort(Protocol):
    def mark_url_seen(self, url: str) -> bool: ...
    def increment_word_counts(self, words: list[str]) -> None: ...
    def top_words(self, limit: int) -> Sequence[Mapping[str, object]]: ...


class AmazonClientPort(Protocol):
    def fetch_description(self, url: str) -> str: ...


class TopWord(TypedDict):
    word: str
    count: int


class ProcessUrlResult(TypedDict):
    status: str
    url: str
    new_words: int
    description: NotRequired[str]


class TopWordsResult(TypedDict):
    limit: int
    words: list[TopWord]


class CrawlService:
    """Coordinates crawling and word-count operations."""

    def __init__(
        self,
        word_repository: WordRepositoryPort,
        amazon_client: AmazonClientPort,
    ) -> None:
        self._word_repository = word_repository
        self._amazon_client = amazon_client

    def process_url(self, url: str) -> ProcessUrlResult:
        """Validate, deduplicate, crawl, and persist counts."""
        if not self._is_valid_amazon_url(url):
            raise ValueError("Only Amazon product URLs are supported.")

        is_new = self._word_repository.mark_url_seen(url)
        if not is_new:
            return {"status": "already_seen", "url": url, "new_words": 0}

        description = self._amazon_client.fetch_description(url)
        words = tokenize_text(description)
        self._word_repository.increment_word_counts(words)

        result: ProcessUrlResult = {"status": "processed", "url": url, "new_words": len(words)}
        if description:
            result["description"] = description[:500]
        return result

    def get_top_words(self, limit: int = 10) -> TopWordsResult:
        """Fetch top N words from repository."""
        if limit <= 0:
            raise ValueError("limit must be greater than zero")

        raw_words = self._word_repository.top_words(limit=limit)
        words: list[TopWord] = []
        for item in raw_words:
            raw_count = item.get("count")
            if isinstance(raw_count, bool):
                count = int(raw_count)
            elif isinstance(raw_count, (int, float, str)):
                count = int(raw_count)
            else:
                count = 0
            words.append({"word": str(item.get("word", "")), "count": count})
        return {"limit": limit, "words": words}

    def _is_valid_amazon_url(self, url: str) -> bool:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            return False
        host = parsed.netloc.lower()
        return "amazon." in host
