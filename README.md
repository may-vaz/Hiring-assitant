# AI Hiring Assistant

An AI-powered hiring platform that automates candidate sourcing and voice-based screening using Hunar.ai Voice AI agents.

**Live Demo:** [https://hiring-assitant.vercel.app](https://hiring-assitant.vercel.app)  
**Backend API:** [https://your-api.onrender.com](https://your-api.onrender.com)

---

## 🎯 What It Does

Recruiters often spend hours searching for candidates, making initial screening calls, and tracking responses. This app automates the entire workflow:

1. **Post a job** → Automatically finds relevant candidates via Apollo.io
2. **Trigger AI voice calls** → Hunar.ai calls candidates with a personalized interview
3. **View results** → See call transcripts, summaries, and candidate responses in real-time

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER BROWSER (Vercel)                       │
│                  Next.js 14 Frontend                           │
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
- Each visitor gets a UUID session cookie (`HttpOnly`, `Secure`)
- All data tagged with `session_id` → Complete isolation between users
- **Why?** Zero friction for the recruiter; just open the link and start

**2. Async Webhook Flow**
- Calls are placed asynchronously via Hunar API
- Hunar calls back via webhook when complete (2-5 mins later)
- **Why?** Non-blocking; user can continue working while calls happen

**3. Mock Fallback**
- If Apollo API fails (rate limit, network issues), return mock candidates
- **Why?** Demo never breaks; recruiter always sees the full workflow

**4. Cross-Domain Architecture**
- Frontend: Vercel (`hiring-assitant.vercel.app`)
- Backend: Render (`your-api.onrender.com`)
- **Why?** Best-of-breed hosting for each stack

---

## 🔄 Complete Data Flow (One Shot)

**User creates a job** → Backend validates input (title ≤200 chars, description ≤5000 chars) → Checks rate limit (max 5 jobs per session) → Saves job to PostgreSQL tagged with `session_id` → Searches Apollo.io for 5 matching candidates (or falls back to mock) → Saves candidates with `job_id` foreign key → Returns job + candidates to frontend.

**User selects candidates & triggers calls** → Backend checks rate limit (max 5 calls per job) → For each candidate, calls Hunar API to create a voice call (passes candidate name, job title, callback webhook URL) → Saves `CallRecord` with status "NOT_STARTED" → Hunar asynchronously dials the candidate (in demo mode, uses a configured test number, never real numbers).

**Call completes** → Hunar POSTs to `/api/webhooks/hunar` with call result → Backend verifies HMAC-SHA256 signature + timestamp (prevents fake webhooks) → Updates `CallRecord` status + result + recording URL → Frontend polls `GET /api/jobs/{id}/calls` every few seconds to show real-time updates.

---

## 🔒 Security Implementation

| Threat | Implementation | Why |
|--------|---------------|-----|
| **Session Hijacking** | UUID v4 + `HttpOnly` + `Secure` cookies | Prevents XSS theft; cookie never leaves HTTPS |
| **API Abuse (Cost)** | Max 5 jobs/session + Max 5 calls/job (HTTP 429) | Prevents unlimited API calls burning Apollo/Hunar credits |
| **Input Attacks** | Title ≤200 chars, Description ≤5000 chars | Prevents buffer overflows + DoS via massive payloads |
| **Fake Webhooks** | HMAC-SHA256 + timestamp validation (300s tolerance) | Only genuine Hunar webhooks accepted; replay attacks blocked |
| **Data Leakage** | `raw_json` stored in DB but never returned to frontend | Full API data available for debugging, but never exposed to user |
| **CSRF** | `SameSite=None` (trade-off for cross-domain) + CORS whitelist + session isolation | Cross-domain (Vercel + Render) requires `SameSite=None`; mitigated by whitelisting only my Vercel domain and isolating sessions. Production would add CSRF tokens. |

---

## 🛠️ Tech Stack (Short)

- **Frontend:** Next.js 14 + TypeScript (Vercel)
- **Backend:** FastAPI + SQLModel + PostgreSQL (Render)
- **External APIs:** Apollo.io (candidate search) + Hunar.ai (voice AI)

---

## 📡 Key API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/jobs` | Create job + search candidates |
| GET | `/api/jobs` | List session jobs |
| DELETE | `/api/jobs/{id}` | Delete job + cascade |
| POST | `/api/jobs/{id}/calls` | Trigger Hunar calls |
| GET | `/api/jobs/{id}/calls` | Get call statuses (auto-refreshes pending) |
| POST | `/api/webhooks/hunar` | Hunar callback (HMAC-SHA256 verified) |

---

## 🚀 Running Locally (Short)

```bash
# Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Frontend
cd frontend
npm install && npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

---

## 📝 Bonus Question: Attendance Without Smartphones

**Problem:** Track 1000 employees across 100 locations without smartphones, but with desktops/laptops and internet.

**Solution: Centralized Kiosk System**

```
Central Server (attendance.company.com)
    ├── Location 1 Terminal (Browser)
    ├── Location 2 Terminal (Browser)
    └── Location 100 Terminal (Browser)
```

- Single web app for all locations
- Location identified by login (Location ID) or IP geofencing
- Employees enter ID + PIN at shared terminal → logs timestamp + location
- HR views real-time dashboard across all sites
- Offline: Terminal caches check-ins; syncs when internet returns
- LLM layer handles exceptions, generates summaries, answers queries

**Why it works:** Centralized single source of truth, location-aware, offline-first, horizontally scalable, AI-augmented.

---

## 👤 Author

**Maeve Vas** - Technical Assessment for Hunar.ai
