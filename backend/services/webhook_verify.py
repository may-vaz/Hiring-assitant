import base64
import hashlib
import hmac
import time


def compute_hunar_signature(*, api_key: str, request_body: bytes, timestamp: str) -> str:
    message = f"{timestamp.strip()}.".encode("utf-8") + request_body
    digest = hmac.new(api_key.encode("utf-8"), message, hashlib.sha256).digest()
    return base64.b64encode(digest).decode("ascii")


def verify_hunar_webhook_signature(
    *,
    signature_header: str | None,
    timestamp_header: str | None,
    request_body: bytes,
    trusted_api_keys: list[str],
    tolerance_seconds: int = 300,
) -> bool:
    if not (signature_header and signature_header.strip()):
        return False
    if not (timestamp_header and timestamp_header.strip()):
        return False

    try:
        ts = int(timestamp_header.strip())
    except ValueError:
        return False

    if abs(time.time() - ts) > tolerance_seconds:
        return False

    timestamp = timestamp_header.strip()
    signatures = [s.strip() for s in signature_header.split(",") if s.strip()]

    for api_key in trusted_api_keys:
        computed = compute_hunar_signature(api_key=api_key, request_body=request_body, timestamp=timestamp)
        for signature in signatures:
            if hmac.compare_digest(signature, computed):
                return True

    return False
