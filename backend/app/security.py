import hashlib
import hmac
import secrets
import time
from typing import Any

import jwt
from fastapi import HTTPException, status

from app.config import settings
from app.services.cache import safe_setex, safe_get

ALGORITHM = "HS256"


def normalize_email(email: str) -> str:
    return email.strip().lower()


def normalize_phone(phone: str) -> str:
    raw = "".join(ch for ch in phone.strip() if ch.isdigit() or ch == "+")
    digits = "".join(ch for ch in raw if ch.isdigit())
    if digits.startswith("0") and len(digits) == 11:
        digits = digits[1:]
    if digits.startswith("91") and len(digits) == 12:
        digits = digits[2:]
    if len(digits) == 10:
        return "+91" + digits
    raise ValueError("Enter a valid Indian mobile number")


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), salt.encode(), 120_000
    ).hex()
    return f"{salt}${digest}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt, digest = stored.split("$", 1)
    except ValueError:
        return False
    expected = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), salt.encode(), 120_000
    ).hex()
    return hmac.compare_digest(expected, digest)


def hash_value(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def create_token(user_id: int, role: str, purpose: str = "access") -> str:
    now = int(time.time())
    token_id = secrets.token_urlsafe(16)
    payload = {
        "sub": str(user_id),
        "role": role,
        "purpose": purpose,
        "jti": token_id,
        "iat": now,
        "exp": now + settings.jwt_expire_minutes * 60,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)


def decode_token(token: str, expected_purpose: str = "access") -> dict[str, Any]:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from exc

    purpose = payload.get("purpose", "access")
    if purpose != expected_purpose:
        raise HTTPException(status_code=401, detail="Invalid token purpose")
    return payload


def create_reset_token(user_id: int) -> str:
    now = int(time.time())
    payload = {
        "sub": str(user_id),
        "purpose": "password_reset",
        "jti": secrets.token_urlsafe(16),
        "iat": now,
        "exp": now + settings.password_reset_ttl_seconds,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)


def decode_reset_token(token: str) -> dict[str, Any]:
    return decode_token(token, expected_purpose="password_reset")


def revoke_token(token: str) -> None:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
        jti = payload.get("jti")
        exp = int(payload.get("exp", 0))
        ttl = max(1, exp - int(time.time()))
        if jti:
            safe_setex(f"cc:revoked:{jti}", ttl, "1")
    except Exception:
        return


def is_token_revoked(payload: dict[str, Any]) -> bool:
    jti = payload.get("jti")
    if not jti:
        return False
    return safe_get(f"cc:revoked:{jti}") is not None


def generate_otp() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def generate_handoff_code(transaction_id: int) -> str:
    secret = settings.handoff_secret.encode()
    message = f"campuscart-handoff:{transaction_id}".encode()
    digest = hmac.new(secret, message, hashlib.sha256).hexdigest()
    number = int(digest[:8], 16) % 10_000
    return f"{number:04d}"
