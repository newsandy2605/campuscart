from collections import Counter
from decimal import Decimal
from sqlalchemy import desc, select
from sqlalchemy.orm import Session
from app.models import InteractionEvent, Listing, ListingCourse, StudentCourse

async def recommend(db: Session, campus_id: int, user_id: int | None, limit: int = 8):
    listings = list(db.scalars(
        select(Listing)
        .where(Listing.campus_id == campus_id, Listing.status == "active")
        .order_by(desc(Listing.favorites), desc(Listing.views), desc(Listing.created_at))
        .limit(100)
    ))
    preferred = Counter()
    course_listing_ids = set()
    if user_id:
        events = db.scalars(
            select(InteractionEvent)
            .where(InteractionEvent.user_id == user_id, InteractionEvent.campus_id == campus_id)
            .order_by(desc(InteractionEvent.created_at)).limit(150)
        )
        for e in events:
            if e.category:
                preferred[e.category.lower()] += 3 if e.event_type in {"favorite", "offer", "purchase"} else 1
        course_listing_ids = {row[0] for row in db.execute(
            select(ListingCourse.listing_id)
            .join(StudentCourse, ListingCourse.course_id == StudentCourse.course_id)
            .where(StudentCourse.user_id == user_id)
        ).all()}
    scored = []
    for item in listings:
        score = Decimal(item.favorites) * Decimal("1.8") + Decimal(item.views) * Decimal("0.12")
        score += Decimal(preferred[item.category.lower()] * 3)
        if item.condition in {"new", "like-new"}:
            score += Decimal("1.5")
        if item.id in course_listing_ids:
            score += Decimal("8")
        if item.distance_km is not None:
            score += max(Decimal("0"), Decimal("2") - item.distance_km / Decimal("2"))
        reason = "Popular with students on this campus"
        if item.id in course_listing_ids:
            reason = "Relevant to one of your current courses"
        elif preferred[item.category.lower()]:
            reason = f"Matches your interest in {item.category}"
        elif item.distance_km is not None and item.distance_km <= 1:
            reason = "Close to your campus pickup area"
        scored.append((score, item, reason))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [{"listing": item, "score": round(float(score), 2), "reason": reason} for score, item, reason in scored[:limit]]
