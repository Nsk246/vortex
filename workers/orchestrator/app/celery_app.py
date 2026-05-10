from datetime import datetime
import uuid
from celery import Celery
from celery.result import allow_join_result
from sqlalchemy import select
from .config import get_settings
from .context_juror import analyze_context
from .db import AuditEvent, Case, JudgeVerdict, JurorRun, MediaAsset, SessionLocal
from .events import publish
from .judge import JurorDecision, weighted_consensus


settings = get_settings()
celery_app = Celery("vortex_orchestrator", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.task_routes = {
    "orchestrator.run_tribunal": {"queue": "orchestration"},
    "ml.visual.analyze": {"queue": "ml"},
    "ml.audio.analyze": {"queue": "ml"},
}


def _audit(db, case_id: str, event_type: str, actor: str, message: str, payload: dict | None = None) -> None:
    db.add(
        AuditEvent(
            id=str(uuid.uuid4()),
            case_id=case_id,
            event_type=event_type,
            actor=actor,
            message=message,
            payload=payload or {},
            created_at=datetime.utcnow(),
        )
    )
    publish(case_id, event_type, actor, message, payload)


def _upsert_juror(db, case_id: str, name: str, result: dict, round_number: int = 1) -> None:
    existing = db.scalar(
        select(JurorRun).where(
            JurorRun.case_id == case_id,
            JurorRun.juror_name == name,
            JurorRun.round == round_number,
        )
    )
    run = existing or JurorRun(
        id=str(uuid.uuid4()),
        case_id=case_id,
        juror_name=name,
        round=round_number,
        created_at=datetime.utcnow(),
    )
    run.status = "complete"
    run.confidence = float(result["confidence"])
    run.weight = float(result["weight"])
    run.result = result
    run.completed_at = datetime.utcnow()
    db.add(run)


def _media_job(case_id: str, asset: MediaAsset) -> dict:
    return {
        "case_id": case_id,
        "media_asset_id": asset.id,
        "storage_key": asset.storage_key,
        "filename": asset.filename,
        "content_type": asset.content_type,
    }


def _mark_failed(case_id: str, error: Exception) -> None:
    with SessionLocal() as db:
        case = db.scalar(select(Case).where(Case.id == case_id))
        if case:
            case.status = "failed"
            case.updated_at = datetime.utcnow()
        _audit(
            db,
            case_id,
            "tribunal.failed",
            "judge",
            "Tribunal stopped after a juror runtime failure.",
            {"error": str(error), "error_type": type(error).__name__},
        )
        db.commit()


@celery_app.task(name="orchestrator.run_tribunal", bind=True)
def run_tribunal(self, case_id: str, org_id: str) -> dict:
    with SessionLocal() as db:
        case = db.scalar(select(Case).where(Case.id == case_id, Case.org_id == org_id))
        if not case:
            raise RuntimeError("Case not found or org mismatch")
        asset = db.scalar(select(MediaAsset).where(MediaAsset.case_id == case_id))
        if not asset:
            raise RuntimeError("No media asset found for case")

        case.status = "processing"
        case.updated_at = datetime.utcnow()
        _audit(db, case_id, "tribunal.started", "judge", "Tribunal opened and evidence admitted.", {"asset_id": asset.id})
        db.commit()

    job = _media_job(case_id, asset)
    publish(case_id, "jurors.queued", "judge", "Visual and acoustic jurors assigned to ML worker queue.", {})
    visual_async = celery_app.send_task("ml.visual.analyze", args=[job])
    audio_async = celery_app.send_task("ml.audio.analyze", args=[job])
    try:
        with allow_join_result():
            visual = visual_async.get(timeout=settings.juror_timeout_seconds)
            audio = audio_async.get(timeout=settings.juror_timeout_seconds)
    except Exception as exc:
        _mark_failed(case_id, exc)
        raise

    with SessionLocal() as db:
        _upsert_juror(db, case_id, "visual", visual)
        _audit(db, case_id, "juror.complete", "visual", visual["rationale"], visual)
        _upsert_juror(db, case_id, "acoustic", audio)
        _audit(db, case_id, "juror.complete", "acoustic", audio["rationale"], audio)
        db.commit()

    preliminary = weighted_consensus(
        [
            JurorDecision("visual", float(visual["confidence"]), float(visual["weight"]), visual.get("quality", {}), visual["rationale"]),
            JurorDecision("acoustic", float(audio["confidence"]), float(audio["weight"]), audio.get("quality", {}), audio["rationale"]),
        ],
        disagreement_threshold=settings.disagreement_threshold,
    )
    publish(
        case_id,
        "judge.preliminary",
        "judge",
        preliminary.rationale,
        {
            "final_confidence": preliminary.final_confidence,
            "disagreement_score": preliminary.disagreement_score,
            "reexamination_triggered": preliminary.reexamination_triggered,
        },
    )

    context = analyze_context(
        transcript=None,
        visual_summary=visual,
        audio_summary=audio,
        contested=preliminary.reexamination_triggered,
    )

    with SessionLocal() as db:
        context_result = {
            "juror_name": "context",
            "confidence": float(context.get("confidence", 0.5)),
            "weight": float(context.get("weight", 0.35)),
            "quality": context.get("quality", {"llm_model": settings.openai_contested_model if preliminary.reexamination_triggered else settings.openai_reasoning_model}),
            "evidence": context.get("evidence", []),
            "rationale": context.get("rationale", "Context juror completed semantic review."),
            "model_versions": [settings.openai_contested_model if preliminary.reexamination_triggered else settings.openai_reasoning_model],
        }
        _upsert_juror(db, case_id, "context", context_result)
        _audit(db, case_id, "juror.complete", "context", context_result["rationale"], context_result)

        verdict = weighted_consensus(
            [
                JurorDecision("visual", float(visual["confidence"]), float(visual["weight"]), visual.get("quality", {}), visual["rationale"]),
                JurorDecision("acoustic", float(audio["confidence"]), float(audio["weight"]), audio.get("quality", {}), audio["rationale"]),
                JurorDecision("context", float(context_result["confidence"]), float(context_result["weight"]), context_result["quality"], context_result["rationale"]),
            ],
            disagreement_threshold=settings.disagreement_threshold,
        )
        db.add(
            JudgeVerdict(
                id=str(uuid.uuid4()),
                case_id=case_id,
                final_confidence=verdict.final_confidence,
                label=verdict.label,
                disagreement_score=verdict.disagreement_score,
                reexamination_triggered=verdict.reexamination_triggered,
                rationale=verdict.rationale,
                weights=verdict.weights,
                created_at=datetime.utcnow(),
            )
        )
        case = db.scalar(select(Case).where(Case.id == case_id))
        case.status = "complete"
        case.risk_score = verdict.final_confidence
        case.verdict_label = verdict.label
        case.updated_at = datetime.utcnow()
        _audit(
            db,
            case_id,
            "judge.verdict",
            "judge",
            verdict.rationale,
            {
                "final_confidence": verdict.final_confidence,
                "label": verdict.label,
                "disagreement_score": verdict.disagreement_score,
                "weights": verdict.weights,
            },
        )
        db.commit()
        return {
            "case_id": case_id,
            "status": "complete",
            "final_confidence": verdict.final_confidence,
            "label": verdict.label,
        }
