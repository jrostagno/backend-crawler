from pydantic import BaseModel, HttpUrl, conint


class CrawlRequest(BaseModel):
    url: HttpUrl


class CrawlResponse(BaseModel):
    status: str
    url: str
    new_words: int
    description: str | None = None


class TopWord(BaseModel):
    word: str
    count: int


class TopWordsResponse(BaseModel):
    limit: conint(gt=0)  # type: ignore[valid-type]
    words: list[TopWord]
