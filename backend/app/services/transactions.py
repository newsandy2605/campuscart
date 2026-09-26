from __future__ import annotations

from datetime import date, datetime, time

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Address, Listing, PickupLocation, Review, SellerProfile, SwapOffer, Transaction
from app.security import generate_handoff_code, hash_value
from app.services.notifications import create_notification
from app.services.reputation import refresh_seller_score
from app.services.audit import record as audit_record


ACTIVE_TRANSACTION_STATUSES = {
    "awaiting_payment",
    "paid",
    "pickup_scheduled",
    "waiting_handoff",
    "swap_accepted",
}


def get_transaction(db: Session, tx_id: int) -> Transaction:
    tx = db.scalar(select(Transaction).where(Transaction.id == tx_id))
    if not tx:
        raise HTTPException(404, "Transaction not found")
    return tx


def ensure_handoff_code(tx: Transaction) -> str:
    code = generate_handoff_code(tx.id)
    expected_hash = hash_value(code)
    if tx.handoff_code_hash != expected_hash:
        tx.handoff_code_hash = expected_hash
    return code


def schedule_pickup(
    db: Session,
    tx: Transaction,
    user_id: int,
    pickup_location_id: int | None,
    pickup_address_id: int | None,
    pickup_date: date,
    pickup_time: time,
):
    if user_id not in {tx.buyer_id, tx.seller_id}:
        raise HTTPException(403, "Not a participant in this transaction")

    if tx.status not in {"paid", "pickup_scheduled", "waiting_handoff", "swap_accepted"}:
        raise HTTPException(409, "Payment or swap acceptance is required before pickup can be scheduled")

    if pickup_date < date.today():
        raise HTTPException(400, "Pickup date cannot be in the past")

    if pickup_location_id:
        location = db.get(PickupLocation, pickup_location_id)
        if not location or not location.active:
            raise HTTPException(404, "Pickup location not found")

        listing = db.get(Listing, tx.listing_id)
        if not listing or location.campus_id != listing.campus_id:
            raise HTTPException(400, "Pickup location does not belong to this campus")

        tx.pickup_location_id = location.id
        tx.pickup_address_snapshot = location.address
        tx.pickup_landmark = location.landmark

    elif pickup_address_id:
        address = db.get(Address, pickup_address_id)
        if not address or address.user_id != user_id:
            raise HTTPException(403, "Pickup address is not available to this user")

        tx.pickup_address_snapshot = ", ".join(
            part
            for part in [
                address.line1,
                address.line2,
                address.locality,
                address.city,
                address.state,
                address.pincode,
            ]
            if part
        )
        tx.pickup_landmark = address.landmark
        tx.pickup_location_id = None
    else:
        raise HTTPException(400, "Choose a pickup location or address")

    tx.pickup_date = pickup_date
    tx.pickup_time = pickup_time
    code = ensure_handoff_code(tx)
    tx.status = "pickup_scheduled"

    create_notification(
        db,
        tx.buyer_id,
        "pickup",
        "Pickup scheduled",
        f"Transaction #{tx.id} is scheduled for {pickup_date.isoformat()} at {pickup_time.strftime('%H:%M')}.",
        f"/transactions/{tx.id}",
    )
    if tx.seller_id != tx.buyer_id:
        create_notification(
            db,
            tx.seller_id,
            "pickup",
            "Pickup scheduled",
            f"Transaction #{tx.id} is scheduled for {pickup_date.isoformat()} at {pickup_time.strftime('%H:%M')}.",
            f"/transactions/{tx.id}",
        )

    return code


def mark_paid(db: Session, tx: Transaction) -> None:
    if tx.status == "awaiting_payment":
        tx.status = "paid"
        tx.paid_at = datetime.utcnow()
        create_notification(
            db,
            tx.seller_id,
            "payment",
            "Payment received",
            f"₹{tx.agreed_price} payment recorded for transaction #{tx.id}.",
            f"/transactions/{tx.id}",
        )


