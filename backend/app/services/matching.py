from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Listing, WantedMatch, WantedPost
from app.services.notifications import create_notification


def _text_score(left: str, right: str) -> int:
    a = set(left.lower().replace("-", " ").split())
    b = set(right.lower().replace("-", " ").split())
    if not a or not b:
        return 0
    overlap = len(a & b)
    return min(40, overlap * 12)


def score_wanted_post(post: WantedPost, listing: Listing) -> int:
    score = 0
    if post.category.strip().lower() == listing.category.strip().lower():
        score += 35
    score += _text_score(post.title, listing.title)

    if post.budget_max is not None and listing.price <= post.budget_max:
        score += 15
    if post.budget_min is not None and listing.price >= post.budget_min:
        score += 5

    if post.budget_min is not None and post.budget_max is not None:
        if post.budget_min <= listing.price <= post.budget_max:
            score += 5

    if listing.condition in {"new", "like-new"}:
        score += 3
    return min(score, 100)


def refresh_wanted_matches_for_listing(db: Session, listing: Listing) -> list[dict]:
    posts = db.scalars(
        select(WantedPost).where(
            WantedPost.campus_id == listing.campus_id,
            WantedPost.status == "open",
        )
    ).all()

    matches: list[dict] = []
    for post in posts:
        score = score_wanted_post(post, listing)
        if score < 40:
            continue

        match = db.scalar(
            select(WantedMatch).where(
                WantedMatch.wanted_post_id == post.id,
                WantedMatch.listing_id == listing.id,
            )
        )

        reason = "Matches your requested category and price range"
        if post.category.lower() == listing.category.lower():
            reason = "Same category and within the requested campus market"

        if not match:
            match = WantedMatch(
                wanted_post_id=post.id,
                listing_id=listing.id,
                score=Decimal(str(score)),
                reason=reason,
            )
            db.add(match)
            create_notification(
                db,
                post.user_id,
                "wanted_match",
                "A wanted item match was found",
                f"{listing.title} matches your request '{post.title}'.",
                f"/marketplace/{listing.id}",
            )
        else:
            match.score = Decimal(str(score))
            match.reason = reason

        matches.append(
            {"wanted_post_id": post.id, "listing_id": listing.id, "score": score, "reason": reason}
        )

    return sorted(matches, key=lambda item: item["score"], reverse=True)


def refresh_wanted_matches_for_post(db: Session, post: WantedPost) -> list[dict]:
    listings = db.scalars(
        select(Listing).where(
            Listing.campus_id == post.campus_id,
            Listing.status == "active",
        )
    ).all()
    result: list[dict] = []
    for listing in listings:
        score = score_wanted_post(post, listing)
        if score < 40:
            continue
        match = db.scalar(
            select(WantedMatch).where(
                WantedMatch.wanted_post_id == post.id,
                WantedMatch.listing_id == listing.id,
            )
        )
        reason = "Matches category/title and your budget range"
        if not match:
            match = WantedMatch(
                wanted_post_id=post.id,
                listing_id=listing.id,
                score=Decimal(str(score)),
                reason=reason,
            )
            db.add(match)
        else:
            match.score = Decimal(str(score))
        result.append({"listing_id": listing.id, "score": score, "reason": reason})
    return sorted(result, key=lambda item: item["score"], reverse=True)


def swap_compatibility(offered: Listing, requested: Listing) -> int:
    score = 0
    if offered.campus_id == requested.campus_id:
        score += 20
    if offered.category.lower() == requested.category.lower():
        score += 20
    if offered.condition == requested.condition:
        score += 10
    if offered.condition in {"new", "like-new"} and requested.condition in {"new", "like-new"}:
        score += 5

    offered_price = float(offered.price or 0)
    requested_price = float(requested.price or 0)
    if offered_price and requested_price:
        difference = abs(offered_price - requested_price) / max(offered_price, requested_price)
        if difference <= 0.10:
            score += 35
        elif difference <= 0.25:
            score += 25
        elif difference <= 0.40:
            score += 15

    score += min(10, _text_score(offered.title, requested.title))
    return min(score, 100)
