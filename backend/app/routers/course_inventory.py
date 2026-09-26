from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.db import get_db
from app.deps import current_user, require_verified_member
from app.models import Campus, Course, Listing, ListingCourse, SellerProfile, StudentCourse, User

router = APIRouter(prefix="/api/course-inventory", tags=["course-inventory"])


@router.get("/mine")
def my_courses(user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.execute(
        select(Course, Campus.slug)
        .join(StudentCourse, StudentCourse.course_id == Course.id)
        .join(Campus, Campus.id == Course.campus_id)
        .where(StudentCourse.user_id == user.id)
        .order_by(Course.semester, Course.code)
    ).all()
    return [
        {"id": course.id, "code": course.code, "name": course.name, "semester": course.semester, "campus_slug": slug}
        for course, slug in rows
    ]


@router.get("/listing/{listing_id}/courses")
def listing_courses(listing_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    listing = db.get(Listing, listing_id)
    if not listing or listing.seller.user_id != user.id:
        raise HTTPException(404, "Listing not found")
    rows = db.scalars(select(Course).join(ListingCourse, ListingCourse.course_id == Course.id).where(ListingCourse.listing_id == listing_id).order_by(Course.semester, Course.code)).all()
    return [{"id": c.id, "code": c.code, "name": c.name, "semester": c.semester, "campus_slug": c.campus.slug} for c in rows]


@router.get("/course/{course_id}/listings")
async def course_listings(course_id: int, db: Session = Depends(get_db)):
    from app.services.listings import listing_output

    course = db.get(Course, course_id)
    if not course:
        raise HTTPException(404, "Course not found")
    rows = db.scalars(
        select(Listing).options(joinedload(Listing.campus), joinedload(Listing.seller), selectinload(Listing.images))
        .join(ListingCourse, ListingCourse.listing_id == Listing.id)
        .where(ListingCourse.course_id == course_id, Listing.status == "active")
        .order_by(Listing.created_at.desc())
    ).all()
    return [await listing_output(item) for item in rows]


@router.post("/listing/{listing_id}/course/{course_id}")
def attach_listing_course(
    listing_id: int,
    course_id: int,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    listing = db.get(Listing, listing_id)
    course = db.get(Course, course_id)
    if not listing or not course:
        raise HTTPException(404, "Listing or course not found")
    if listing.campus_id != course.campus_id:
        raise HTTPException(400, "Listing and course must belong to the same campus")
    require_verified_member(course.campus.slug, user, db)
    if listing.seller.user_id != user.id:
        raise HTTPException(403, "Only the seller can tag a listing to a course")
    exists = db.scalar(
        select(ListingCourse).where(
            ListingCourse.listing_id == listing_id,
            ListingCourse.course_id == course_id,
        )
    )
    if not exists:
        db.add(ListingCourse(listing_id=listing_id, course_id=course_id))
        db.commit()
    return {"listing_id": listing_id, "course_id": course_id, "attached": True}


@router.delete("/listing/{listing_id}/course/{course_id}")
def detach_listing_course(
    listing_id: int,
    course_id: int,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    listing = db.get(Listing, listing_id)
    if not listing or listing.seller.user_id != user.id:
        raise HTTPException(404, "Listing not found")
    row = db.scalar(
        select(ListingCourse).where(
            ListingCourse.listing_id == listing_id,
            ListingCourse.course_id == course_id,
        )
    )
    if row:
        db.delete(row)
        db.commit()
    return {"listing_id": listing_id, "course_id": course_id, "attached": False}
