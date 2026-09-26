
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload, selectinload
from app.db import get_db
from app.deps import current_user, require_verified_member
from app.models import Review, SellerProfile, Transaction, User, Listing
from app.schemas import SellerApplyIn
from app.services.reputation import refresh_seller_score

router = APIRouter(prefix="/api/sellers", tags=["sellers"])

@router.post("/apply")
def apply(data: SellerApplyIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if not user.email_verified:
        raise HTTPException(403, "Verify your email first")
    seller = user.seller_profile
    if seller:
        seller.display_name = data.display_name
        seller.bio = data.bio
    else:
        seller = SellerProfile(user_id=user.id, display_name=data.display_name, bio=data.bio, verified=user.email_verified)
        db.add(seller)
    db.commit()
    db.refresh(seller)
    return {"id": seller.id, "display_name": seller.display_name, "bio": seller.bio, "verified": seller.verified,
            "reputation_score": seller.reputation_score, "completed_orders": seller.completed_orders,
            "cancellations": seller.cancellations, "response_rate": seller.response_rate}

@router.get("/me")
def my_seller(user: User = Depends(current_user), db: Session = Depends(get_db)):
    seller = db.scalar(select(SellerProfile).where(SellerProfile.user_id == user.id))
    if not seller:
        raise HTTPException(404, "Seller profile not found")
    return {"id": seller.id, "user_id": seller.user_id, "display_name": seller.display_name, "bio": seller.bio,
            "verified": seller.verified, "reputation_score": float(seller.reputation_score), "completed_orders": seller.completed_orders,
            "cancellations": seller.cancellations, "response_rate": float(seller.response_rate)}

@router.get("/me/listings")
async def my_listings(user: User = Depends(current_user), db: Session = Depends(get_db)):
    seller = db.scalar(select(SellerProfile).where(SellerProfile.user_id == user.id))
    if not seller:
        raise HTTPException(404, "Seller profile not found")
    from app.services.listings import listing_output
    rows = db.scalars(select(Listing).options(joinedload(Listing.campus), joinedload(Listing.seller), selectinload(Listing.images))
                      .where(Listing.seller_id == seller.id).order_by(Listing.created_at.desc())).all()
    return [await listing_output(x) for x in rows]

@router.get("/{seller_id}")
def seller_detail(seller_id: int, db: Session = Depends(get_db)):
    seller = db.get(SellerProfile, seller_id)
    if not seller:
        raise HTTPException(404, "Seller not found")
    avg = db.scalar(select(func.avg(Review.rating)).where(Review.reviewee_id == seller.user_id))
    return {"id": seller.id, "user_id": seller.user_id, "display_name": seller.display_name, "bio": seller.bio,
            "verified": seller.verified, "reputation_score": float(seller.reputation_score), "completed_orders": seller.completed_orders,
            "cancellations": seller.cancellations, "response_rate": float(seller.response_rate), "average_rating": round(float(avg or 0), 2)}
