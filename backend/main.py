from fastapi import FastAPI, Depends, HTTPException
from sqlmodel import Session, select

from database import init_db, get_session
from models import Job, Candidate
from schemas import JobCreateRequest, JobResponse, CandidateResponse
from services.candidate_search import search_people

app = FastAPI(title="AI Hiring Assistant")


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/")
def health_check():
    return {"status": "ok", "message": "AI Hiring Assistant backend is running"}


@app.post("/api/jobs", response_model=JobResponse)
def create_job(payload: JobCreateRequest, session: Session = Depends(get_session)):
    job = Job(title=payload.title, description=payload.description)
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

    return JobResponse(
        id=job.id,
        title=job.title,
        description=job.description,
        candidates=[CandidateResponse.model_validate(c) for c in candidates],
    )


@app.get("/api/jobs/{job_id}", response_model=JobResponse)
def get_job(job_id: int, session: Session = Depends(get_session)):
    job = session.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    candidates = session.exec(
        select(Candidate).where(Candidate.job_id == job_id)
    ).all()

    return JobResponse(
        id=job.id,
        title=job.title,
        description=job.description,
        candidates=[CandidateResponse.model_validate(c) for c in candidates],
    )