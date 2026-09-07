import uuid

from fastapi import FastAPI, Depends, HTTPException, Request, Response, Cookie
from sqlmodel import Session, select
from typing import Optional

from database import init_db, get_session
from models import Job, Candidate, CallRecord
from schemas import (
    JobCreateRequest,
    JobResponse,
    CandidateResponse,
    CallTriggerRequest,
    CallRecordResponse,
)
from services.candidate_search import search_people
from services.hunar_client import create_call, get_call

app = FastAPI(title="AI Hiring Assistant")

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://hiring-assitant.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SESSION_COOKIE_NAME = "hiring_session_id"


def get_or_create_session_id(
    response: Response,
    hiring_session_id: Optional[str] = Cookie(default=None),
) -> str:
    """
    Anonymous session scoping — no login required. Each browser gets a random
    ID stored in a cookie on first visit. Every job is tagged with this ID,
    and every read is filtered by it, so different visitors never see each
    other's searches. Cookie lasts 1 year; clearing cookies starts a fresh
    session with an empty dashboard.
    """
    if hiring_session_id:
        return hiring_session_id

    new_session_id = str(uuid.uuid4())
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=new_session_id,
        max_age=60 * 60 * 24 * 365,
        httponly=True,
        samesite="none",
        secure=True,
    )
    return new_session_id


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/")
def health_check():
    return {"status": "ok", "message": "AI Hiring Assistant backend is running"}


def _to_job_response(job: Job, candidates: list[Candidate]) -> JobResponse:
    return JobResponse(
        id=job.id,
        title=job.title,
        description=job.description,
        created_at=job.created_at,
        candidates=[CandidateResponse.model_validate(c) for c in candidates],
    )


def _to_call_response(call: CallRecord, candidate: Candidate) -> CallRecordResponse:
    return CallRecordResponse(
        id=call.id,
        candidate_id=call.candidate_id,
        candidate_name=candidate.name,
        candidate_title=candidate.title,
        candidate_company=candidate.company,
        hunar_call_id=call.hunar_call_id,
        status=call.status,
        lifecycle_status=call.lifecycle_status,
        recording_url=call.recording_url,
        result=call.result,
        duration_minutes=call.duration_minutes,
    )


@app.post("/api/jobs", response_model=JobResponse)
def create_job(
    payload: JobCreateRequest,
    session: Session = Depends(get_session),
    session_id: str = Depends(get_or_create_session_id),
):
    job = Job(
        title=payload.title,
        description=payload.description,
        session_id=session_id,
    )
    session.add(job)
    session.commit()
    session.refresh(job)

    found_candidates = search_people(payload.description)

    candidates = []
    for c in found_candidates:
        candidate = Candidate(
            job_id=job.id,
            name=c["name"],
            title=c["title"],
            company=c["company"],
            email=c["email"],
            phone=c["phone"],
            linkedin_url=c["linkedin_url"],
            source=c["source"],
            raw_json=c["raw_json"],
        )
        session.add(candidate)
        candidates.append(candidate)

    session.commit()
    for c in candidates:
        session.refresh(c)

    return _to_job_response(job, candidates)


@app.get("/api/jobs", response_model=list[JobResponse])
def list_jobs(
    session: Session = Depends(get_session),
    session_id: str = Depends(get_or_create_session_id),
):
    jobs = session.exec(
        select(Job)
        .where(Job.session_id == session_id)
        .order_by(Job.created_at.desc())
    ).all()

    result = []
    for job in jobs:
        candidates = session.exec(
            select(Candidate).where(Candidate.job_id == job.id)
        ).all()
        result.append(_to_job_response(job, candidates))
    return result


@app.get("/api/jobs/{job_id}", response_model=JobResponse)
def get_job(
    job_id: int,
    session: Session = Depends(get_session),
    session_id: str = Depends(get_or_create_session_id),
):
    job = session.get(Job, job_id)
    if not job or job.session_id != session_id:
        raise HTTPException(status_code=404, detail="Job not found")

    candidates = session.exec(
        select(Candidate).where(Candidate.job_id == job_id)
    ).all()

    return _to_job_response(job, candidates)


@app.delete("/api/jobs/{job_id}")
def delete_job(
    job_id: int,
    session: Session = Depends(get_session),
    session_id: str = Depends(get_or_create_session_id),
):
    job = session.get(Job, job_id)
    if not job or job.session_id != session_id:
        raise HTTPException(status_code=404, detail="Job not found")

    candidates = session.exec(
        select(Candidate).where(Candidate.job_id == job_id)
    ).all()
    candidate_ids = [c.id for c in candidates]

    if candidate_ids:
        calls = session.exec(
            select(CallRecord).where(CallRecord.candidate_id.in_(candidate_ids))
        ).all()
        for call in calls:
            session.delete(call)

    for candidate in candidates:
        session.delete(candidate)

    session.delete(job)
    session.commit()

    return {"status": "deleted", "job_id": job_id}


