from datetime import datetime

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.deps import current_user
from app.models import OTPChallenge, User
from app.schemas import LoginIn, OTPRequestIn, OTPVerifyIn, PasswordResetIn, RegisterIn
from app.security import (
    create_reset_token,
    create_token,
    hash_password,
    normalize_email,
    normalize_phone,
    revoke_token,
    verify_password,
)
from app.services.otp import create_challenge, deliver_otp, normalize_destination
from app.services.rate_limit import check_otp_rate, allow_request

router = APIRouter(prefix="/api/auth", tags=["auth"])

VALID_OTP_PURPOSES = {
    "verification",
    "email_verification",
    "phone_verification",
    "login",
    "password_reset",
}


def user_out(user: User):
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "phone": user.phone,
        "role": user.role,
        "email_verified": user.email_verified,
        "phone_verified": user.phone_verified,
    }


def normalize_purpose(channel: str, purpose: str) -> str:
    purpose = purpose.strip().lower()
    if purpose == "verification":
        return "email_verification" if channel == "email" else "phone_verification"
    if purpose not in VALID_OTP_PURPOSES:
        raise HTTPException(status_code=400, detail="Invalid OTP purpose")
    if purpose == "email_verification" and channel != "email":
        raise HTTPException(status_code=400, detail="Email verification requires email OTP")
    if purpose == "phone_verification" and channel != "phone":
        raise HTTPException(status_code=400, detail="Phone verification requires phone OTP")
    return purpose


def _deliver(db, user_id, channel, destination, purpose):
    try:
        check_otp_rate(destination)
        challenge, code = create_challenge(db, user_id, channel, destination, purpose)
        delivery = deliver_otp(channel, destination, code, purpose)
        return challenge, delivery
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=429, detail=str(exc)) from exc
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/register")
def register(request: Request, data: RegisterIn, db: Session = Depends(get_db)):
    client_ip = request.client.host if request.client else "unknown"
    if not allow_request(f"cc:register:{client_ip}", 12, 3600):
        raise HTTPException(429, "Too many registration attempts. Try again later.")
    email = normalize_email(str(data.email)) if data.email else None
    phone = None
    if data.phone:
        try:
            phone = normalize_phone(data.phone)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    if not email and not phone:
        raise HTTPException(422, "Enter an email address or phone number")
    if data.verification_channel == "email" and not email:
        raise HTTPException(422, "Email is required when email OTP is selected")
    if data.verification_channel == "phone" and not phone:
        raise HTTPException(422, "Phone number is required when phone OTP is selected")

    if email and db.scalar(select(User).where(User.email == email)):
        raise HTTPException(409, "Email already registered")
    if phone and db.scalar(select(User).where(User.phone == phone)):
        raise HTTPException(409, "Phone already registered")

    user = User(
        name=data.name.strip(),
        email=email or f"phone-{phone.replace('+', '')}@campuscart.local",
        phone=phone,
        password_hash=hash_password(data.password),
    )
    db.add(user)
    db.flush()

    destination = email if data.verification_channel == "email" else phone
    challenge, delivery = _deliver(
        db, user.id, data.verification_channel, destination,
        "email_verification" if data.verification_channel == "email" else "phone_verification",
    )
    db.commit()

    return {
        "message": f"Account created. Verify your {data.verification_channel}.",
        "user": user_out(user),
        "token": create_token(user.id, user.role),
        "otp_challenge_id": challenge.id,
        "otp_delivery": delivery,
        "verification_channel": data.verification_channel,
    }


@router.post("/login")
def login(request: Request, data: LoginIn, db: Session = Depends(get_db)):
    client_ip = request.client.host if request.client else "unknown"
    if not allow_request(f"cc:login:{client_ip}", 20, 900):
        raise HTTPException(429, "Too many login attempts. Try again later.")
    identifier = data.identifier.strip()
    if "@" in identifier:
        value = normalize_email(identifier)
        user = db.scalar(select(User).where(User.email == value))
    else:
        try:
            value = normalize_phone(identifier)
        except ValueError:
            value = identifier
        user = db.scalar(select(User).where(User.phone == value))

    if not user or not user.active or not verify_password(data.password, user.password_hash):
        raise HTTPException(401, "Invalid email/phone or password")
    return {"token": create_token(user.id, user.role), "user": user_out(user)}


