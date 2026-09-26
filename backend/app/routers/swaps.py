from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, or_, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import current_user, require_verified_member
from app.models import Conversation, Listing, SwapOffer, Transaction, User
from app.schemas import SwapCreateIn
from app.services.notifications import create_notification
from app.services.matching import swap_compatibility

router = APIRouter(prefix="/api/swaps", tags=["swaps"])


def swap_out(swap: SwapOffer, db: Session):
    offered = db.get(Listing, swap.offered_listing_id)
    requested = db.get(Listing, swap.requested_listing_id)
    proposer = db.get(User, swap.proposer_id)
    receiver = db.get(User, swap.receiver_id)
    return {
        "id": swap.id,
        "proposer_id": swap.proposer_id,
        "receiver_id": swap.receiver_id,
        "proposer_name": proposer.name if proposer else None,
        "receiver_name": receiver.name if receiver else None,
        "offered_listing_id": swap.offered_listing_id,
        "offered_listing_title": offered.title if offered else None,
        "requested_listing_id": swap.requested_listing_id,
        "requested_listing_title": requested.title if requested else None,
        "message": swap.message,
        "status": swap.status,
        "compatibility": swap_compatibility(offered, requested) if offered and requested else 0,
        "created_at": swap.created_at,
        "responded_at": swap.responded_at,
        "transaction_id": next((t.id for t in db.scalars(select(Transaction).where(Transaction.swap_offer_id == swap.id)).all()), None),
    }


