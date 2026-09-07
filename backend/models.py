from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, JSON, Column


class Job(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: str
    session_id: str = Field(index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Candidate(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    job_id: int = Field(foreign_key="job.id")
    name: str
    title: Optional[str] = None
    company: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    source: str = "mock"
    raw_json: dict = Field(default={}, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)


class CallRecord(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    candidate_id: int = Field(foreign_key="candidate.id")
    hunar_call_id: Optional[str] = None
    status: str = "NOT_STARTED"
    lifecycle_status: str = "NOT_STARTED"
    recording_url: Optional[str] = None
    result: dict = Field(default={}, sa_column=Column(JSON))
    transcript_summary: Optional[str] = None
    duration_minutes: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)