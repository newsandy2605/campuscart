from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, func, or_, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.db import get_db
from app.deps import current_user, optional_user, require_verified_member
from app.models import Address, Campus, CampusMember, Course, Favorite, InteractionEvent, Listing, ListingCourse, ListingImage, PickupLocation, User
from app.schemas import ListingCreateIn, ListingImageIn, ListingUpdateIn
from app.services.listings import get_listing, listing_output
from app.services.matching import refresh_wanted_matches_for_listing
from app.services.storage import delete_media_url
from app.services.notifications import create_notification

router = APIRouter(prefix="/api", tags=["listings"])


def _validate_pickup_inputs(data, user: User, campus: Campus, db: Session):
    if data.pickup_location_id:
        location = db.get(PickupLocation, data.pickup_location_id)
        if not location or not location.active or location.campus_id != campus.id:
            raise HTTPException(400, "Pickup location is invalid for this campus")
    if data.pickup_address_id:
        address = db.get(Address, data.pickup_address_id)
        if not address or address.user_id != user.id:
            raise HTTPException(403, "Pickup address is not available to this user")


def _sync_listing_courses(db: Session, listing: Listing, course_ids: list[int]) -> None:
    if not course_ids:
        return
    unique_ids = sorted(set(course_ids))
    courses = db.scalars(select(Course).where(Course.id.in_(unique_ids), Course.campus_id == listing.campus_id)).all()
    if len(courses) != len(unique_ids):
        raise HTTPException(400, "One or more selected courses do not belong to this campus")
    existing = {x.course_id for x in db.scalars(select(ListingCourse).where(ListingCourse.listing_id == listing.id)).all()}
    for course in courses:
        if course.id not in existing:
            db.add(ListingCourse(listing_id=listing.id, course_id=course.id))



@router.get("/marketplace")
async def marketplace(
    campus_slug: str,
    search: str = "",
    category: str = "",
    condition: str = "",
    listing_type: str = "",
    min_price: Decimal | None = None,
    max_price: Decimal | None = None,
    sort: str = "recommended",
    user: User | None = Depends(optional_user),
    db: Session = Depends(get_db),
):
    campus = db.scalar(select(Campus).where(Campus.slug == campus_slug, Campus.active.is_(True)))
    if not campus:
        raise HTTPException(404, "Campus not found")

    q = select(Listing).options(
        joinedload(Listing.campus),
        joinedload(Listing.seller),
        selectinload(Listing.images),
    ).where(Listing.campus_id == campus.id, Listing.status == "active")

    if search:
        needle = f"%{search.strip()}%"
        q = q.where(or_(
            Listing.title.ilike(needle),
            Listing.description.ilike(needle),
            Listing.category.ilike(needle),
        ))
    if category:
        q = q.where(Listing.category == category)
    if condition:
        q = q.where(Listing.condition == condition)
    if listing_type:
        q = q.where(Listing.listing_type == listing_type)
    if min_price is not None:
        q = q.where(Listing.price >= min_price)
    if max_price is not None:
        q = q.where(Listing.price <= max_price)

    if sort == "newest":
        q = q.order_by(desc(Listing.created_at))
    elif sort == "price_low":
        q = q.order_by(Listing.price.asc())
    elif sort == "price_high":
        q = q.order_by(Listing.price.desc())
    elif sort == "closest":
        q = q.order_by(Listing.distance_km.asc().nullslast())
    else:
        q = q.order_by(desc(Listing.favorites), desc(Listing.views), desc(Listing.created_at))

    items = db.scalars(q.limit(60)).all()
    outputs = []
    for item in items:
        outputs.append(await listing_output(item))
        if user:
            db.add(InteractionEvent(
                user_id=user.id,
                campus_id=campus.id,
                listing_id=item.id,
                event_type="view",
                category=item.category,
            ))
    if user:
        db.commit()
    return outputs


