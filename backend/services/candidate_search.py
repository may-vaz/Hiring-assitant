import random
from faker import Faker

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


def _guess_role_from_jd(job_description: str) -> str:
    jd_lower = job_description.lower()
    for title in TITLE_KEYWORDS:
        if title.lower() in jd_lower:
            return title
    # fallback: pick a role that shares a keyword with the JD
    for word in jd_lower.split():
        for title in TITLE_KEYWORDS:
            if word in title.lower():
                return title
    return random.choice(TITLE_KEYWORDS)


def search_people(job_description: str, count: int = 8) -> list[dict]:
    """
    Mock candidate search. Returns a list of candidate dicts shaped
    exactly like what a real vendor (e.g. Apollo) search would return.
    Swap this function's internals later to call a real API —
    the return shape must stay the same.
    """
    matched_role = _guess_role_from_jd(job_description)

    candidates = []
    for _ in range(count):
        name = fake.name()
        candidates.append({
            "name": name,
            "title": matched_role,
            "company": random.choice(COMPANIES),
            "email": None,   # intentionally not sourced — see README
            "phone": None,   # intentionally not sourced — see README
            "linkedin_url": f"https://linkedin.com/in/{name.lower().replace(' ', '-')}",
            "source": "mock",
            "raw_json": {},
        })
    return candidates