from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import current_user, require_verified_member
from app.models import Campus, Conversation, Listing, Offer, Transaction, User
from app.schemas import OfferCreateIn
from app.services.notifications import create_notification
from app.services.rate_limit import check_offer_rate

router = APIRouter(prefix="/api/offers", tags=["offers"])


def offer_out(o: Offer, db: Session):
    buyer = db.get(User, o.buyer_id)
    seller = db.get(User, o.seller_id)
    listing = db.get(Listing, o.listing_id)
    return {
        "id": o.id,
        "listing_id": o.listing_id,
        "buyer_id": o.buyer_id,
        "seller_id": o.seller_id,
        "buyer_name": buyer.name if buyer else None,
        "seller_name": seller.name if seller else None,
        "listing_title": listing.title if listing else None,
        "amount": o.amount,
        "message": o.message,
        "status": o.status,
        "expires_at": o.expires_at,
        "created_at": o.created_at,
        "responded_at": o.responded_at,
    }


@router.post("")
def create_offer(data: OfferCreateIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    try:
        check_offer_rate(user.id)
    except ValueError as exc:
        raise HTTPException(429, str(exc)) from exc

    listing = db.scalar(select(Listing).where(Listing.id == data.listing_id).with_for_update())
    if not listing or listing.status != "active":
        raise HTTPException(404, "Listing is not available")

    campus = db.get(Campus, listing.campus_id)
    if not campus:
        raise HTTPException(404, "Campus not found")
    require_verified_member(campus.slug, user, db)

    if listing.seller.user_id == user.id:
        raise HTTPException(400, "You cannot offer on your own listing")
    if data.amount <= 0:
        raise HTTPException(400, "Offer must be positive")

    duplicate = db.scalar(
        select(Offer).where(
            Offer.listing_id == listing.id,
            Offer.buyer_id == user.id,
            Offer.status == "pending",
        )
    )
    if duplicate:
        raise HTTPException(409, "You already have a pending offer on this listing")

    offer = Offer(
        listing_id=listing.id,
        buyer_id=user.id,
        seller_id=listing.seller.user_id,
        amount=data.amount,
        message=data.message.strip(),
        expires_at=datetime.utcnow() + timedelta(hours=data.expires_hours),
    )
    db.add(offer)
    db.flush()
    create_notification(
        db,
        offer.seller_id,
        "offer",
        "New offer received",
        f"₹{offer.amount} offered for {listing.title}.",
        f"/offers/{offer.id}",
    )
    db.commit()
    return offer_out(offer, db)


@router.get("/inbox")
def inbox(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return [
        offer_out(o, db)
        for o in db.scalars(
            select(Offer).where(Offer.seller_id == user.id).order_by(desc(Offer.created_at))
        ).all()
    ]


@router.get("/sent")
def sent(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return [
        offer_out(o, db)
        for o in db.scalars(
            select(Offer).where(Offer.buyer_id == user.id).order_by(desc(Offer.created_at))
        ).all()
    ]


@router.post("/{offer_id}/accept")
def accept(offer_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    offer = db.scalar(select(Offer).where(Offer.id == offer_id).with_for_update())
    if not offer:
        raise HTTPException(404, "Offer not found")
    if offer.seller_id != user.id:
        raise HTTPException(403, "Only the seller can accept this offer")
    if offer.status != "pending":
        raise HTTPException(409, "Offer is not pending")
    if offer.expires_at and offer.expires_at <= datetime.utcnow():
        offer.status = "expired"
        offer.responded_at = datetime.utcnow()
        db.commit()
        raise HTTPException(409, "Offer has expired")

    listing = db.scalar(select(Listing).where(Listing.id == offer.listing_id).with_for_update())
    if not listing or listing.status != "active":
        raise HTTPException(409, "Listing is no longer available")

    offer.status = "accepted"
    offer.responded_at = datetime.utcnow()
    listing.status = "reserved"

    pending_offers = db.scalars(
        select(Offer).where(
            Offer.listing_id == listing.id,
            Offer.id != offer.id,
            Offer.status == "pending",
        )
    ).all()
    now = datetime.utcnow()
    for other in pending_offers:
        other.status = "rejected"
        other.responded_at = now
        create_notification(
            db,
            other.buyer_id,
            "offer",
            "Listing reserved",
            f"Another offer was accepted for {listing.title}.",
            f"/marketplace/{listing.id}",
        )

    tx = Transaction(
        listing_id=listing.id,
        offer_id=offer.id,
        buyer_id=offer.buyer_id,
        seller_id=offer.seller_id,
        agreed_price=offer.amount,
        status="awaiting_payment",
        pickup_address_snapshot=listing.pickup_area,
        pickup_landmark=listing.pickup_landmark,
    )

    if listing.pickup_location_id:
        tx.pickup_location_id = listing.pickup_location_id

    if listing.pickup_address_id:
        from app.models import Address
        address = db.get(Address, listing.pickup_address_id)
        if address and address.user_id == user.id:
            tx.pickup_address_snapshot = ", ".join(
                part
                for part in [address.line1, address.line2, address.locality, address.city, address.state, address.pincode]
                if part
            )
            tx.pickup_landmark = address.landmark

    db.add(tx)
    db.flush()

    conversation = db.scalar(
        select(Conversation).where(
            Conversation.listing_id == listing.id,
            Conversation.buyer_id == offer.buyer_id,
            Conversation.seller_id == offer.seller_id,
        )
    )
    if not conversation:
        conversation = Conversation(
            listing_id=listing.id,
            buyer_id=offer.buyer_id,
            seller_id=offer.seller_id,
        )
        db.add(conversation)
        db.flush()
    conversation.transaction_id = tx.id

    create_notification(
        db,
        offer.buyer_id,
        "offer",
        "Offer accepted",
        f"Your ₹{offer.amount} offer for {listing.title} was accepted.",
        f"/transactions/{tx.id}",
    )
    db.commit()
    return {"offer": offer_out(offer, db), "transaction_id": tx.id, "listing_status": listing.status}


@router.post("/{offer_id}/reject")
def reject(offer_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    offer = db.get(Offer, offer_id)
    if not offer or offer.seller_id != user.id:
        raise HTTPException(404, "Offer not found")
    if offer.status != "pending":
        raise HTTPException(409, "Offer is not pending")
    offer.status = "rejected"
    offer.responded_at = datetime.utcnow()
    db.commit()
    create_notification(
        db,
        offer.buyer_id,
        "offer",
        "Offer declined",
        f"Your offer #{offer.id} was declined.",
        f"/offers/{offer.id}",
    )
    db.commit()
    return offer_out(offer, db)


@router.post("/{offer_id}/withdraw")
def withdraw(offer_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    offer = db.get(Offer, offer_id)
    if not offer or offer.buyer_id != user.id:
        raise HTTPException(404, "Offer not found")
    if offer.status != "pending":
        raise HTTPException(409, "Offer is not pending")
    offer.status = "withdrawn"
    offer.responded_at = datetime.utcnow()
    db.commit()
    return offer_out(offer, db)
