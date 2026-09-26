from datetime import datetime
import re

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.campus_models import CampusDomain
from app.db import get_db
from app.deps import require_admin
from app.models import Course, AuditLog, Campus, CampusMember, Listing, Report, Transaction, User
from app.services.audit import record as audit_record
from app.schemas import CampusCreateIn, CampusDomainIn, CampusUpdateIn, AdminUserStatusIn, CourseCreateIn

router = APIRouter(prefix="/api/admin", tags=["admin"])


def normalize_domain(domain: str) -> str:
    value = domain.strip().lower().removeprefix("https://").removeprefix("http://").split("/", 1)[0]
    value = value[1:] if value.startswith("@") else value
    if not re.fullmatch(r"[a-z0-9.-]+\.[a-z]{2,63}", value):
        raise HTTPException(422, f"Invalid email domain: {domain}")
    return value


def domains_for(db: Session, campus: Campus):
    rows = db.scalars(select(CampusDomain).where(CampusDomain.campus_id == campus.id).order_by(CampusDomain.domain)).all()
    values = {campus.email_domain.lower()} if campus.email_domain else set()
    values.update(r.domain for r in rows if r.active)
    return sorted(values)


def campus_admin_out(db: Session, campus: Campus):
    members = db.scalar(select(func.count()).select_from(CampusMember).where(CampusMember.campus_id == campus.id)) or 0
    verified = db.scalar(select(func.count()).select_from(CampusMember).where(CampusMember.campus_id == campus.id, CampusMember.verified.is_(True))) or 0
    pending = db.scalar(select(func.count()).select_from(CampusMember).where(CampusMember.campus_id == campus.id, CampusMember.verified.is_(False))) or 0
    return {"id": campus.id, "name": campus.name, "slug": campus.slug, "city": campus.city, "state": campus.state, "pincode": campus.pincode,
            "email_domains": domains_for(db, campus), "description": campus.description, "current_semester": campus.current_semester,
            "active": campus.active, "member_count": members, "verified_member_count": verified, "pending_member_count": pending}


