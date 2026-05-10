import json
import redis
from .config import get_settings


settings = get_settings()


def redis_client() -> redis.Redis:
    return redis.from_url(settings.redis_url, decode_responses=True)


def case_channel(case_id: str) -> str:
    return f"case:{case_id}:events"


def publish_case_event(case_id: str, event: dict) -> None:
    redis_client().publish(case_channel(case_id), json.dumps(event, default=str))

