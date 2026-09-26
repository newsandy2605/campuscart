from datetime import datetime
import re

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.campus_models import CampusDomain
from app.config import settings
from app.db import get_db
from app.deps import current_user
from app.models import Campus, CampusMember, PickupLocation, User
from app.schemas import CampusDomainIn, CampusJoinIn
from app.security import hash_value

router = APIRouter(prefix="/api/campuses", tags=["campuses"])


def normalize_domain(domain: str) -> str:
    value = domain.strip().lower()
    value = value.removeprefix("https://").removeprefix("http://")
    value = value.split("/", 1)[0]
    if value.startswith("@"):
        value = value[1:]
    if not re.fullmatch(r"[a-z0-9.-]+\.[a-z]{2,63}", value):
        raise HTTPException(status_code=422, detail="Invalid email domain")
    return value


def campus_domains(db: Session, campus: Campus) -> list[str]:
    rows = db.scalars(
        select(CampusDomain.domain)
        .where(CampusDomain.campus_id == campus.id, CampusDomain.active.is_(True))
        .order_by(CampusDomain.domain)
    ).all()
    values = {x.lower() for x in rows if x}
    if campus.email_domain:
        values.add(campus.email_domain.lower())
    return sorted(values)


def campus_out(db: Session, campus: Campus):
    member_count = db.scalar(
        select(func.count())
        .select_from(CampusMember)
        .where(
            CampusMember.campus_id == campus.id,
            CampusMember.verified.is_(True),
        )
    ) or 0
    return {
        "id": campus.id,
        "name": campus.name,
        "slug": campus.slug,
        "city": campus.city,
        "state": campus.state,
        "pincode": campus.pincode,
        "email_domain": campus.email_domain,
        "email_domains": campus_domains(db, campus),
        "description": campus.description,
        "current_semester": campus.current_semester,
        "semester_start": campus.semester_start,
        "semester_end": campus.semester_end,
        "active": campus.active,
        "member_count": member_count,
    }


@router.get("")
def list_campuses(db: Session = Depends(get_db)):
    campuses = db.scalars(
        select(Campus).where(Campus.active.is_(True)).order_by(Campus.name)
    ).all()
    return [campus_out(db, c) for c in campuses]


@router.get("/{slug}")
def get_campus(slug: str, db: Session = Depends(get_db)):
    campus = db.scalar(
        select(Campus).where(Campus.slug == slug, Campus.active.is_(True))
    )
    if not campus:
        raise HTTPException(404, "Campus not found")
    data = campus_out(db, campus)
    pickups = db.scalars(
        select(PickupLocation).where(
            PickupLocation.campus_id == campus.id,
            PickupLocation.active.is_(True),
        )
    ).all()
    data["pickup_locations"] = [
        {
            "id": p.id,
            "name": p.name,
            "address": p.address,
            "landmark": p.landmark,
            "opening_hours": p.opening_hours,
        }
        for p in pickups
    ]
    return data


@router.get("/{slug}/membership")
def membership_status(
    slug: str,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    campus = db.scalar(select(Campus).where(Campus.slug == slug, Campus.active.is_(True)))
    if not campus:
        raise HTTPException(404, "Campus not found")
    member = db.scalar(select(CampusMember).where(CampusMember.campus_id == campus.id, CampusMember.user_id == user.id))
    return {
        "campus_slug": campus.slug,
        "campus_name": campus.name,
        "status": "approved" if member and member.verified else "pending_review" if member else "not_joined",
        "verified": bool(member and member.verified),
        "verification_method": member.verification_method if member else None,
        "verified_at": member.verified_at if member else None,
    }


@router.post("/{slug}/join")
def join_campus(
    slug: str,
    data: CampusJoinIn,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    campus = db.scalar(
        select(Campus).where(Campus.slug == slug, Campus.active.is_(True))
    )
    if not campus:
        raise HTTPException(404, "Campus not found")
    if not (user.email_verified or user.phone_verified):
        raise HTTPException(403, "Verify your email or phone with OTP before joining a campus")

    member = db.scalar(
        select(CampusMember).where(
            CampusMember.campus_id == campus.id,
            CampusMember.user_id == user.id,
        )
    )
    if member and member.verified:
        return {
            "message": "Campus already connected",
            "verified": True,
            "status": "approved",
            "verification_method": member.verification_method,
        }

    student_id = data.student_id.strip()
    stored_identity = student_id if student_id else f"contact:{user.id}:{campus.id}"
    domain_match = bool(user.email and user.email.rsplit("@", 1)[-1].lower() in set(campus_domains(db, campus)))
    mode = settings.campus_verification_mode.lower()
    verified = domain_match or mode == "development_allow_contact"
    method = "institutional_email" if domain_match else ("contact_otp_development" if verified else "admin_review")

    if member is None:
        member = CampusMember(
            campus_id=campus.id,
            user_id=user.id,
            student_id_hash=hash_value(stored_identity),
            verified=verified,
            verification_method=method,
            verified_at=datetime.utcnow() if verified else None,
        )
        db.add(member)
    else:
        member.student_id_hash = hash_value(stored_identity)
        if verified:
            member.verified = True
            member.verified_at = datetime.utcnow()
            member.verification_method = method

    db.commit()

    if not verified:
        return {
            "message": f"Your request to join {campus.name} is pending verification.",
            "verified": False,
            "status": "pending_review",
            "verification_method": "admin_review",
            "campus_slug": campus.slug,
        }

    return {
        "message": f"Connected to {campus.name}",
        "verified": True,
        "status": "approved",
        "verification_method": method,
        "campus_slug": campus.slug,
    }
