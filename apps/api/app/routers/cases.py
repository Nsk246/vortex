import hashlib
from datetime import datetime
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import extract, func, select
from sqlalchemy.orm import Session, selectinload
from celery import Celery
from app.config import get_settings
from app.database import get_db
from app.dependencies import get_current_user
from app.models import AuditEvent, Case, JudgeVerdict, MediaAsset, User
from app.schemas import CaseCreate, CaseDetailResponse, CaseResponse, MediaResponse, RunResponse
from app.storage import upload_bytes


router = APIRouter(prefix="/api/v1/cases", tags=["cases"])
settings = get_settings()
celery_app = Celery("vortex_api", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.broker_connection_timeout = 5
celery_app.conf.task_publish_retry = False

ALLOWED_CONTENT_TYPES = {
    "video/mp4",
    "video/quicktime",
    "audio/mpeg",
    "audio/wav",
    "audio/x-wav",
}


def current_month_usage(db: Session, org_id: str) -> int:
    now = datetime.utcnow()
    return db.scalar(
        select(func.count(Case.id)).where(
            Case.org_id == org_id,
            extract("year", Case.created_at) == now.year,
            extract("month", Case.created_at) == now.month,
            Case.status != "draft",
        )
    ) or 0


def case_to_response(case: Case) -> CaseResponse:
    return CaseResponse(
        id=case.id,
        title=case.title,
        status=case.status,
        risk_score=case.risk_score,
        verdict_label=case.verdict_label,
        created_at=case.created_at,
    )


@router.post("", response_model=CaseResponse)
def create_case(payload: CaseCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_month_usage(db, user.org_id) >= user.organization.monthly_quota:
        raise HTTPException(status_code=429, detail="Monthly analysis quota reached")
    case = Case(org_id=user.org_id, created_by_id=user.id, title=payload.title, status="draft")
    db.add(case)
    db.commit()
    db.refresh(case)
    return case_to_response(case)


@router.get("", response_model=list[CaseResponse])
def list_cases(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    cases = db.scalars(select(Case).where(Case.org_id == user.org_id).order_by(Case.created_at.desc())).all()
    return [case_to_response(case) for case in cases]


@router.post("/{case_id}/media", response_model=MediaResponse)
async def upload_media(
    case_id: str,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    case = db.scalar(select(Case).where(Case.id == case_id, Case.org_id == user.org_id))
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=415, detail="Unsupported media type")
    body = await file.read()
    max_mb = settings.free_max_file_mb if user.organization.plan == "free" else settings.paid_max_file_mb
    if len(body) > max_mb * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"File exceeds {max_mb}MB limit for this plan")

    digest = hashlib.sha256(body).hexdigest()
    key = f"orgs/{user.org_id}/cases/{case.id}/original/{digest}-{file.filename}"
    upload_bytes(key, body, file.content_type or "application/octet-stream")
    asset = MediaAsset(
        case_id=case.id,
        storage_key=key,
        filename=file.filename or "evidence",
        content_type=file.content_type or "application/octet-stream",
        size_bytes=len(body),
        sha256=digest,
    )
    case.status = "uploaded"
    case.updated_at = datetime.utcnow()
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return MediaResponse(
        id=asset.id,
        filename=asset.filename,
        content_type=asset.content_type,
        size_bytes=asset.size_bytes,
        sha256=asset.sha256,
    )


@router.post("/{case_id}/run", response_model=RunResponse)
def run_case(case_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> RunResponse:
    case = db.scalar(
        select(Case)
        .options(selectinload(Case.media_assets))
        .where(Case.id == case_id, Case.org_id == user.org_id)
    )
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    if not case.media_assets:
        raise HTTPException(status_code=400, detail="Upload media before starting tribunal")
    case.status = "queued"
    case.updated_at = datetime.utcnow()
    db.commit()
    try:
        task = celery_app.send_task(
            settings.orchestrator_task_name,
            args=[case.id, user.org_id],
            queue=settings.orchestrator_queue_name,
        )
    except Exception as exc:
        case.status = "uploaded"
        case.updated_at = datetime.utcnow()
        db.commit()
        raise HTTPException(status_code=503, detail=f"Could not enqueue tribunal task: {exc}") from exc
    return RunResponse(case_id=case.id, status="queued", task_id=task.id)


@router.get("/{case_id}", response_model=CaseDetailResponse)
def get_case(case_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    case = db.scalar(
        select(Case)
        .options(selectinload(Case.media_assets), selectinload(Case.audit_events), selectinload(Case.verdict))
        .where(Case.id == case_id, Case.org_id == user.org_id)
    )
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    verdict = None
    if case.verdict:
        verdict = {
            "final_confidence": case.verdict.final_confidence,
            "label": case.verdict.label,
            "disagreement_score": case.verdict.disagreement_score,
            "reexamination_triggered": case.verdict.reexamination_triggered,
            "rationale": case.verdict.rationale,
            "weights": case.verdict.weights,
        }
    return CaseDetailResponse(
        **case_to_response(case).model_dump(),
        media_assets=[
            MediaResponse(
                id=asset.id,
                filename=asset.filename,
                content_type=asset.content_type,
                size_bytes=asset.size_bytes,
                sha256=asset.sha256,
            )
            for asset in case.media_assets
        ],
        audit_events=[
            {
                "id": event.id,
                "event_type": event.event_type,
                "actor": event.actor,
                "message": event.message,
                "payload": event.payload,
                "created_at": event.created_at,
            }
            for event in sorted(case.audit_events, key=lambda item: item.created_at)
        ],
        verdict=verdict,
    )