@router.get("/overview")
def overview(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    return {"users": db.scalar(select(func.count()).select_from(User)) or 0, "active_users": db.scalar(select(func.count()).select_from(User).where(User.active.is_(True))) or 0,
            "campuses": db.scalar(select(func.count()).select_from(Campus)) or 0,
            "active_listings": db.scalar(select(func.count()).select_from(Listing).where(Listing.status == "active")) or 0,
            "transactions": db.scalar(select(func.count()).select_from(Transaction)) or 0,
            "open_reports": db.scalar(select(func.count()).select_from(Report).where(Report.status == "open")) or 0,
            "pending_verifications": db.scalar(select(func.count()).select_from(CampusMember).where(CampusMember.verified.is_(False))) or 0}


@router.get("/campuses")
def admin_list_campuses(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    return [campus_admin_out(db, c) for c in db.scalars(select(Campus).order_by(Campus.name)).all()]


@router.post("/campuses")
def create_campus(data: CampusCreateIn, user: User = Depends(require_admin), db: Session = Depends(get_db)):
    slug = data.slug.strip().lower()
    if db.scalar(select(Campus).where(Campus.slug == slug)):
        raise HTTPException(409, "Campus slug already exists")
    normalized = []
    for raw in data.email_domains:
        domain = normalize_domain(raw)
        if domain not in normalized:
            normalized.append(domain)
    campus = Campus(name=data.name.strip(), slug=slug, city=data.city.strip(), state=data.state.strip(), pincode=data.pincode.strip(),
                    email_domain=normalized[0] if normalized else "", description=data.description.strip(), current_semester=data.current_semester.strip() or "Current semester")
    db.add(campus); db.flush()
    for domain in normalized:
        db.add(CampusDomain(campus_id=campus.id, domain=domain, active=True))
    audit_record(db, user.id, "campus.created", "campus", campus.id, f"slug={campus.slug};domains={','.join(normalized)}")
    db.commit(); db.refresh(campus)
    return campus_admin_out(db, campus)


@router.patch("/campuses/{campus_id}")
def update_campus(campus_id: int, data: CampusUpdateIn, user: User = Depends(require_admin), db: Session = Depends(get_db)):
    campus = db.get(Campus, campus_id)
    if not campus: raise HTTPException(404, "Campus not found")
    changes = data.model_dump(exclude_unset=True)
    if "slug" in changes:
        changes["slug"] = changes["slug"].strip().lower()
        if db.scalar(select(Campus).where(Campus.slug == changes["slug"], Campus.id != campus.id)):
            raise HTTPException(409, "Campus slug already exists")
    for key, value in changes.items(): setattr(campus, key, value.strip() if isinstance(value, str) else value)
    audit_record(db, user.id, "campus.updated", "campus", campus.id, ",".join(sorted(changes)))
    db.commit(); db.refresh(campus)
    return campus_admin_out(db, campus)


@router.post("/campuses/{campus_id}/domains")
def add_campus_domain(campus_id: int, data: CampusDomainIn, user: User = Depends(require_admin), db: Session = Depends(get_db)):
    campus = db.get(Campus, campus_id)
    if not campus: raise HTTPException(404, "Campus not found")
    domain = normalize_domain(data.domain)
    existing = db.scalar(select(CampusDomain).where(CampusDomain.campus_id == campus_id, CampusDomain.domain == domain))
    if existing: existing.active = True
    else: db.add(CampusDomain(campus_id=campus_id, domain=domain, active=True))
    if not campus.email_domain: campus.email_domain = domain
    audit_record(db, user.id, "campus.domain_added", "campus", campus.id, domain)
    db.commit()
    return {"ok": True, "domain": domain, "email_domains": domains_for(db, campus)}


@router.delete("/campuses/{campus_id}/domains/{domain_id}")
def deactivate_campus_domain(campus_id: int, domain_id: int, user: User = Depends(require_admin), db: Session = Depends(get_db)):
    domain = db.scalar(select(CampusDomain).where(CampusDomain.id == domain_id, CampusDomain.campus_id == campus_id))
    if not domain: raise HTTPException(404, "Campus domain not found")
    domain.active = False
    audit_record(db, user.id, "campus.domain_deactivated", "campus_domain", domain.id, str(domain.id))
    db.commit()
    return {"ok": True}


@router.get("/courses")
def admin_courses(campus_id: int | None = None, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    q = select(Course).order_by(Course.campus_id, Course.semester, Course.code)
    if campus_id:
        q = q.where(Course.campus_id == campus_id)
    rows = db.scalars(q).all()
    return [{"id": c.id, "campus_id": c.campus_id, "code": c.code, "name": c.name, "semester": c.semester} for c in rows]

@router.post("/campuses/{campus_id}/courses")
def admin_create_course(campus_id: int, data: CourseCreateIn, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    campus = db.get(Campus, campus_id)
    if not campus:
        raise HTTPException(404, "Campus not found")
    code = data.code.strip().upper()
    exists = db.scalar(select(Course).where(Course.campus_id == campus_id, Course.code == code))
    if exists:
        raise HTTPException(409, "Course code already exists for this campus")
    course = Course(campus_id=campus_id, code=code, name=data.name.strip(), semester=data.semester.strip())
    db.add(course); db.flush()
    audit_record(db, _.id, "course.created", "course", course.id, f"campus={campus_id}")
    db.commit(); db.refresh(course)
    return {"id": course.id, "campus_id": course.campus_id, "code": course.code, "name": course.name, "semester": course.semester}

@router.get("/campus-members")
def pending_members(campus_id: int | None = None, pending_only: bool = True, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    q = select(CampusMember, User, Campus).join(User, User.id == CampusMember.user_id).join(Campus, Campus.id == CampusMember.campus_id)
    if campus_id: q = q.where(CampusMember.campus_id == campus_id)
    if pending_only: q = q.where(CampusMember.verified.is_(False))
    rows = db.execute(q.order_by(CampusMember.joined_at.desc())).all()
    return [{"id": m.id, "user_id": u.id, "name": u.name, "email": u.email, "phone": u.phone, "campus_id": c.id, "campus_name": c.name,
             "verification_method": m.verification_method, "verified": m.verified, "joined_at": m.joined_at, "verified_at": m.verified_at} for m,u,c in rows]


@router.post("/campus-members/{member_id}/approve")
def approve_member(member_id: int, user: User = Depends(require_admin), db: Session = Depends(get_db)):
    member = db.get(CampusMember, member_id)
    if not member: raise HTTPException(404, "Campus membership not found")
    member.verified = True; member.verified_at = datetime.utcnow(); member.verification_method = "admin_review"
    audit_record(db, user.id, "campus_member.approved", "campus_member", member.id, f"user={member.user_id};campus={member.campus_id}")
    db.commit()
    return {"id": member.id, "status": "approved", "verified": True}


@router.post("/campus-members/{member_id}/revoke")
def revoke_member(member_id: int, user: User = Depends(require_admin), db: Session = Depends(get_db)):
    member = db.get(CampusMember, member_id)
    if not member: raise HTTPException(404, "Campus membership not found")
    member.verified = False; member.verified_at = None; member.verification_method = "admin_review"
    audit_record(db, user.id, "campus_member.revoked", "campus_member", member.id, f"user={member.user_id};campus={member.campus_id}")
    db.commit()
    return {"id": member.id, "status": "pending_review", "verified": False}


@router.get("/users")
def admin_users(q: str = Query(default=""), active: bool | None = None, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    query = select(User)
    if q.strip():
        needle = f"%{q.strip().lower()}%"
        query = query.where(or_(func.lower(User.name).like(needle), func.lower(User.email).like(needle), func.lower(func.coalesce(User.phone, "")).like(needle)))
    if active is not None: query = query.where(User.active.is_(active))
    rows = db.scalars(query.order_by(User.created_at.desc()).limit(100)).all()
    return [{"id": u.id, "name": u.name, "email": u.email, "phone": u.phone, "role": u.role, "active": u.active, "email_verified": u.email_verified, "phone_verified": u.phone_verified, "created_at": u.created_at} for u in rows]


@router.patch("/users/{user_id}")
def set_user_status(user_id: int, data: AdminUserStatusIn, user: User = Depends(require_admin), db: Session = Depends(get_db)):
    target = db.get(User, user_id)
    if not target: raise HTTPException(404, "User not found")
    if target.id == user.id and not data.active: raise HTTPException(400, "You cannot deactivate your own admin account")
    target.active = data.active
    audit_record(db, user.id, "user.activated" if data.active else "user.deactivated", "user", target.id, target.name)
    db.commit()
    return {"ok": True, "active": target.active}


@router.get("/transactions")
def admin_transactions(q: str = Query(default=""), _: User = Depends(require_admin), db: Session = Depends(get_db)):
    query = select(Transaction, Listing.title, User.name.label("buyer_name"), User.email.label("buyer_email")).join(Listing, Listing.id == Transaction.listing_id).join(User, User.id == Transaction.buyer_id)
    if q.strip().isdigit(): query = query.where(Transaction.id == int(q))
    elif q.strip(): query = query.where(func.lower(Listing.title).like(f"%{q.strip().lower()}%"))
    rows = db.execute(query.order_by(Transaction.created_at.desc()).limit(100)).all()
    return [{"id": tx.id, "listing_id": tx.listing_id, "listing_title": title, "buyer_name": name, "buyer_email": email, "seller_id": tx.seller_id, "agreed_price": tx.agreed_price, "status": tx.status, "created_at": tx.created_at, "paid_at": tx.paid_at, "completed_at": tx.completed_at} for tx,title,name,email in rows]


@router.get("/listings")
def admin_listings(q: str = Query(default=""), _: User = Depends(require_admin), db: Session = Depends(get_db)):
    query = select(Listing, User.name.label("seller_name"), Campus.name.label("campus_name")).join(User, User.id == Listing.seller_id).join(Campus, Campus.id == Listing.campus_id)
    if q.strip():
        needle = f"%{q.strip().lower()}%"
        query = query.where(or_(func.lower(Listing.title).like(needle), func.lower(User.name).like(needle), func.lower(Campus.name).like(needle)))
    rows = db.execute(query.order_by(Listing.created_at.desc()).limit(100)).all()
    return [{"id": l.id, "title": l.title, "seller_name": seller_name, "campus_name": campus_name, "price": l.price, "status": l.status, "created_at": l.created_at} for l,seller_name,campus_name in rows]


@router.get("/audit-logs")
def audit_logs(q: str = Query(default=""), _: User = Depends(require_admin), db: Session = Depends(get_db)):
    query = select(AuditLog)
    if q.strip():
        needle = f"%{q.strip().lower()}%"
        query = query.where(or_(func.lower(AuditLog.action).like(needle), func.lower(AuditLog.resource_type).like(needle), func.lower(AuditLog.resource_id).like(needle), func.lower(AuditLog.detail).like(needle)))
    rows = db.scalars(query.order_by(AuditLog.created_at.desc()).limit(100)).all()
    return [{"id": x.id, "actor_user_id": x.actor_user_id, "action": x.action, "resource_type": x.resource_type, "resource_id": x.resource_id, "detail": x.detail, "ip_address": x.ip_address, "created_at": x.created_at} for x in rows]


@router.post("/listings/{listing_id}/remove")
def moderate_listing(listing_id: int, user: User = Depends(require_admin), db: Session = Depends(get_db)):
    listing = db.get(Listing, listing_id)
    if not listing: raise HTTPException(404, "Listing not found")
    listing.status = "removed"
    audit_record(db, user.id, "listing.removed_by_admin", "listing", listing.id, listing.title)
    db.commit()
    return {"ok": True, "status": listing.status}


@router.post("/deactivate-user/{user_id}")
def deactivate_legacy(user_id: int, user: User = Depends(require_admin), db: Session = Depends(get_db)):
    target = db.get(User, user_id)
    if not target: return {"ok": False, "message": "User not found"}
    target.active = False
    audit_record(db, user.id, "user.deactivated", "user", target.id, target.name)
    db.commit()
    return {"ok": True}