@router.get("/options")
def swap_options(campus_slug: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    campus, _ = require_verified_member(campus_slug, user, db)
    mine = db.scalars(
        select(Listing)
        .where(
            Listing.campus_id == campus.id,
            Listing.seller.has(user_id=user.id),
            Listing.status == "active",
        )
        .order_by(desc(Listing.created_at))
    ).all()
    candidates = db.scalars(
        select(Listing)
        .where(
            Listing.campus_id == campus.id,
            Listing.status == "active",
            Listing.seller.has(user_id != user.id),
        )
        .order_by(desc(Listing.created_at))
        .limit(100)
    ).all()
    return {
        "my_listings": [{"id": x.id, "title": x.title, "category": x.category, "price": x.price} for x in mine],
        "candidate_listings": [
            {"id": x.id, "title": x.title, "category": x.category, "price": x.price, "seller_id": x.seller.user_id}
            for x in candidates
        ],
    }


@router.post("")
def propose(data: SwapCreateIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    offered = db.scalar(select(Listing).where(Listing.id == data.offered_listing_id).with_for_update())
    requested = db.scalar(select(Listing).where(Listing.id == data.requested_listing_id).with_for_update())
    if not offered or not requested or offered.status != "active" or requested.status != "active":
        raise HTTPException(404, "Both listings must be active")
    if offered.seller.user_id != user.id:
        raise HTTPException(403, "Offered listing must belong to you")
    if requested.seller.user_id == user.id:
        raise HTTPException(400, "Requested listing must belong to another user")
    if offered.campus_id != requested.campus_id:
        raise HTTPException(400, "Swaps are currently campus-local")
    require_verified_member(offered.campus.slug, user, db)

    duplicate = db.scalar(
        select(SwapOffer).where(
            SwapOffer.proposer_id == user.id,
            SwapOffer.receiver_id == requested.seller.user_id,
            SwapOffer.offered_listing_id == offered.id,
            SwapOffer.requested_listing_id == requested.id,
            SwapOffer.status == "pending",
        )
    )
    if duplicate:
        return swap_out(duplicate, db)

    swap = SwapOffer(
        proposer_id=user.id,
        receiver_id=requested.seller.user_id,
        offered_listing_id=offered.id,
        requested_listing_id=requested.id,
        message=data.message,
    )
    db.add(swap)
    db.flush()
    create_notification(
        db,
        swap.receiver_id,
        "swap",
        "New swap proposal",
        f"{offered.title} for {requested.title}.",
        f"/swap?proposal={swap.id}",
    )
    db.commit()
    return swap_out(swap, db)


@router.get("/inbox")
def inbox(user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.scalars(
        select(SwapOffer)
        .where(SwapOffer.receiver_id == user.id)
        .order_by(desc(SwapOffer.created_at))
    ).all()
    return [swap_out(x, db) for x in rows]


@router.get("/sent")
def sent(user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.scalars(
        select(SwapOffer)
        .where(SwapOffer.proposer_id == user.id)
        .order_by(desc(SwapOffer.created_at))
    ).all()
    return [swap_out(x, db) for x in rows]


@router.post("/{swap_id}/accept")
def accept(swap_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    swap = db.scalar(select(SwapOffer).where(SwapOffer.id == swap_id).with_for_update())
    if not swap or swap.receiver_id != user.id:
        raise HTTPException(404, "Swap not found")
    if swap.status != "pending":
        raise HTTPException(409, "Swap is not pending")

    offered = db.scalar(select(Listing).where(Listing.id == swap.offered_listing_id).with_for_update())
    requested = db.scalar(select(Listing).where(Listing.id == swap.requested_listing_id).with_for_update())
    if not offered or not requested or offered.status != "active" or requested.status != "active":
        raise HTTPException(409, "One of the listings is no longer available")

    swap.status = "accepted"
    swap.responded_at = datetime.utcnow()
    offered.status = "reserved"
    requested.status = "reserved"

    tx = Transaction(
        listing_id=offered.id,
        swap_offer_id=swap.id,
        buyer_id=swap.receiver_id,
        seller_id=swap.proposer_id,
        agreed_price=0,
        status="swap_accepted",
        pickup_location_id=requested.pickup_location_id or offered.pickup_location_id,
        pickup_address_snapshot=offered.pickup_area or requested.pickup_area,
        pickup_landmark=offered.pickup_landmark or requested.pickup_landmark,
    )
    db.add(tx)
    db.flush()
    conversation = db.scalar(select(Conversation).where(Conversation.listing_id == offered.id, Conversation.buyer_id == swap.receiver_id, Conversation.seller_id == swap.proposer_id))
    if not conversation:
        conversation = Conversation(listing_id=offered.id, buyer_id=swap.receiver_id, seller_id=swap.proposer_id)
        db.add(conversation); db.flush()
    conversation.transaction_id = tx.id

    # Other pending swap proposals involving either item are no longer executable.
    db.query(SwapOffer).filter(
        SwapOffer.id != swap.id,
        SwapOffer.status == "pending",
        or_(
            SwapOffer.offered_listing_id.in_([offered.id, requested.id]),
            SwapOffer.requested_listing_id.in_([offered.id, requested.id]),
        ),
    ).update(
        {SwapOffer.status: "rejected", SwapOffer.responded_at: datetime.utcnow()},
        synchronize_session=False,
    )

    create_notification(
        db,
        swap.proposer_id,
        "swap",
        "Swap accepted",
        f"Your swap proposal for {requested.title} was accepted. Schedule pickup for transaction #{tx.id}.",
        f"/transactions/{tx.id}",
    )
    db.commit()
    result = swap_out(swap, db)
    result["transaction_id"] = tx.id
    result["transaction_status"] = tx.status
    return result


@router.post("/{swap_id}/reject")
def reject(swap_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    swap = db.get(SwapOffer, swap_id)
    if not swap or swap.receiver_id != user.id:
        raise HTTPException(404, "Swap not found")
    if swap.status != "pending":
        raise HTTPException(409, "Swap is not pending")
    swap.status = "rejected"
    swap.responded_at = datetime.utcnow()
    create_notification(
        db,
        swap.proposer_id,
        "swap",
        "Swap declined",
        "Your swap proposal was declined.",
        "/swap",
    )
    db.commit()
    return swap_out(swap, db)


@router.get("/matches")
def swap_matches(
    have_listing_id: int,
    wanted_listing_id: int | None = None,
    wanted_category: str = "",
    wanted_query: str = "",
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    have = db.scalar(select(Listing).where(Listing.id == have_listing_id))
    if not have or have.seller.user_id != user.id:
        raise HTTPException(404, "Listing not found")

    candidates = db.scalars(
        select(Listing).where(
            Listing.campus_id == have.campus_id,
            Listing.status == "active",
            Listing.seller_id != have.seller_id,
        )
    ).all()

    if wanted_listing_id:
        candidates = [x for x in candidates if x.id == wanted_listing_id]
    if wanted_category:
        candidates = [x for x in candidates if x.category.lower() == wanted_category.lower()]
    if wanted_query:
        needle = wanted_query.strip().lower()
        candidates = [
            x for x in candidates
            if needle in x.title.lower() or needle in x.category.lower() or needle in x.description.lower()
        ]

    results = []
    for listing in candidates:
        score = swap_compatibility(have, listing)
        results.append(
            {
                "listing_id": listing.id,
                "title": listing.title,
                "seller_id": listing.seller.user_id,
                "seller_name": listing.seller.display_name,
                "category": listing.category,
                "price": listing.price,
                "score": score,
            }
        )

    return sorted(results, key=lambda x: x["score"], reverse=True)[:20]


@router.get("/cycles")
def swap_cycles(user: User = Depends(current_user), campus_slug: str = "", db: Session = Depends(get_db)):
    base = db.scalars(select(Listing).where(Listing.status == "active")).all()
    if campus_slug:
        base = [x for x in base if x.campus.slug == campus_slug]

    mine = [x for x in base if x.seller.user_id == user.id]
    if not mine:
        return []

    others = [x for x in base if x.seller.user_id != user.id]
    results = []
    for first in mine:
        for a in others:
            for b in others:
                if len({a.id, b.id}) != 2:
                    continue
                if a.seller_id == b.seller_id:
                    continue
                s1 = swap_compatibility(first, a)
                s2 = swap_compatibility(a, b)
                s3 = swap_compatibility(b, first)
                if min(s1, s2, s3) < 60:
                    continue
                results.append(
                    {
                        "path": [first.id, a.id, b.id],
                        "score": round((s1 + s2 + s3) / 3, 2),
                    }
                )

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:5]
