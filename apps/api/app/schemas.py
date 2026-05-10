from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=10)
    full_name: str = Field(min_length=2, max_length=160)
    organization_name: str = Field(min_length=2, max_length=160)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    org_id: str
    role: str


class CaseCreate(BaseModel):
    title: str = Field(min_length=2, max_length=200)


class CaseResponse(BaseModel):
    id: str
    title: str
    status: str
    risk_score: float | None
    verdict_label: str | None
    created_at: datetime


class MediaResponse(BaseModel):
    id: str
    filename: str
    content_type: str
    size_bytes: int
    sha256: str


class RunResponse(BaseModel):
    case_id: str
    status: str
    task_id: str


class AuditEventResponse(BaseModel):
    id: str
    event_type: str
    actor: str
    message: str
    payload: dict
    created_at: datetime


class VerdictResponse(BaseModel):
    final_confidence: float
    label: str
    disagreement_score: float
    reexamination_triggered: bool
    rationale: str
    weights: dict


class CaseDetailResponse(CaseResponse):
    media_assets: list[MediaResponse]
    audit_events: list[AuditEventResponse]
    verdict: VerdictResponse | None = None