def confirm_handoff(db: Session, tx: Transaction, user_id: int, code: str | None):
    if tx.status not in {"pickup_scheduled", "waiting_handoff"}:
        raise HTTPException(409, "Transaction is not ready for handoff")
    if user_id not in {tx.buyer_id, tx.seller_id}:
        raise HTTPException(403, "Not a participant")
    if not tx.pickup_date or not tx.pickup_time:
        raise HTTPException(409, "Pickup must be scheduled first")
    if date.today() < tx.pickup_date:
        raise HTTPException(409, f"Handoff becomes available on {tx.pickup_date.isoformat()}")

    expected_code = ensure_handoff_code(tx)

    if user_id == tx.seller_id:
        if not code:
            raise HTTPException(400, "Enter the 4-digit handoff code provided by the buyer")
        if code != expected_code:
            raise HTTPException(400, "Invalid handoff code")
        tx.seller_handoff_confirmed = True
        tx.status = "waiting_handoff"
        audit_record(db, user_id, "transaction.handoff_confirmed", "transaction", tx.id, "seller")
        create_notification(
            db,
            tx.buyer_id,
            "transaction",
            "Seller confirmed handoff",
            f"The seller confirmed the handoff for transaction #{tx.id}. Confirm that you received the item.",
            f"/transactions/{tx.id}",
        )
    else:
        if not tx.seller_handoff_confirmed:
            raise HTTPException(409, "Seller must confirm the handoff before you confirm receipt")
        tx.buyer_handoff_confirmed = True
        audit_record(db, user_id, "transaction.handoff_confirmed", "transaction", tx.id, "buyer_receipt")

    if tx.buyer_handoff_confirmed and tx.seller_handoff_confirmed:
        tx.status = "completed"
        tx.completed_at = datetime.utcnow()
        listing = db.get(Listing, tx.listing_id)
        if listing:
            listing.status = "completed"

        if tx.swap_offer_id:
            swap = db.get(SwapOffer, tx.swap_offer_id)
            if swap:
                requested_listing = db.get(Listing, swap.requested_listing_id)
                if requested_listing:
                    requested_listing.status = "completed"
                swap.status = "completed"
                swap.responded_at = swap.responded_at or datetime.utcnow()

        seller = db.scalar(select(SellerProfile).where(SellerProfile.user_id == tx.seller_id))
        if seller:
            seller.completed_orders += 1
            refresh_seller_score(db, seller.id)

        create_notification(
            db,
            tx.buyer_id,
            "transaction",
            "Transaction completed",
            f"Transaction #{tx.id} is complete. You can now review the seller.",
            f"/transactions/{tx.id}",
        )
        create_notification(
            db,
            tx.seller_id,
            "transaction",
            "Transaction completed",
            f"Transaction #{tx.id} is complete. You can now review the buyer.",
            f"/transactions/{tx.id}",
        )

    return tx


def cancel_transaction(db: Session, tx: Transaction, user_id: int):
    if user_id not in {tx.buyer_id, tx.seller_id}:
        raise HTTPException(403, "Not a participant")
    if tx.status == "completed":
        raise HTTPException(409, "Completed transaction cannot be cancelled")
    if tx.status in {"paid", "pickup_scheduled", "waiting_handoff"}:
        raise HTTPException(
            409,
            "This transaction has been paid. Use the refund flow before cancelling it.",
        )

    tx.status = "cancelled"
    tx.cancelled_at = datetime.utcnow()
    audit_record(db, user_id, "transaction.cancelled", "transaction", tx.id)
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

    seller = db.scalar(select(SellerProfile).where(SellerProfile.user_id == tx.seller_id))
    if seller:
        seller.cancellations += 1
        refresh_seller_score(db, seller.id)
    create_notification(db, tx.buyer_id, "transaction", "Transaction cancelled", f"Transaction #{tx.id} was cancelled.", f"/transactions/{tx.id}")
    if tx.seller_id != tx.buyer_id:
        create_notification(db, tx.seller_id, "transaction", "Transaction cancelled", f"Transaction #{tx.id} was cancelled.", f"/transactions/{tx.id}")
    return tx


def add_review(db: Session, tx: Transaction, reviewer_id: int, data):
    if tx.status != "completed":
        raise HTTPException(409, "Reviews are available after transaction completion")

    if reviewer_id == tx.buyer_id:
        reviewee = tx.seller_id
    elif reviewer_id == tx.seller_id:
        reviewee = tx.buyer_id
    else:
        raise HTTPException(403, "Not a participant")

    exists = db.scalar(
        select(Review).where(
            Review.transaction_id == tx.id,
            Review.reviewer_id == reviewer_id,
        )
    )
    if exists:
        raise HTTPException(409, "You already reviewed this transaction")

    review = Review(
        transaction_id=tx.id,
        reviewer_id=reviewer_id,
        reviewee_id=reviewee,
        rating=data.rating,
        comment=data.comment,
    )
    db.add(review)
    db.flush()

    if reviewee == tx.seller_id:
        seller = db.scalar(select(SellerProfile).where(SellerProfile.user_id == reviewee))
        if seller:
            refresh_seller_score(db, seller.id)

    return review
