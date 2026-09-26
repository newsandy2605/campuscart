import base64
import hashlib
import hmac
import httpx
from decimal import Decimal

from fastapi import HTTPException

from app.config import settings


class PaymentProvider:
    name = "base"

    async def create_order(self, amount: Decimal, receipt: str, notes: dict):
        raise NotImplementedError

    async def fetch_payment(self, payment_id: str):
        return None

    async def refund(self, payment_id: str, amount: Decimal | None = None):
        raise NotImplementedError

    def verify_signature(self, order_id: str, payment_id: str, signature: str):
        raise NotImplementedError


class LocalPaymentProvider(PaymentProvider):
    name = "local"

    async def create_order(self, amount: Decimal, receipt: str, notes: dict):
        return {
            "id": f"local_order_{receipt}",
            "amount": int(amount * 100),
            "currency": "INR",
            "receipt": receipt,
            "status": "created",
            "notes": notes,
            "test_mode": True,
        }

    async def refund(self, payment_id: str, amount: Decimal | None = None):
        return {
            "id": f"local_refund_{payment_id}",
            "status": "processed",
            "amount": int((amount or Decimal("0")) * 100),
            "test_mode": True,
        }

    def verify_signature(self, order_id: str, payment_id: str, signature: str):
        return signature == "local"


class RazorpayProvider(PaymentProvider):
    name = "razorpay"

    def _headers(self):
        raw = f"{settings.razorpay_key_id}:{settings.razorpay_key_secret}".encode()
        token = base64.b64encode(raw).decode()
        return {
            "Authorization": f"Basic {token}",
            "Content-Type": "application/json",
        }

    async def create_order(self, amount: Decimal, receipt: str, notes: dict):
        if not settings.razorpay_key_id or not settings.razorpay_key_secret:
            raise HTTPException(503, "Razorpay credentials are not configured")
        payload = {
            "amount": int(amount * 100),
            "currency": "INR",
            "receipt": receipt,
            "notes": notes,
        }
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                "https://api.razorpay.com/v1/orders",
                json=payload,
                headers=self._headers(),
            )
            if response.status_code >= 400:
                raise HTTPException(
                    response.status_code,
                    f"Payment provider error: {response.text}",
                )
            return response.json()

    async def fetch_payment(self, payment_id: str):
        if not settings.razorpay_key_id or not settings.razorpay_key_secret:
            raise HTTPException(503, "Razorpay credentials are not configured")
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(
                f"https://api.razorpay.com/v1/payments/{payment_id}",
                headers=self._headers(),
            )
            if response.status_code >= 400:
                raise HTTPException(
                    response.status_code,
                    f"Payment provider error: {response.text}",
                )
            return response.json()

    async def refund(self, payment_id: str, amount: Decimal | None = None):
        if not settings.razorpay_key_id or not settings.razorpay_key_secret:
            raise HTTPException(503, "Razorpay credentials are not configured")
        payload = {}
        if amount is not None:
            payload["amount"] = int(amount * 100)
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                f"https://api.razorpay.com/v1/payments/{payment_id}/refund",
                json=payload,
                headers=self._headers(),
            )
            if response.status_code >= 400:
                raise HTTPException(
                    response.status_code,
                    f"Refund provider error: {response.text}",
                )
            return response.json()

    def verify_signature(self, order_id: str, payment_id: str, signature: str):
        message = f"{order_id}|{payment_id}".encode()
        expected = hmac.new(
            settings.razorpay_key_secret.encode(),
            message,
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, signature)


def get_provider() -> PaymentProvider:
    return (
        RazorpayProvider()
        if settings.payment_provider == "razorpay"
        else LocalPaymentProvider()
    )


def verify_webhook(body: bytes, signature: str) -> bool:
    if settings.payment_provider != "razorpay":
        return True
    secret = settings.razorpay_webhook_secret
    if not secret:
        return False
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)
