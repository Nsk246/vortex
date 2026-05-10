from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    database_url: str = "sqlite:///./vortex.db"
    redis_url: str = "redis://localhost:6379/0"
    openai_api_key: str | None = None
    openai_reasoning_model: str = "gpt-5.4-mini"
    openai_contested_model: str = "gpt-5.5"
    search_api_key: str | None = None
    search_endpoint: str | None = None
    disagreement_threshold: float = 0.45
    juror_timeout_seconds: int = 900


@lru_cache
def get_settings() -> Settings:
    return Settings()

