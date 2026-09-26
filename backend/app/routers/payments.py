import json
from datetime import datetime

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import current_user
from app.models import Listing, Payment, SwapOffer, Transaction, User
from app.schemas import PaymentCreateIn, PaymentVerifyIn
from app.services.notifications import create_notification
from app.services.payment import get_provider
from app.services.transactions import mark_paid
from app.services.audit import record as audit_record

router = APIRouter(prefix="/api/payments", tags=["payments"])


@router.post("/create-order")
async def create_order(data: PaymentCreateIn, user: User = Depends(current_user), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")):
    if idempotency_key and len(idempotency_key) > 100:
        raise HTTPException(400, "Invalid Idempotency-Key")
    tx = db.get(Transaction, data.transaction_id)
    if not tx or user.id != tx.buyer_id:
        raise HTTPException(404, "Transaction not found")
    if tx.status != "awaiting_payment":
        raise HTTPException(409, "Transaction is not awaiting payment")

    provider = get_provider()
    payment = db.scalar(select(Payment).where(Payment.transaction_id == tx.id))
    if payment and payment.status == "captured":
        raise HTTPException(409, "Payment is already complete")
    if payment and payment.status == "created" and payment.provider_order_id and payment.metadata_json:
        try:
            existing_order = json.loads(payment.metadata_json)
            return {"payment_id": payment.id, "provider": provider.name, "order": existing_order, "key_id": __import__("app.config", fromlist=["settings"]).settings.razorpay_key_id if provider.name == "razorpay" else None, "idempotent_replay": True}
        except json.JSONDecodeError:
            pass

    order = await provider.create_order(
        tx.agreed_price,
        f"campuscart_tx_{tx.id}",
        {"transaction_id": tx.id, "listing_id": tx.listing_id},
    )

    if not payment:
        payment = Payment(
            transaction_id=tx.id,
            provider=provider.name,
            amount=tx.agreed_price,
            currency="INR",
            method=data.method,
        )
        db.add(payment)

    payment.provider = provider.name
    payment.provider_order_id = order.get("id")
    payment.status = "created"
    payment.metadata_json = json.dumps(order, default=str)
    db.commit()
    db.refresh(payment)

    return {
        "payment_id": payment.id,
        "provider": provider.name,
        "order": order,
        "key_id": __import__("app.config", fromlist=["settings"]).settings.razorpay_key_id
        if provider.name == "razorpay"
        else None,
    }


@router.post("/verify")
async def verify(data: PaymentVerifyIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    payment = db.scalar(select(Payment).where(Payment.provider_order_id == data.provider_order_id))
    if not payment:
        raise HTTPException(404, "Payment not found")

    tx = db.get(Transaction, payment.transaction_id)
    if not tx or tx.buyer_id != user.id:
        raise HTTPException(403, "Not allowed")

    if payment.status == "captured" and payment.signature_verified:
        return {"ok": True, "payment_id": payment.id, "transaction_id": tx.id, "status": tx.status}

    provider = get_provider()
    if not provider.verify_signature(
        data.provider_order_id,
        data.provider_payment_id,
        data.signature,
    ):
        raise HTTPException(400, "Payment signature verification failed")

    if provider.name == "razorpay":
        provider_payment = await provider.fetch_payment(data.provider_payment_id)
        if provider_payment.get("order_id") != data.provider_order_id:
            raise HTTPException(400, "Payment does not belong to this order")
        if int(provider_payment.get("amount", 0)) != int(tx.agreed_price * 100):
            raise HTTPException(400, "Payment amount does not match transaction amount")
        if provider_payment.get("status") != "captured":
            raise HTTPException(409, "Payment is not captured yet")

    payment.provider_payment_id = data.provider_payment_id
    payment.signature_verified = True
    payment.status = "captured"
    payment.paid_at = datetime.utcnow()
    mark_paid(db, tx)
    audit_record(db, user.id, "payment.captured", "payment", payment.id, f"transaction={tx.id}")
    db.commit()
    return {"ok": True, "payment_id": payment.id, "transaction_id": tx.id, "status": tx.status}


@router.get("/{payment_id}")
def payment(payment_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    payment = db.get(Payment, payment_id)
    if not payment:
        raise HTTPException(404, "Payment not found")
    tx = db.get(Transaction, payment.transaction_id)
    if not tx or user.id not in {tx.buyer_id, tx.seller_id}:
        raise HTTPException(403, "Not allowed")
    return {
        "id": payment.id,
        "transaction_id": payment.transaction_id,
        "provider": payment.provider,
        "provider_order_id": payment.provider_order_id,
        "provider_payment_id": payment.provider_payment_id,
        "amount": payment.amount,
        "currency": payment.currency,
        "method": payment.method,
        "status": payment.status,
        "signature_verified": payment.signature_verified,
        "paid_at": payment.paid_at,
    }


@router.post("/{payment_id}/refund")
async def refund(payment_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    payment = db.get(Payment, payment_id)
    if not payment:
        raise HTTPException(404, "Payment not found")
    tx = db.get(Transaction, payment.transaction_id)
    if not tx or user.id not in {tx.buyer_id, tx.seller_id}:
        raise HTTPException(403, "Not allowed")
    if payment.status == "refunded":
        return {"ok": True, "payment_id": payment.id, "transaction_id": tx.id, "status": payment.status, "idempotent_replay": True}
    if payment.status != "captured" or not payment.provider_payment_id:
        raise HTTPException(409, "Captured payment is required for a refund")
    if tx.status == "completed":
        raise HTTPException(409, "Completed transactions cannot be refunded here")

    provider = get_provider()
    refund_result = await provider.refund(payment.provider_payment_id, payment.amount)
    payment.status = "refunded"
    payment.metadata_json = json.dumps({"refund": refund_result}, default=str)
    tx.status = "cancelled"
    tx.cancelled_at = datetime.utcnow()
    listing = db.get(Listing, tx.listing_id)
    if listing and listing.status == "reserved":
        listing.status = "active"
    if tx.swap_offer_id:
        swap = db.get(SwapOffer, tx.swap_offer_id)
        if swap:
            requested_listing = db.get(Listing, swap.requested_listing_id)
            if requested_listing and requested_listing.status == "reserved":
                requested_listing.status = "active"
            swap.status = "cancelled"
            swap.responded_at = swap.responded_at or datetime.utcnow()

    audit_record(db, user.id, "payment.refunded", "payment", payment.id, f"transaction={tx.id}")
    create_notification(
        db,
        tx.buyer_id,
        "refund",
        "Payment refunded",
        f"₹{payment.amount} was refunded for transaction #{tx.id}.",
        f"/transactions/{tx.id}",
    )
    create_notification(
        db,
        tx.seller_id,
        "refund",
        "Transaction refunded",
        f"Transaction #{tx.id} was refunded.",
        f"/transactions/{tx.id}",
    )
    db.commit()
    return {"ok": True, "payment_id": payment.id, "transaction_id": tx.id, "status": payment.status}
