
from sqlalchemy import DateTime
import uuid

from sqlmodel import Field, SQLModel
from sqlalchemy import Column, JSON
from datetime import datetime , timezone
from enum import Enum

def get_datetime_utc() -> datetime:
    return datetime.now(timezone.utc)


class Jobs(SQLModel, table = True):
    __tablename__ = "jobs"
    id : uuid.UUID | None = Field(default_factory= uuid.uuid4, primary_key= True)
    title: str = Field(index = True)
    description: str | None = Field(default = None, index = True)
    required_skills : list[str] = Field(
        default_factory = list,
        sa_column = Column(JSON)
    )
    min_experience: float = Field(ge = 0)
    required_certs : list[str] | None = Field(
        default = None, 
        sa_column = Column(JSON)) 
    created_at: datetime = Field(
        default_factory= get_datetime_utc,
        sa_type = DateTime(timezone = True)
    )

class Candidates(SQLModel, table = True):
    __tablename__ = "candidates"
    id : uuid.UUID = Field(default_factory = uuid.uuid4, primary_key = True)
    name: str = Field(index = True, min_length=1, max_length=255)
    profile_text: str 
    skills : list[str] | None = Field(
        default = None,
        sa_column = Column(JSON)
    )
    years_experience: float = Field(ge = 0)
    certifications : list[str] | None = Field(
        default = None,
        sa_column = Column(JSON)
    )
    last_active: datetime| None = Field(
        default = None,
        sa_type = DateTime(timezone = True)
    )
    profile_complete : float = Field(ge = 0.0, le = 1.0)
    raw_data: dict | None = Field(
        default = None,
        sa_column = Column(JSON)
    )
    created_at: datetime = Field(
        default_factory= get_datetime_utc,
        sa_type = DateTime(timezone = True)
    )


class RunStatus(str, Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"

class PipelineRun(SQLModel, table = True):
    __tablename__ = "pipeline_runs"
    id: uuid.UUID = Field(default_factory= uuid.uuid4, primary_key = True)
    job_id : uuid.UUID = Field(default = None, foreign_key= 'jobs.id')
    status : RunStatus = Field(default = RunStatus.pending)
    created_at: datetime = Field(
        default_factory= get_datetime_utc,
        sa_type = DateTime(timezone = True)
    )
    completed_at : datetime | None = Field(
        default = None,
        sa_type = DateTime(timezone = True)
    )
    error: str | None = Field(default = None)

class RankedResult(SQLModel, table = True):
    __tablename__ = "ranked_results"
    id: uuid.UUID = Field(default_factory = uuid.uuid4, primary_key = True)
    run_id: uuid.UUID = Field(default = None, foreign_key = 'pipeline_runs.id')
    candidate_id: uuid.UUID = Field(default = None, foreign_key = 'candidates.id')
    rank: int  
    final_score: float 
    semantic_sim : float = Field(default = None)
    skill_overlap : float = Field(default = None)
    exp_fit : float = Field(default = None)
    activity_score : float = Field(default = None)
    matched_skills : list[str] = Field(
        default_factory = list,
        sa_column = Column(JSON)
    )
    gaps : list[str] = Field(
        default_factory = list,
        sa_column = Column(JSON)
    )
    justification : str = Field(default = None)
    created_at: datetime = Field(
        default_factory= get_datetime_utc,
        sa_type = DateTime(timezone = True)
    )



    
