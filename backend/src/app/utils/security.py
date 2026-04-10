from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Tuple

from app.utils.time import utc_now


@dataclass
class SessionToken:
    raw: str
    digest: str
    expires_at: datetime


def hash_password(password: str, iterations: int = 240_000) -> str:
    salt = os.urandom(16)
    derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return (
        f"pbkdf2_sha256${iterations}$"
        f"{base64.b64encode(salt).decode('ascii')}$"
        f"{base64.b64encode(derived).decode('ascii')}"
    )


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        scheme, raw_iterations, raw_salt, raw_hash = stored_hash.split("$", 3)
        if scheme != "pbkdf2_sha256":
            return False
        iterations = int(raw_iterations)
        salt = base64.b64decode(raw_salt.encode("ascii"))
        expected = base64.b64decode(raw_hash.encode("ascii"))
    except (ValueError, TypeError):
        return False
    calculated = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return hmac.compare_digest(calculated, expected)


def generate_session_token(ttl_hours: int) -> SessionToken:
    raw = secrets.token_urlsafe(32)
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return SessionToken(raw=raw, digest=digest, expires_at=utc_now() + timedelta(hours=ttl_hours))


def digest_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def safe_compare(left: str, right: str) -> bool:
    return hmac.compare_digest(left.encode("utf-8"), right.encode("utf-8"))
