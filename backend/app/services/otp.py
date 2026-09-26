import smtplib
from datetime import datetime, timedelta
from email.message import EmailMessage

import httpx

from app.config import settings
from app.models import OTPChallenge
from app.security import generate_otp, hash_value, normalize_email, normalize_phone


def now() -> datetime:
    return datetime.utcnow()


def normalize_destination(channel: str, destination: str) -> str:
    if channel == "email":
        return normalize_email(destination)
    return normalize_phone(destination)


def create_challenge(db, user_id, channel, destination, purpose):
    destination = normalize_destination(channel, destination)

    previous = db.query(OTPChallenge).filter(
        OTPChallenge.destination == destination,
        OTPChallenge.channel == channel,
        OTPChallenge.purpose == purpose,
        OTPChallenge.consumed_at.is_(None),
    ).all()
    for item in previous:
        item.consumed_at = now()

    code = generate_otp()
    challenge = OTPChallenge(
        user_id=user_id,
        channel=channel,
        destination=destination,
        purpose=purpose,
        code_hash=hash_value(code),
        expires_at=now() + timedelta(seconds=settings.otp_ttl_seconds),
    )
    db.add(challenge)
    db.flush()
    return challenge, code


def _email_body(code: str, purpose: str) -> str:
    purpose_text = purpose.replace("_", " ")
    return (
        f"Your CampusCart {purpose_text} code is {code}.\n\n"
        f"This code expires in {settings.otp_ttl_seconds // 60} minutes."
    )


def _send_email(destination: str, body: str) -> str:
    message = EmailMessage()
    message["Subject"] = "CampusCart verification code"
    message["From"] = settings.smtp_from
    message["To"] = destination
    message.set_content(body)

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as server:
        if settings.smtp_starttls:
            server.starttls()
        if settings.smtp_user:
            server.login(settings.smtp_user, settings.smtp_password)
        server.send_message(message)

    return "smtp"


def _send_twilio_verify(destination: str) -> str:
    if not all([settings.twilio_account_sid, settings.twilio_auth_token, settings.twilio_verify_service_sid]):
        raise RuntimeError("Twilio Verify credentials are not fully configured")

    url = (
        "https://verify.twilio.com/v2/Services/"
        f"{settings.twilio_verify_service_sid}/Verifications"
    )
    response = httpx.post(
        url,
        data={"To": destination, "Channel": "sms"},
        auth=(settings.twilio_account_sid, settings.twilio_auth_token),
        timeout=20,
    )
    if response.status_code >= 400:
        raise RuntimeError(f"Twilio Verify failed: {response.text}")
    return "twilio_verify"

def _send_webhook_sms(destination: str, body: str) -> str:
    response = httpx.post(
        settings.sms_webhook_url,
        json={"to": destination, "message": body},
        timeout=15,
    )
    response.raise_for_status()
    return "sms_webhook"


def deliver_otp(channel: str, destination: str, code: str, purpose: str):
    body = _email_body(code, purpose)
    provider = None

    if channel == "email":
        if settings.smtp_host:
            provider = _send_email(destination, body)
        elif settings.app_env == "development" and settings.dev_otp_echo:
            print(f"[CampusCart DEV OTP] email {destination} {purpose}: {code}")
            provider = "development"
        else:
            raise RuntimeError(
                "Email OTP delivery is not configured. Set SMTP_HOST or enable DEV_OTP_ECHO in development."
            )

    elif channel == "phone":
        if settings.sms_provider.lower() == "twilio":
            provider = _send_twilio_verify(destination)
        elif settings.sms_webhook_url:
            provider = _send_webhook_sms(destination, body)
        elif settings.app_env == "development" and settings.dev_otp_echo:
            print(f"[CampusCart DEV OTP] phone {destination} {purpose}: {code}")
            provider = "development"
        else:
            raise RuntimeError(
                "Phone OTP delivery is not configured. Set Twilio/SMS webhook settings or enable DEV_OTP_ECHO in development."
            )
    else:
        raise RuntimeError("Unsupported OTP channel")

    return {
        "provider": provider,
        "debug_code": code
        if provider != "twilio_verify" and settings.app_env == "development" and settings.dev_otp_echo
        else None,
    }
