from pydantic import BaseModel, Field


class MediaJob(BaseModel):
    case_id: str
    media_asset_id: str
    storage_key: str
    filename: str
    content_type: str


class JurorFinding(BaseModel):
    juror_name: str
    confidence: float = Field(ge=0, le=1)
    weight: float = Field(ge=0, le=1)
    quality: dict
    evidence: list[dict]
    rationale: str
    model_versions: list[str]

