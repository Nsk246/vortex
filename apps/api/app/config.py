from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    database_url: str = "sqlite:///./vortex.db"
    redis_url: str = "redis://localhost:6379/0"
    jwt_secret: str = Field(default="development-secret-change-me")
    jwt_issuer: str = "vortex"
    access_token_minutes: int = 1440

    s3_endpoint_url: str | None = None
    s3_bucket: str = "vortex-media"
    s3_access_key_id: str | None = None
    s3_secret_access_key: str | None = None
    s3_region: str = "us-east-1"

    free_monthly_analyses: int = 5
    free_max_file_mb: int = 150
    free_max_duration_seconds: int = 180
    paid_max_file_mb: int = 2048
    paid_max_duration_seconds: int = 3600
    cors_origins: str = "http://localhost:3000"

    orchestrator_task_name: str = "orchestrator.run_tribunal"

    def validate_production(self) -> None:
        missing = []
        if self.app_env == "production":
            if len(self.jwt_secret) < 48:
                missing.append("JWT_SECRET length >= 48")
            for key, value in {
                "DATABASE_URL": self.database_url,
                "REDIS_URL": self.redis_url,
                "S3_ENDPOINT_URL": self.s3_endpoint_url,
                "S3_ACCESS_KEY_ID": self.s3_access_key_id,
                "S3_SECRET_ACCESS_KEY": self.s3_secret_access_key,
            }.items():
                if not value:
                    missing.append(key)
        if missing:
            raise RuntimeError(f"Production configuration missing: {', '.join(missing)}")


@lru_cache
def get_settings() -> Settings:
    return Settings()
