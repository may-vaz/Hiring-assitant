import os
import httpx
from dotenv import load_dotenv
from faker import Faker
import random

load_dotenv()

APOLLO_API_KEY = os.getenv("APOLLO_API_KEY")
USE_MOCK_CANDIDATES = os.getenv("USE_MOCK_CANDIDATES", "false").lower() == "true"

fake = Faker()

TITLE_KEYWORDS = [
    "Software Engineer", "Backend Engineer", "Frontend Engineer",
    "Full Stack Developer", "Data Scientist", "Product Manager",
    "DevOps Engineer", "ML Engineer", "QA Engineer", "Sales Manager",
    "Marketing Manager", "HR Manager", "UI/UX Designer"
]

COMPANIES = [
    "Acme Corp", "Nimbus Labs", "Vertex Systems", "Brightline Tech",
    "Northstar Solutions", "Quantum Analytics", "Pixel Forge",
    "Cloudpeak Inc", "Ironwood Technologies", "Silverline Digital"
]

MAX_RESULTS = 5  # keep small and conservative — well under free-tier limits


def _guess_role_from_jd(job_description: str) -> str:
    jd_lower = job_description.lower()
    for title in TITLE_KEYWORDS:
        if title.lower() in jd_lower:
            return title
    for word in jd_lower.split():
        for title in TITLE_KEYWORDS:
            if word in title.lower():
                return title
    return random.choice(TITLE_KEYWORDS)


def _mock_search(job_description: str, count: int = MAX_RESULTS) -> list[dict]:
    matched_role = _guess_role_from_jd(job_description)
    candidates = []
    for _ in range(count):
        name = fake.name()
        candidates.append({
            "name": name,
            "title": matched_role,
            "company": random.choice(COMPANIES),
            "email": None,
            "phone": None,
            "linkedin_url": f"https://linkedin.com/in/{name.lower().replace(' ', '-')}",
            "source": "mock",
            "raw_json": {},
        })
    return candidates


def _apollo_search(job_description: str, count: int = MAX_RESULTS) -> list[dict]:
    matched_role = _guess_role_from_jd(job_description)

    payload = {
        "person_titles": [matched_role],
        "per_page": count,
    }

    response = httpx.post(
        "https://api.apollo.io/api/v1/mixed_people/api_search",
        headers={"X-Api-Key": APOLLO_API_KEY, "Content-Type": "application/json"},
        json=payload,
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()

    candidates = []
    for person in data.get("people", [])[:count]:
        first_name = person.get("first_name", "")
        last_name_obf = person.get("last_name_obfuscated", "")
        full_name = f"{first_name} {last_name_obf}".strip() or "Unknown Candidate"

        org = person.get("organization") or {}
        company_name = org.get("name", "Unknown Company")

        candidates.append({
            "name": full_name,
            "title": person.get("title", matched_role),
            "company": company_name,
            "email": None,  # intentionally not enriched — see README
            "phone": None,  # intentionally not enriched — see README
            "linkedin_url": None,  # not returned by this endpoint on Free plan
            "source": "apollo",
            "raw_json": person,
        })
    return candidates


def search_people(job_description: str, count: int = MAX_RESULTS) -> list[dict]:
    """
    Searches for candidates matching the job description.
    Uses real Apollo People Search by default; falls back to a mock
    generator if USE_MOCK_CANDIDATES=true or if the Apollo call fails
    for any reason (rate limit, network issue, etc.) so the app never
    breaks the demo flow.
    """
    if USE_MOCK_CANDIDATES:
        return _mock_search(job_description, count)

    try:
        return _apollo_search(job_description, count)
    except Exception as e:
        print(f"[apollo search failed, falling back to mock] {e}")
        return _mock_search(job_description, count)