from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload
from app.models import Listing
from app.services.saleor import get_product

async def listing_output(listing: Listing):
    try:
        product = await get_product(listing.saleor_product_id)
    except Exception:
        product = None
    if not product:
        product = {
            "id": listing.saleor_product_id or f"campuscart-{listing.id}",
            "name": listing.title,
            "slug": str(listing.id),
            "thumbnail": {"url": listing.images[0].url, "alt": listing.images[0].alt} if listing.images else None,
            "pricing": {"priceRange": {"start": {"gross": {"amount": float(listing.price), "currency": "INR"}}}},
        }
    return {
        "id": listing.id,
        "campus_slug": listing.campus.slug,
        "campus_name": listing.campus.name,
        "campus_city": listing.campus.city,
        "campus_state": listing.campus.state,
        "campus_pincode": listing.campus.pincode,
        "title": listing.title,
        "saleor_product_id": listing.saleor_product_id,
        "seller_id": listing.seller_id,
        "seller": {
            "id": listing.seller.id,
            "display_name": listing.seller.display_name,
            "verified": listing.seller.verified,
            "reputation_score": listing.seller.reputation_score,
            "completed_orders": listing.seller.completed_orders,
            "response_rate": listing.seller.response_rate,
        },
        "category": listing.category,
        "subcategory": listing.subcategory,
        "condition": listing.condition,
        "listing_type": listing.listing_type,
        "price": listing.price,
        "price_override": listing.price,
        "rental_price": listing.rental_price,
        "rental_period": listing.rental_period,
        "deposit": listing.deposit,
        "description": listing.description,
        "status": listing.status,
        "pickup_area": listing.pickup_area,
        "pickup_landmark": listing.pickup_landmark,
        "pickup_instructions": listing.pickup_instructions,
        "distance_km": listing.distance_km,
        "views": listing.views,
        "favorites": listing.favorites,
        "share_count": listing.share_count,
        "created_at": listing.created_at.isoformat() if listing.created_at else "",
        "images": [{"id": x.id, "url": x.url, "alt": x.alt, "sort_order": x.sort_order} for x in sorted(listing.images, key=lambda x: x.sort_order)],
        "product": product,
    }

def get_listing(db: Session, listing_id: int):
    item = db.scalar(
        select(Listing)
        .options(joinedload(Listing.campus), joinedload(Listing.seller), selectinload(Listing.images))
        .where(Listing.id == listing_id)
    )
    if not item:
        raise HTTPException(status_code=404, detail="Listing not found")
    return item
