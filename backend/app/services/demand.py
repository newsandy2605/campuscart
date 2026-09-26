from datetime import datetime, timedelta
from statistics import median

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import InteractionEvent, Listing, Offer, Transaction, WantedPost


def _median_or_none(values):
    return round(float(median(values)), 2) if values else None


def demand_radar(db: Session, campus_id: int):
    wanted_rows = db.execute(
        select(WantedPost.category, func.count(WantedPost.id))
        .where(WantedPost.campus_id == campus_id, WantedPost.status == "open")
        .group_by(WantedPost.category)
    ).all()

    listing_rows = db.execute(
        select(Listing.category, func.count(Listing.id))
        .where(Listing.campus_id == campus_id, Listing.status == "active")
        .group_by(Listing.category)
    ).all()

    interest_rows = db.execute(
        select(InteractionEvent.category, func.count(InteractionEvent.id))
        .where(
            InteractionEvent.campus_id == campus_id,
            InteractionEvent.created_at >= datetime.utcnow() - timedelta(days=14),
            InteractionEvent.category != "",
        )
        .group_by(InteractionEvent.category)
        .order_by(func.count(InteractionEvent.id).desc())
        .limit(20)
    ).all()

    wanted_map = {category: count for category, count in wanted_rows}
    listing_map = {category: count for category, count in listing_rows}
    interest_map = {category: count for category, count in interest_rows}
    categories = set(wanted_map) | set(listing_map) | set(interest_map)

    result = []
    for category in categories:
        active = listing_map.get(category, 0)
        wanted = wanted_map.get(category, 0)

        accepted = db.execute(
            select(Offer.amount)
            .join(Listing, Offer.listing_id == Listing.id)
            .where(
                Listing.campus_id == campus_id,
                Listing.category == category,
                Offer.status == "accepted",
            )
        ).scalars().all()
        completed = db.execute(
            select(Transaction.agreed_price)
            .join(Listing, Transaction.listing_id == Listing.id)
            .where(
                Listing.campus_id == campus_id,
                Listing.category == category,
                Transaction.status == "completed",
            )
        ).scalars().all()
        prices = [float(x) for x in list(accepted) + list(completed)]

        result.append({
            "category": category,
            "wanted": wanted,
            "active_listings": active,
            "demand_supply_ratio": round(wanted / active, 2) if active else float(wanted),
            "typical_accepted_price": _median_or_none(prices),
            "recent_interest_events": interest_map.get(category, 0),
            "demand_level": (
                "HIGH" if wanted > active and wanted >= 3 else
                "MEDIUM" if wanted else
                "LOW"
            ),
        })

    result.sort(key=lambda x: (x["wanted"], x["recent_interest_events"]), reverse=True)
    return result


def price_insight(db: Session, campus_id: int, category: str):
    active = db.scalars(
        select(Listing.price).where(
            Listing.campus_id == campus_id,
            Listing.category == category,
            Listing.status == "active",
        )
    ).all()
    accepted = db.execute(
        select(Offer.amount)
        .join(Listing, Offer.listing_id == Listing.id)
        .where(
            Listing.campus_id == campus_id,
            Listing.category == category,
            Offer.status == "accepted",
        )
    ).scalars().all()
    completed = db.execute(
        select(Transaction.agreed_price)
        .join(Listing, Transaction.listing_id == Listing.id)
        .where(
            Listing.campus_id == campus_id,
            Listing.category == category,
            Transaction.status == "completed",
        )
    ).scalars().all()

    prices = [float(x) for x in list(accepted) + list(completed)] or [float(x) for x in active]
    if not prices:
        return {
            "category": category,
            "sample_size": 0,
            "low": None,
            "median": None,
            "high": None,
            "confidence": "low",
        }

    prices.sort()
    n = len(prices)
    low = prices[max(0, int(n * 0.25) - 1)]
    high = prices[min(n - 1, int(n * 0.75))]
    return {
        "category": category,
        "sample_size": n,
        "low": round(low, 2),
        "median": round(prices[n // 2], 2),
        "high": round(high, 2),
        "confidence": "high" if n >= 15 else "medium" if n >= 5 else "low",
        "based_on": "completed sales and accepted offers" if (accepted or completed) else "active listings",
    }
