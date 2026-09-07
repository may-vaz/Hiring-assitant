from datetime import datetime
from pydantic import BaseModel
from typing import Optional


class JobCreateRequest(BaseModel):
    title: str
    description: str


class CandidateResponse(BaseModel):
    id: int
    name: str
    title: Optional[str]
    company: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    linkedin_url: Optional[str]
    source: str

    class Config:
        from_attributes = True


class JobResponse(BaseModel):
    id: int
    title: str
    description: str
    created_at: datetime
    candidates: list[CandidateResponse]

class CallTriggerRequest(BaseModel):
    candidate_ids: list[int]


class CallRecordResponse(BaseModel):
    id: int
    candidate_id: int
    candidate_name: str
    candidate_title: Optional[str] = None
    candidate_company: Optional[str] = None
    hunar_call_id: Optional[str]
    status: str
    lifecycle_status: str
    recording_url: Optional[str]
    result: dict
    duration_minutes: Optional[float]

    class Config:
        from_attributes = True