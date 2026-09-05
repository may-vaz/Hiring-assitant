import os
import httpx
from dotenv import load_dotenv

load_dotenv()

HUNAR_API_KEY = os.getenv("HUNAR_API_KEY")
HUNAR_AGENT_ID = os.getenv("HUNAR_AGENT_ID")
DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"
DEMO_PHONE_NUMBER = os.getenv("DEMO_PHONE_NUMBER")
WEBHOOK_BASE_URL = os.getenv("WEBHOOK_BASE_URL")

BASE_URL = "https://api.voice.hunar.ai/external/v1"

HEADERS = {
    "X-API-Key": HUNAR_API_KEY,
    "Content-Type": "application/json",
}


def create_call(candidate_name: str, job_title: str, company: str = "our company") -> dict:
    """
    Places a Hunar voice call. In DEMO_MODE, the callee_name shown to the
    agent is the real candidate's name, but the mobile_number is forced to
    DEMO_PHONE_NUMBER — see README for why real candidate numbers are never dialed.
    """
    mobile_number = DEMO_PHONE_NUMBER if DEMO_MODE else None

    if not mobile_number:
        raise ValueError("No phone number available to call.")

    payload = {
        "agent_id": HUNAR_AGENT_ID,
        "callee_name": candidate_name,
        "mobile_number": mobile_number,
        "custom_data": {
            "job_role": job_title,
            "company": company,
        },
        "callback_config": {
            "call_summary_callback_url": f"{WEBHOOK_BASE_URL}/api/webhooks/hunar"
        },
    }

    response = httpx.post(f"{BASE_URL}/calls/", headers=HEADERS, json=payload, timeout=30)
    response.raise_for_status()
    return response.json()


def get_call(hunar_call_id: str) -> dict:
    response = httpx.get(f"{BASE_URL}/calls/{hunar_call_id}/", headers=HEADERS, timeout=30)
    response.raise_for_status()
    return response.json()


def list_agents() -> dict:
    response = httpx.get(f"{BASE_URL}/agents/", headers=HEADERS, timeout=30)
    response.raise_for_status()
    return response.json()