@router.post("/otp/request")
def request_otp(data: OTPRequestIn, db: Session = Depends(get_db)):
    purpose = normalize_purpose(data.channel, data.purpose)
    try:
        destination = normalize_destination(data.channel, data.destination)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    if data.channel == "email":
        user = db.scalar(select(User).where(User.email == destination))
    else:
        user = db.scalar(select(User).where(User.phone == destination))

    if not user or not user.active:
        raise HTTPException(404, "Account not found")

    if purpose == "email_verification" and user.email_verified:
        return {"message": "Email is already verified", "verified": True}
    if purpose == "phone_verification" and user.phone_verified:
        return {"message": "Phone is already verified", "verified": True}
    if purpose == "phone_verification" and not user.phone:
        raise HTTPException(400, "Add a phone number before requesting phone verification")

    challenge, delivery = _deliver(db, user.id, data.channel, destination, purpose)
    db.commit()

    return {
        "message": "OTP sent",
        "challenge_id": challenge.id,
        "channel": data.channel,
        "purpose": purpose,
        "otp_delivery": delivery,
    }


@router.post("/otp/verify")
def verify_otp(data: OTPVerifyIn, db: Session = Depends(get_db)):
    purpose = normalize_purpose(data.channel, data.purpose)
    try:
        destination = normalize_destination(data.channel, data.destination)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    challenge = db.scalar(
        select(OTPChallenge)
        .where(
            OTPChallenge.channel == data.channel,
            OTPChallenge.destination == destination,
            OTPChallenge.purpose == purpose,
            OTPChallenge.consumed_at.is_(None),
        )
        .order_by(OTPChallenge.created_at.desc())
    )
    if not challenge:
        raise HTTPException(404, "OTP challenge not found")
    if challenge.expires_at < datetime.utcnow():
        raise HTTPException(400, "OTP expired")
    if challenge.attempts >= settings.otp_max_attempts:
        raise HTTPException(429, "Too many OTP attempts")

    import hmac
    from app.security import hash_value

    challenge.attempts += 1
    provider_verified = False
    if data.channel == "phone" and settings.sms_provider.lower() == "twilio" and settings.twilio_verify_service_sid:
        import httpx
        url = (
            "https://verify.twilio.com/v2/Services/"
            f"{settings.twilio_verify_service_sid}/VerificationCheck"
        )
        try:
            response = httpx.post(
                url,
                data={"To": destination, "Code": data.code},
                auth=(settings.twilio_account_sid, settings.twilio_auth_token),
                timeout=20,
            )
            if response.status_code >= 400:
                db.commit()
                raise HTTPException(400, "Phone OTP verification failed")
            provider_verified = response.json().get("status") == "approved"
        except HTTPException:
            raise
        except Exception as exc:
            db.commit()
            raise HTTPException(503, f"Phone OTP provider unavailable: {exc}") from exc
    else:
        provider_verified = hmac.compare_digest(challenge.code_hash, hash_value(data.code))

    if not provider_verified:
        db.commit()
        raise HTTPException(400, "Invalid OTP")

    challenge.consumed_at = datetime.utcnow()
    user = db.get(User, challenge.user_id) if challenge.user_id else None
    if not user or not user.active:
        db.commit()
        raise HTTPException(404, "Account not found")

    if purpose == "email_verification":
        user.email_verified = True
    elif purpose == "phone_verification":
        user.phone_verified = True
    elif purpose == "password_reset":
        db.commit()
        return {
            "verified": True,
            "channel": data.channel,
            "reset_token": create_reset_token(user.id),
        }

    db.commit()
    return {
        "verified": True,
        "channel": data.channel,
        "token": create_token(user.id, user.role),
        "user": user_out(user),
    }


@router.post("/password/reset")
def reset_password(data: PasswordResetIn, db: Session = Depends(get_db)):
    from app.security import decode_reset_token

    payload = decode_reset_token(data.reset_token)
    try:
        user_id = int(payload["sub"])
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(400, "Invalid reset token") from exc

    user = db.get(User, user_id)
    if not user or not user.active:
        raise HTTPException(404, "Account not found")
    if __import__("app.security", fromlist=["is_token_revoked"]).is_token_revoked(payload):
        raise HTTPException(400, "Reset token has already been used")
    user.password_hash = hash_password(data.new_password)
    __import__("app.security", fromlist=["revoke_token"]).revoke_token(data.reset_token)
    db.commit()
    return {"ok": True, "message": "Password updated"}


@router.post("/logout")
def logout(authorization: str = Header(default=""), user: User = Depends(current_user)):
    if not authorization.lower().startswith("bearer "):
        raise HTTPException(401, "Authorization header is required")
    token = authorization.split(" ", 1)[1].strip()
    revoke_token(token)
    return {"ok": True, "message": f"Signed out {user.name}"}


@router.get("/me")
def me(user: User = Depends(current_user)):
    data = user_out(user)
    data["campuses"] = [
        {"slug": m.campus.slug, "name": m.campus.name, "verified": m.verified}
        for m in user.memberships
    ]
    return data
