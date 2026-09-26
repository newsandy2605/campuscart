import hmac
import hashlib

from app.services.payment import verify_webhook
from app.security import generate_handoff_code, hash_value


def test_handoff_code_is_deterministic():
    assert generate_handoff_code(42) == generate_handoff_code(42)
    assert len(generate_handoff_code(42)) == 4


def test_webhook_signature_is_checked(monkeypatch):
    from app.config import settings
    settings.payment_provider = "razorpay"
    settings.razorpay_webhook_secret = "secret"
    body = b'{"event":"payment.captured"}'
    signature = hmac.new(b"secret", body, hashlib.sha256).hexdigest()
    assert verify_webhook(body, signature) is True
    assert verify_webhook(body, "bad") is False
