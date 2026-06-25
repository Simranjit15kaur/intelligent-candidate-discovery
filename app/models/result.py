from pydantic import BaseModel
import uuid
from datetime import datetime
from app.db.models import ScanStatus


class RankedCandidateResult(BaseModel):
    candidate_id: uuid.UUID
    name: str
    rank: int
    final_score: float
    semantic_sim: float | None
    skill_overlap: float | None
    exp_fit: float | None
    activity_score: float | None
    matched_skills: list[str]
    gaps: list[str]
    justification: str | None

    model_config = {"from_attributes": True}


class PipelineRunRead(BaseModel):
    run_id: uuid.UUID
    job_id: uuid.UUID
    status: ScanStatus
    created_at: datetime
    completed_at: datetime | None
    error: str | None
    results: list[RankedCandidateResult] = []

    model_config = {"from_attributes": True}