import json
from datetime import datetime

from fastapi import APIRouter, Header, HTTPException, Request
from sqlalchemy import select

from app.db import SessionLocal
from app.models import Payment, Transaction
from app.services.payment import verify_webhook
from app.services.transactions import mark_paid
from app.services.notifications import create_notification

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])


@router.post("/razorpay")
async def razorpay(request: Request, x_razorpay_signature: str = Header(default="")):
    body = await request.body()
    if not verify_webhook(body, x_razorpay_signature):
        raise HTTPException(400, "Invalid webhook signature")

    payload = json.loads(body.decode("utf-8"))
    event = payload.get("event", "")
    payment_entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
    order_entity = payload.get("payload", {}).get("order", {}).get("entity", {})
    order_id = payment_entity.get("order_id") or order_entity.get("id")
    payment_id = payment_entity.get("id")

    with SessionLocal() as db:
        payment = None
        if order_id:
            payment = db.scalar(select(Payment).where(Payment.provider_order_id == order_id))
        if not payment and payment_id:
            payment = db.scalar(select(Payment).where(Payment.provider_payment_id == payment_id))
        if not payment:
            return {"received": True, "ignored": True}

        tx = db.get(Transaction, payment.transaction_id)

        if event in {"payment.captured", "order.paid"}:
            if payment.status != "captured":
                payment.provider_payment_id = payment_id or payment.provider_payment_id
                payment.signature_verified = True
                payment.status = "captured"
                payment.paid_at = datetime.utcnow()
                if tx:
                    mark_paid(db, tx)
        elif event == "payment.failed":
            if payment.status != "captured":
                payment.status = "failed"
                if tx:
                    create_notification(
                        db,
                        tx.buyer_id,
                        "payment_failed",
                        "Payment failed",
                        f"Payment for transaction #{tx.id} was not captured.",
                        f"/payment/{tx.id}",
                    )
        db.commit()

    return {"received": True}
