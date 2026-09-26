
from decimal import Decimal
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.models import ReputationEvent, Review, SellerProfile

def calculate_score(db: Session, seller: SellerProfile) -> Decimal:
    rating_avg = db.scalar(select(func.avg(Review.rating)).where(Review.reviewee_id == seller.user_id)) or 0
    rating_component = Decimal(str(rating_avg)) * Decimal("13")
    completion_component = Decimal(str(min(seller.completed_orders, 50))) * Decimal("0.35")
    cancellation_penalty = Decimal(str(min(seller.cancellations, 20))) * Decimal("1.75")
    response_component = Decimal(str(seller.response_rate or 0)) * Decimal("0.08")
    verified_bonus = Decimal("8") if seller.verified else Decimal("0")
    event_adjustment = db.scalar(
        select(func.coalesce(func.sum(ReputationEvent.weight), 0))
        .where(ReputationEvent.seller_id == seller.id)
    ) or 0
    score = (
        Decimal("26")
        + rating_component
        + completion_component
        + response_component
        + verified_bonus
        + Decimal(str(event_adjustment))
        - cancellation_penalty
    )
    return max(Decimal("0"), min(score, Decimal("100"))).quantize(Decimal("0.01"))

def refresh_seller_score(db: Session, seller_id: int, commit: bool = False):
    seller = db.get(SellerProfile, seller_id)
    if not seller:
        return None
    seller.reputation_score = calculate_score(db, seller)
    if commit:
        db.commit()
        db.refresh(seller)
    return seller.reputation_score
