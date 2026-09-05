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
    candidates: list[CandidateResponse]

class CallTriggerRequest(BaseModel):
    candidate_ids: list[int]


class CallRecordResponse(BaseModel):
    id: int
    candidate_id: int
    hunar_call_id: Optional[str]
    status: str
    lifecycle_status: str
    recording_url: Optional[str]
    result: dict
    duration_minutes: Optional[float]

    class Config:
        from_attributes = True