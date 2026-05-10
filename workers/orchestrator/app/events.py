import json
import redis
from .config import get_settings


settings = get_settings()


def client() -> redis.Redis:
    return redis.from_url(settings.redis_url, decode_responses=True)


def publish(case_id: str, event_type: str, actor: str, message: str, payload: dict | None = None) -> None:
    event = {
        "case_id": case_id,
        "event_type": event_type,
        "actor": actor,
        "message": message,
        "payload": payload or {},
    }
    client().publish(f"case:{case_id}:events", json.dumps(event, default=str))