@router.post("/listings")
async def create_listing(data: ListingCreateIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    campus, _ = require_verified_member(data.campus_slug, user, db)
    if not user.seller_profile:
        raise HTTPException(403, "Create a seller profile first")
    _validate_pickup_inputs(data, user, campus, db)

    seller = user.seller_profile
    listing = Listing(
        campus_id=campus.id,
        seller_id=seller.id,
        **{k: v for k, v in data.model_dump().items() if k not in {"images", "course_ids"}},
    )
    db.add(listing)
    db.flush()

    for image in data.images:
        db.add(ListingImage(listing_id=listing.id, **image.model_dump()))
    _sync_listing_courses(db, listing, data.course_ids)

    refresh_wanted_matches_for_listing(db, listing)
    db.commit()
    db.refresh(listing)
    return await listing_output(get_listing(db, listing.id))


@router.get("/listings/{listing_id}")
async def detail(listing_id: int, user: User | None = Depends(optional_user), db: Session = Depends(get_db)):
    listing = get_listing(db, listing_id)
    listing.views += 1
    if user:
        db.add(InteractionEvent(
            user_id=user.id,
            campus_id=listing.campus_id,
            listing_id=listing.id,
            event_type="view",
            category=listing.category,
        ))
    db.commit()
    return await listing_output(listing)


@router.patch("/listings/{listing_id}")
async def update_listing(listing_id: int, data: ListingUpdateIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    listing = get_listing(db, listing_id)
    if listing.seller.user_id != user.id:
        raise HTTPException(403, "Only the seller can edit this listing")
    if listing.status not in {"draft", "active"}:
        raise HTTPException(409, "Only draft or active listings can be edited")

    if data.pickup_location_id:
        location = db.get(PickupLocation, data.pickup_location_id)
        if not location or not location.active or location.campus_id != listing.campus_id:
            raise HTTPException(400, "Pickup location is invalid for this campus")
    if data.pickup_address_id:
        address = db.get(Address, data.pickup_address_id)
        if not address or address.user_id != user.id:
            raise HTTPException(403, "Pickup address is not available to this user")

    changes = data.model_dump(exclude_unset=True)
    course_ids = changes.pop("course_ids", None)
    for key, value in changes.items():
        setattr(listing, key, value)
    if course_ids is not None:
        db.query(ListingCourse).filter(ListingCourse.listing_id == listing.id).delete(synchronize_session=False)
        _sync_listing_courses(db, listing, course_ids)

    refresh_wanted_matches_for_listing(db, listing)
    db.commit()
    return await listing_output(get_listing(db, listing_id))


@router.post("/listings/{listing_id}/images")
def attach_listing_image(listing_id: int, data: ListingImageIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    listing = get_listing(db, listing_id)
    if listing.seller.user_id != user.id:
        raise HTTPException(403, "Only the seller can add listing photos")
    if listing.status not in {"draft", "active"}:
        raise HTTPException(409, "Photos cannot be changed after the listing is reserved")
    if len(listing.images) >= 6:
        raise HTTPException(409, "A listing can have at most 6 photos")
    image = ListingImage(listing_id=listing.id, url=data.url, alt=data.alt, sort_order=data.sort_order)
    db.add(image); db.commit(); db.refresh(image)
    return {"id": image.id, "listing_id": listing.id, "url": image.url, "alt": image.alt, "sort_order": image.sort_order}


@router.delete("/listings/{listing_id}/images/{image_id}")
def delete_listing_image(listing_id: int, image_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    listing = get_listing(db, listing_id)
    if listing.seller.user_id != user.id:
        raise HTTPException(403, "Only the seller can delete listing photos")
    if listing.status not in {"draft", "active"}:
        raise HTTPException(409, "Photos cannot be changed after the listing is reserved")
    image = db.get(ListingImage, image_id)
    if not image or image.listing_id != listing.id:
        raise HTTPException(404, "Listing image not found")
    if len(listing.images) <= 1:
        raise HTTPException(409, "A listing must keep at least one photo")
    url = image.url
    db.delete(image); db.commit(); delete_media_url(url)
    return {"ok": True}


@router.delete("/listings/{listing_id}")
def delete_listing(listing_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    listing = get_listing(db, listing_id)
    if listing.seller.user_id != user.id:
        raise HTTPException(403, "Only the seller can remove this listing")
    if listing.status == "reserved":
        raise HTTPException(409, "Reserved listing cannot be removed")
    listing.status = "removed"
    db.commit()
    return {"ok": True, "status": listing.status}


@router.post("/listings/{listing_id}/favorite")
def favorite_listing(listing_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    listing = get_listing(db, listing_id)
    if listing.seller.user_id == user.id:
        raise HTTPException(400, "You cannot favorite your own listing")

    existing = db.scalar(select(Favorite).where(
        Favorite.user_id == user.id,
        Favorite.listing_id == listing_id,
    ))
    if existing:
        db.delete(existing)
        listing.favorites = max(0, listing.favorites - 1)
        action = False
        event = "unfavorite"
    else:
        db.add(Favorite(user_id=user.id, listing_id=listing_id))
        listing.favorites += 1
        action = True
        event = "favorite"

    db.add(InteractionEvent(
        user_id=user.id,
        campus_id=listing.campus_id,
        listing_id=listing.id,
        event_type=event,
        category=listing.category,
    ))
    db.commit()
    return {"favorite": action, "favorites": listing.favorites}


@router.get("/listings/{listing_id}/favorite")
def favorite_status(listing_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    exists = db.scalar(select(Favorite.id).where(
        Favorite.user_id == user.id,
        Favorite.listing_id == listing_id,
    ))
    return {"favorite": exists is not None}


@router.post("/listings/{listing_id}/share")
def share_listing(listing_id: int, user: User | None = Depends(optional_user), db: Session = Depends(get_db)):
    listing = get_listing(db, listing_id)
    listing.share_count += 1
    if user:
        db.add(InteractionEvent(
            user_id=user.id,
            campus_id=listing.campus_id,
            listing_id=listing.id,
            event_type="share",
            category=listing.category,
        ))
    db.commit()
    return {
        "share_count": listing.share_count,
        "whatsapp_url": f"https://wa.me/?text=CampusCart%20listing%20{listing.id}",
    }
