from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import current_user, optional_user, require_verified_member
from app.models import Campus, LostFoundItem, User
from app.schemas import LostFoundClaimIn, LostFoundCreateIn
from app.services.audit import record as audit_record
from app.services.notifications import create_notification

router = APIRouter(prefix="/api/lost-found", tags=["lost-found"])


def _out(item: LostFoundItem, user: User | None = None):
    return {
        "id": item.id, "item_type": item.item_type, "title": item.title, "description": item.description,
        "location_text": item.location_text, "item_date": item.item_date, "status": item.status,
        "is_owner": bool(user and item.user_id == user.id), "claimant_id": item.claimant_id,
        "claim_message": item.claim_message, "claimed_at": item.claimed_at, "resolved_at": item.resolved_at, "created_at": item.created_at,
    }


@router.post("")
def create(data: LostFoundCreateIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    campus, _ = require_verified_member(data.campus_slug, user, db)
    item = LostFoundItem(campus_id=campus.id, user_id=user.id, **data.model_dump(exclude={"campus_slug"}))
    db.add(item); db.commit(); db.refresh(item)
    return _out(item, user)


@router.get("")
def list_items(campus_slug: str, type: str = "", user: User | None = Depends(optional_user), db: Session = Depends(get_db)):
    campus = db.scalar(select(Campus).where(Campus.slug == campus_slug, Campus.active.is_(True)))
    if not campus: raise HTTPException(404, "Campus not found")
    q = select(LostFoundItem).where(LostFoundItem.campus_id == campus.id, LostFoundItem.status.in_(["open", "claimed"]))
    if type: q = q.where(LostFoundItem.item_type == type)
    rows = db.scalars(q.order_by(desc(LostFoundItem.created_at))).all()
    return [_out(row, user) for row in rows]


@router.post("/{item_id}/claim")
def claim(item_id: int, data: LostFoundClaimIn | None = None, user: User = Depends(current_user), db: Session = Depends(get_db)):
    item = db.get(LostFoundItem, item_id)
    if not item: raise HTTPException(404, "Lost & found item not found")
    if item.status != "open": raise HTTPException(409, "Item is no longer open")
    require_verified_member(item.campus.slug, user, db)
    if item.user_id == user.id: raise HTTPException(400, "You cannot claim your own post")
    if item.item_type != "found": raise HTTPException(400, "Only found items can be claimed")
    item.claimant_id = user.id; item.claim_message = (data.message.strip() if data else ""); item.claimed_at = datetime.utcnow(); item.status = "claimed"
    audit_record(db, user.id, "lost_found.claim_submitted", "lost_found", item.id, item.claim_message[:300])
    create_notification(db, item.user_id, "lost_found", "Claim request received", f"{user.name} says '{item.title}' belongs to them. Review the claim in Lost & Found.", "/lost-found")
    create_notification(db, user.id, "lost_found", "Claim submitted", f"Your claim for '{item.title}' was sent to the poster.", "/lost-found")
    db.commit()
    return {"id": item.id, "status": item.status, "claimant_id": item.claimant_id}


@router.post("/{item_id}/confirm")
def confirm_claim(item_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    item = db.get(LostFoundItem, item_id)
    if not item or item.user_id != user.id: raise HTTPException(404, "Lost & found item not found")
    if item.status != "claimed" or not item.claimant_id: raise HTTPException(409, "No pending claim to confirm")
    item.status = "closed"; item.resolved_at = datetime.utcnow()
    audit_record(db, user.id, "lost_found.claim_confirmed", "lost_found", item.id)
    create_notification(db, item.claimant_id, "lost_found", "Claim confirmed", f"The poster confirmed your claim for '{item.title}'.", "/lost-found")
    db.commit()
    return {"id": item.id, "status": item.status}


@router.post("/{item_id}/reject-claim")
def reject_claim(item_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    item = db.get(LostFoundItem, item_id)
    if not item or item.user_id != user.id: raise HTTPException(404, "Lost & found item not found")
    if item.status != "claimed" or not item.claimant_id: raise HTTPException(409, "No pending claim to reject")
    claimant = item.claimant_id; item.claimant_id = None; item.claim_message = ""; item.claimed_at = None; item.status = "open"
    audit_record(db, user.id, "lost_found.claim_rejected", "lost_found", item.id)
    create_notification(db, claimant, "lost_found", "Claim needs more information", f"The poster did not confirm your claim for '{item.title}'.", "/lost-found")
    db.commit()
    return {"id": item.id, "status": item.status}


@router.post("/{item_id}/close")
def close(item_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    item = db.get(LostFoundItem, item_id)
    if not item or item.user_id != user.id: raise HTTPException(404, "Lost & found item not found")
    item.status = "closed"; item.resolved_at = datetime.utcnow()
    audit_record(db, user.id, "lost_found.closed", "lost_found", item.id)
    db.commit()
    return {"id": item.id, "status": item.status}
