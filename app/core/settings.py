from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    app_name: str = "Backend Challenge API"
    redis_url: str = "redis://localhost:6379/0"
    redis_seen_prefix: str = "crawler:seen"
    redis_word_scores_key: str = "crawler:word_scores"
    crawl_timeout_seconds: float = 10.0
    crawl_user_agent: str = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
    request_retries: int = 2

    model_config = SettingsConfigDict(env_file=".env", env_prefix="CRAWLER_")


settings = Settings()
