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
    allowed_origins: str = (
        "http://localhost:8080,http://127.0.0.1:8080,"
        "http://localhost:5173,http://127.0.0.1:5173"
    )
    log_level: str = "INFO"
    env: str = "development"

    model_config = SettingsConfigDict(env_file=".env", env_prefix="CRAWLER_")

    @property
    def cors_allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


settings = Settings()
