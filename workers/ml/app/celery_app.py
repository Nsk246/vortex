from celery import Celery
from .config import get_settings
from .schemas import MediaJob
from .visual_juror import analyze_visual
from .audio_juror import analyze_audio


settings = get_settings()
celery_app = Celery("vortex_ml", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.task_routes = {
    "ml.visual.analyze": {"queue": "ml"},
    "ml.audio.analyze": {"queue": "ml"},
}


@celery_app.task(name="ml.visual.analyze")
def visual_task(job: dict) -> dict:
    return analyze_visual(MediaJob(**job)).model_dump()


@celery_app.task(name="ml.audio.analyze")
def audio_task(job: dict) -> dict:
    return analyze_audio(MediaJob(**job)).model_dump()

