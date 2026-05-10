from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    redis_url: str = "redis://localhost:6379/0"
    app_env: str = "development"
    s3_endpoint_url: str | None = None
    s3_bucket: str = "vortex-media"
    s3_access_key_id: str | None = None
    s3_secret_access_key: str | None = None
    s3_region: str = "us-east-1"

    visual_face_model_path: str | None = None
    visual_general_model_path: str | None = None
    visual_model_license: str = "unreviewed"
    audio_model_id: str | None = None
    audio_model_license: str = "unreviewed"
    allow_remote_model_downloads: bool = False
    max_video_frames: int = 96
    audio_window_seconds: int = 4

    def require_production_models(self) -> None:
        missing = []
        if not self.visual_face_model_path:
            missing.append("VISUAL_FACE_MODEL_PATH")
        if not self.visual_general_model_path:
            missing.append("VISUAL_GENERAL_MODEL_PATH")
        if not self.audio_model_id:
            missing.append("AUDIO_MODEL_ID")
        if self.app_env == "production":
            if self.visual_model_license != "production-approved":
                missing.append("VISUAL_MODEL_LICENSE=production-approved")
            if self.audio_model_license != "production-approved":
                missing.append("AUDIO_MODEL_LICENSE=production-approved")
        if missing:
            raise RuntimeError(f"ML worker missing required production model configuration: {', '.join(missing)}")


@lru_cache
def get_settings() -> Settings:
    return Settings()
