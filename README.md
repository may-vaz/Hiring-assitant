# AI Hiring Assistant

An AI-powered hiring platform that automates candidate sourcing and voice-based screening using Hunar.ai Voice AI agents.

**Live Demo:** [https://hiring-assitant.vercel.app](https://hiring-assitant.vercel.app)
**Backend API:** [https://hiring-assistant-backend-0dh1.onrender.com](https://hiring-assistant-backend-0dh1.onrender.com)

---

## What It Does

Recruiters spend hours searching for candidates, making initial screening calls, and tracking responses. This app automates the entire workflow:

1. **Post a job** → Automatically finds relevant candidates via Apollo.io
2. **Trigger AI voice calls** → Hunar.ai calls candidates with a personalized interview
3. **View results** → See call transcripts, summaries, and candidate responses in real-time

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 16 (App Router), TypeScript, Tailwind CSS, shadcn/ui |
| Backend | Python, FastAPI, SQLModel |
| Database | PostgreSQL |
| Candidate Search | Apollo.io People Search API |
| Voice AI | Hunar.ai Voice Agents API |
| Frontend Hosting | Vercel |
| Backend + DB Hosting | Render |

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER BROWSER (Vercel)                       │
│                  Next.js 16 Frontend                           │
│                                                                 │
│  User creates job → Gets candidates → Triggers voice calls     │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTPS + Session Cookie
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   BACKEND (Render)                             │
│                   FastAPI + PostgreSQL                         │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐ │
│  │  /api/jobs   │  │ /api/calls   │  │ /webhooks/hunar      │ │
│  │  (CRUD)      │  │ (Trigger)    │  │ (Callback)           │ │
│  └──────────────┘  └──────────────┘  └──────────────────────┘ │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Services: Apollo Search │ Hunar Client │ Webhook Verify │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Database: PostgreSQL (Job → Candidate → CallRecord)    │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    EXTERNAL APIS                               │
│         Apollo.io (Candidate Search) + Hunar.ai (Voice AI)     │
└─────────────────────────────────────────────────────────────────┘
```

### Key Design Decisions

**1. Session-Based (No Login)**
- Each visitor gets a UUID session cookie with `HttpOnly` and `Secure` flags
- All data tagged with `session_id` ensuring complete isolation between users
- Eliminates friction for the recruiter who can simply open the link and start using the app

**2. Async Webhook Flow**
- Calls are placed asynchronously via Hunar API to prevent blocking the user
- Hunar calls back via webhook when complete (2-5 minutes later)
- Frontend polls the status endpoint to display real-time updates

**3. Mock Fallback**
- If Apollo API fails (rate limit, network issues), the system returns mock candidates
- Ensures the demo never breaks and the recruiter always sees the full workflow

**4. Cross-Domain Architecture**
- Frontend hosted on Vercel (`hiring-assitant.vercel.app`)
- Backend hosted on Render (`hiring-assistant-backend-0dh1.onrender.com`)
- Allows using best-of-breed hosting for each technology stack

---

## Complete Data Flow

**Job Creation:** User submits job title and description → Backend validates input length (title ≤200 chars, description ≤5000 chars) → Checks rate limit (max 5 jobs per session) → Saves job to PostgreSQL tagged with `session_id` → Searches Apollo.io for 5 matching candidates (or falls back to mock if API fails) → Saves candidates with `job_id` foreign key → Returns job + candidates to frontend.

**Call Triggering:** User selects candidates and triggers calls → Backend validates candidates belong to the job and session → Checks rate limit (max 5 calls per job) → For each candidate, calls Hunar API to create a voice call passing candidate name, job title, company, and callback webhook URL → Saves `CallRecord` with status "NOT_STARTED" → Hunar asynchronously dials the candidate (in demo mode, uses a configured test number, never real candidate numbers).

**Webhook Processing:** Hunar POSTs to `/api/webhooks/hunar` with call result → Backend verifies HMAC-SHA256 signature and timestamp to prevent fake webhooks → Updates `CallRecord` status, result, recording URL, and duration → Frontend polls `GET /api/jobs/{id}/calls` every few seconds to show real-time updates.

---

## Security Implementation

| Threat | Implementation | Rationale |
|--------|---------------|-----------|
| **Session Hijacking** | UUID v4 with `HttpOnly`, `Secure`, `SameSite=None` flags | UUIDs are cryptographically random; HttpOnly prevents JavaScript access; Secure ensures HTTPS only; SameSite=None enables cross-domain cookie sharing between Vercel and Render |
| **API Abuse (Cost)** | Max 5 jobs per session, Max 5 calls per job with HTTP 429 responses | Prevents unlimited API usage that would burn Apollo/Hunar credits; public deployment requires these guardrails |
| **Input Attacks** | Title ≤200 characters, Description ≤5000 characters with HTTP 400 responses | Prevents buffer overflows and DoS attacks through massive payloads |
| **Fake Webhooks** | HMAC-SHA256 signature verification with 300-second timestamp tolerance | Validates webhooks actually came from Hunar; timestamp prevents replay attacks |
| **Data Leakage** | `raw_json` stored in database but excluded from all API responses | Full API data available for debugging but never exposed to frontend |
| **CORS** | Whitelist only `localhost:3000` and `hiring-assitant.vercel.app` with credentials allowed | Restricts API access to only trusted frontend origins |
| **CSRF** | `SameSite=None` required for cross-domain cookies; mitigated by CORS whitelist + session isolation | Production would add CSRF tokens; current trade-off acceptable for demo with no sensitive operations |

---

## External API Integrations

### Apollo.io (Candidate Search)

**Implementation:** `services/candidate_search.py`

```
API Endpoint: https://api.apollo.io/api/v1/mixed_people/api_search
Authentication: X-Api-Key header
Request: { "person_titles": [extracted_role], "per_page": 5 }
Response: People list with name, title, company, raw_json
```

**Access Investigation:** Apollo's Free plan initially returned `API_INACCESSIBLE` for the search endpoint even with a master API key. Rather than assume this was a hard paywall, I tested directly with `curl` and found Apollo restricts free API access entirely for accounts signed up with a generic email provider (Gmail, Outlook, etc.) — a restriction not obvious from the dashboard UI. Re-registering with a college (`.edu`) email resolved it, confirmed by a live search returning real candidate data. This is documented here because the debugging process — verifying the actual API error rather than guessing — is as relevant as the final integration.

**Smart Title Extraction:** The system scans the job description against a keyword list (Software Engineer, Data Scientist, Product Manager, etc.) and extracts the most relevant role for the Apollo search. This ensures Apollo returns candidates matching the actual job requirements.

**Rate Limiting Safeguards:**
- Results capped at 5 candidates per search (well within Apollo's free tier limits)
- API call wrapped in try-catch with automatic mock fallback
- Prevents demo breakage during rate limits or network failures

**Mock Fallback:** If Apollo call fails for any reason, the system generates mock candidates using Faker library with realistic names, companies, and job titles. This ensures the full hiring workflow remains visible to the recruiter.In production, I would replace this with Redis caching + circuit breaker pattern—storing successful Apollo responses and serving cached data during failures, with exponential backoff retries and monitoring alerts.

### Hunar.ai (Voice AI Agent)

**Implementation:** `services/hunar_client.py`

```
API Endpoint: https://api.voice.hunar.ai/external/v1/calls/
Authentication: X-API-Key header
Request: {
    agent_id, callee_name, mobile_number,
    custom_data: { job_role, company, candidate_name, location },
    callback_config: { call_summary_callback_url },
    retry_config: { max_retry_count: 2, retry_interval_hours: 3 },
    guardrails: { allowed_days: ["MON-SAT"], earliest_call_time: "09:00", last_call_time: "20:00" },
    timezone: "Asia/Kolkata"
}
```

**Call Configuration:**

| Setting | Value | Purpose |
|---------|-------|---------|
| **Retry Config** | 2 retry attempts, 3-hour intervals | Ensures candidates are reached even if they miss the first call |
| **Calling Hours** | 9:00 AM - 8:00 PM IST, Monday-Saturday | Respects work-life balance; prevents late-night disturbance |
| **Demo Mode** | `DEMO_MODE=true` forces calls to configured test number | Never dials real candidate numbers scraped from a search provider without their consent — real screening calls only get placed once a recruiter has actually engaged a candidate through proper channels; this app only *demonstrates* that call, it doesn't perform live outreach |
| **Webhook URL** | `WEBHOOK_BASE_URL/api/webhooks/hunar` | Hunar POSTs call results here for async processing |
| **Agent ID** | Configured via `HUNAR_AGENT_ID` | Specifies which Hunar Voice AI agent to use for the interview |

**Agent Prompt Tuning:** The stock agent prompt included a "confirm answers by repeating key facts" instruction, which caused the agent to verbally recap the candidate's answers mid-call — unlike a natural screening call. Updated `agent_prompt`, `conclusion`, and `result_prompt` via `PUT /agents/{id}/` to remove the recap behavior, add outcome-appropriate closings, and tighten the result extraction rules (no hallucinated values, stripped filler words, locked enum outputs) so the conversation feels natural while the structured result stays clean and reliable for the dashboard.

**Webhook Signature Verification:** All webhooks are verified using HMAC-SHA256 with Hunar's API key and timestamp, following Hunar's documented `X-Hunar-Signature` / `X-Hunar-Timestamp` scheme. The system validates both the signature header and timestamp, rejecting any request older than 300 seconds. This prevents fake webhook injection and replay attacks.

---

## Key API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/jobs` | Create job + search candidates via Apollo |
| GET | `/api/jobs` | List all jobs for current session |
| GET | `/api/jobs/{id}` | Get specific job with candidates |
| DELETE | `/api/jobs/{id}` | Delete job with cascade to candidates and calls |
| POST | `/api/jobs/{id}/calls` | Trigger Hunar calls for selected candidates |
| GET | `/api/jobs/{id}/calls` | Get call statuses with auto-refresh from Hunar |
| POST | `/api/webhooks/hunar` | Hunar callback endpoint with signature verification |

---

## Running Locally

```bash
# Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
# copy .env.example to .env and fill in your own API keys
uvicorn main:app --reload --port 8000

# Frontend
cd frontend
npm install && npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

---
# Question: Attendance Tracking Without Smartphones

**Problem:** Track attendance of 1000 employees across 100 locations without smartphones.
---
**Assume we don't have smartphones or personal devices, but we do have desktops/laptops, internet, and a central server.**
## Solution: Centralized Kiosk System

```
┌─────────────────────────────────────────────────────────────────────┐
│                    CENTRAL SERVER (Cloud)                          │
│                attendance.company.com                              │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │  PostgreSQL Database + Load Balancer + LLM Layer             │ │
│  │  - Stores all check-ins with timestamp, employee, location   │ │
│  │  - Handles 1000+ check-ins daily                             │ │
│  │  - LLM answers queries: "Who missed check-in at Location 42?"│ │
│  └───────────────────────────────────────────────────────────────┘ │
└──────────────────────┬──────────────────────────┬──────────────────┘
                       │                          │
           ┌───────────▼──────────┐   ┌───────────▼──────────┐
           │    Location 1        │   │   Location 100       │
           │  ┌────────────────┐  │   │  ┌────────────────┐  │
           │  │ Shared Terminal│  │   │  │ Shared Terminal│  │
           │  │  (Browser)     │  │   │  │  (Browser)     │  │
           │  │                │  │   │  │                │  │
           │  │ Employee enters│  │   │  │ Employee enters│  │
           │  │ ID + PIN       │  │   │  │ ID + PIN       │  │
           │  └────────────────┘  │   │  └────────────────┘  │
           └──────────────────────┘   └──────────────────────┘
```

## How It Works

**The Setup:** I build a single web application hosted on a central server (attendance.company.com). At each of the 100 locations, I place one or more shared computers or kiosk terminals. Every terminal opens a browser and navigates to the same URL. The system identifies each location either through a unique "Location ID" entered at startup or through IP geofencing (detecting which network the terminal is on). This means no per-location software installation—just a browser and internet connection.

**The Check-in Process:** When an employee arrives at work, they walk to the terminal, enter their unique Employee ID and PIN (or swipe an ID card/fingerprint), and click "Check In." The browser sends this data over HTTPS to the central server, which logs the timestamp, employee ID, and location in the Database. HR admins can log into the same website from anywhere to view a real-time dashboard showing attendance across all 100 sites, generate reports, or query anomalies. If a location loses internet, the terminal caches check-ins locally using the browser's storage and syncs automatically when connectivity returns—ensuring no data is ever lost.

**Scalability** This architecture scales horizontally with zero friction. Adding a 101st location simply means setting up another terminal and registering its Location ID—no new code, no additional servers. A location with 50 employees needs one terminal; a location with 500 employees can deploy multiple terminals to avoid queues, all pointing to the same central URL. The load balancer distributes traffic across application servers, and the database auto-scales with read replicas for reporting and partitioning for performance. The LLM layer sits on top, handling exceptions (late arrivals, shift swaps), generating daily summaries, and answering natural-language queries like "Who didn't check in at Location 42 today?" This design ensures centralized data integrity, offline resilience, geographic awareness, and AI-augmented automation—making it production-ready for enterprise-scale attendance tracking.

Author
Maeve Vas - Technical Assessment for Hunar.ai
