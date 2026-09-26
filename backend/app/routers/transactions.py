from sqlalchemy import desc, or_, select
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import current_user
from app.models import Listing, Offer, Payment, PickupLocation, SellerProfile, Transaction, User
from app.schemas import HandoffIn, PickupScheduleIn, ReviewIn
from app.services.transactions import (
    add_review,
    cancel_transaction,
    confirm_handoff,
    ensure_handoff_code,
    get_transaction,
    schedule_pickup,
)

router = APIRouter(prefix="/api/transactions", tags=["transactions"])


def out(tx: Transaction, user_id: int | None = None, db: Session | None = None):
    role = "buyer" if user_id == tx.buyer_id else "seller" if user_id == tx.seller_id else None
    listing = db.get(Listing, tx.listing_id) if db else None
    buyer = db.get(User, tx.buyer_id) if db else None
    seller = db.get(User, tx.seller_id) if db else None
    payment = db.scalar(select(Payment).where(Payment.transaction_id == tx.id)) if db else None

    handoff_code = None
    if role == "buyer" and tx.pickup_date and tx.pickup_time:
        handoff_code = ensure_handoff_code(tx)

    return {
        "id": tx.id,
        "listing_id": tx.listing_id,
        "offer_id": tx.offer_id,
        "swap_offer_id": tx.swap_offer_id,
        "buyer_id": tx.buyer_id,
        "seller_id": tx.seller_id,
        "buyer_name": buyer.name if buyer else None,
        "seller_name": seller.name if seller else None,
        "agreed_price": tx.agreed_price,
        "status": tx.status,
        "pickup_location_id": tx.pickup_location_id,
        "pickup_address": tx.pickup_address_snapshot,
        "pickup_landmark": tx.pickup_landmark,
        "pickup_date": tx.pickup_date,
        "pickup_time": tx.pickup_time,
        "handoff_code": handoff_code,
        "buyer_handoff_confirmed": tx.buyer_handoff_confirmed,
        "seller_handoff_confirmed": tx.seller_handoff_confirmed,
        "paid_at": tx.paid_at,
        "completed_at": tx.completed_at,
        "cancelled_at": tx.cancelled_at,
        "payment_id": payment.id if payment else None,
        "payment_status": payment.status if payment else None,
        "viewer_role": role,
        "listing_title": listing.title if listing else None,
        "listing_status": listing.status if listing else None,
    }


@router.get("")
def list_transactions(user: User = Depends(current_user), db: Session = Depends(get_db)):
    txs = db.scalars(
        select(Transaction)
        .where(or_(Transaction.buyer_id == user.id, Transaction.seller_id == user.id))
        .order_by(desc(Transaction.created_at))
    ).all()
    return [out(x, user.id, db) for x in txs]


@router.get("/{transaction_id}")
def detail(transaction_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    tx = get_transaction(db, transaction_id)
    if user.id not in {tx.buyer_id, tx.seller_id}:
        raise HTTPException(403, "Not a participant")
    return out(tx, user.id, db)


@router.post("/{transaction_id}/pickup")
def schedule(
    transaction_id: int,
    data: PickupScheduleIn,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    tx = get_transaction(db, transaction_id)
    code = schedule_pickup(
        db,
        tx,
        user.id,
        data.pickup_location_id,
        data.pickup_address_id,
        data.pickup_date,
        data.pickup_time,
    )
    db.commit()
    return {
        "transaction": out(tx, user.id, db),
        "handoff_code": code if user.id == tx.buyer_id else None,
    }


@router.post("/{transaction_id}/handoff")
def handoff(
    transaction_id: int,
    data: HandoffIn,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    tx = get_transaction(db, transaction_id)
    tx = confirm_handoff(db, tx, user.id, data.code)
    db.commit()
    return out(tx, user.id, db)


@router.post("/{transaction_id}/cancel")
def cancel(transaction_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    tx = get_transaction(db, transaction_id)
    tx = cancel_transaction(db, tx, user.id)
    db.commit()
    return out(tx, user.id, db)


@router.post("/{transaction_id}/review")
def review(
    transaction_id: int,
    data: ReviewIn,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    tx = get_transaction(db, transaction_id)
    item = add_review(db, tx, user.id, data)
    db.commit()
    return {
        "id": item.id,
        "transaction_id": item.transaction_id,
        "reviewer_id": item.reviewer_id,
        "reviewee_id": item.reviewee_id,
        "rating": item.rating,
        "comment": item.comment,
    }