@app.post("/api/jobs/{job_id}/calls", response_model=list[CallRecordResponse])
def trigger_calls(
    job_id: int,
    payload: CallTriggerRequest,
    session: Session = Depends(get_session),
    session_id: str = Depends(get_or_create_session_id),
):
    job = session.get(Job, job_id)
    if not job or job.session_id != session_id:
        raise HTTPException(status_code=404, detail="Job not found")

    valid_candidates = session.exec(
        select(Candidate).where(
            Candidate.job_id == job_id,
            Candidate.id.in_(payload.candidate_ids),
        )
    ).all()
    valid_candidate_ids = {c.id for c in valid_candidates}
    candidates_by_id = {c.id: c for c in valid_candidates}

    existing_calls = session.exec(
        select(CallRecord).where(CallRecord.candidate_id.in_(valid_candidate_ids))
    ).all()
    already_called_ids = {c.candidate_id for c in existing_calls}

    call_records = []
    errors = []

    for candidate_id in valid_candidate_ids:
        if candidate_id in already_called_ids:
            continue

        candidate = candidates_by_id[candidate_id]

        try:
            hunar_response = create_call(
                candidate_name=candidate.name,
                job_title=job.title,
                company=candidate.company or "our company",
            )
        except Exception as e:
            errors.append({"candidate_id": candidate_id, "error": str(e)})
            continue

        call_record = CallRecord(
            candidate_id=candidate.id,
            hunar_call_id=hunar_response.get("id"),
            status=hunar_response.get("status", "NOT_STARTED"),
            lifecycle_status=hunar_response.get("lifecycle_status", "NOT_STARTED"),
        )
        session.add(call_record)
        session.commit()
        session.refresh(call_record)
        call_records.append(_to_call_response(call_record, candidate))

    return call_records


@app.get("/api/jobs/{job_id}/calls", response_model=list[CallRecordResponse])
def list_calls(
    job_id: int,
    session: Session = Depends(get_session),
    session_id: str = Depends(get_or_create_session_id),
):
    job = session.get(Job, job_id)
    if not job or job.session_id != session_id:
        raise HTTPException(status_code=404, detail="Job not found")

    candidates = session.exec(
        select(Candidate).where(Candidate.job_id == job_id)
    ).all()
    candidates_by_id = {c.id: c for c in candidates}
    candidate_ids = list(candidates_by_id.keys())

    calls = session.exec(
        select(CallRecord).where(CallRecord.candidate_id.in_(candidate_ids))
    ).all()

    for call in calls:
        needs_refresh = (
            call.status not in ("COMPLETED", "FAILED", "CANCELLED", "NOT_CONNECTED")
            or not call.result
        )
        if needs_refresh and call.hunar_call_id:
            try:
                latest = get_call(call.hunar_call_id)
                call.status = latest.get("status", call.status)
                call.lifecycle_status = latest.get("lifecycle_status", call.lifecycle_status)
                call.recording_url = latest.get("recording_url", call.recording_url)
                call.result = latest.get("result", call.result)
                call.duration_minutes = latest.get("duration_minutes", call.duration_minutes)
                session.add(call)
            except Exception:
                pass

    session.commit()
    for c in calls:
        session.refresh(c)

    return [_to_call_response(c, candidates_by_id[c.candidate_id]) for c in calls]


@app.post("/api/webhooks/hunar")
async def hunar_webhook(request: Request, session: Session = Depends(get_session)):
    payload = await request.json()

    hunar_call_id = payload.get("id")
    if not hunar_call_id:
        raise HTTPException(status_code=400, detail="Missing call id in webhook payload")

    call_record = session.exec(
        select(CallRecord).where(CallRecord.hunar_call_id == hunar_call_id)
    ).first()

    if not call_record:
        return {"status": "ignored", "reason": "no matching call record"}

    call_record.status = payload.get("status", call_record.status)
    call_record.lifecycle_status = payload.get("lifecycle_status", call_record.lifecycle_status)
    call_record.recording_url = payload.get("recording_url", call_record.recording_url)
    call_record.result = payload.get("result", call_record.result)
    call_record.duration_minutes = payload.get("duration_minutes", call_record.duration_minutes)

    session.add(call_record)
    session.commit()

    return {"status": "ok"}
