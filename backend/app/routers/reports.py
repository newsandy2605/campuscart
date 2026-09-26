
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import current_user, require_admin
from app.models import Conversation, Listing, Report, User
from app.schemas import AdminResolveIn, ReportIn
from app.services.audit import record as audit_record
from app.services.rate_limit import allow_request

router = APIRouter(prefix="/api/reports", tags=["reports"])
VALID_TARGET_TYPES = {"listing", "user", "conversation"}

@router.post("")
def report(data: ReportIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if data.target_type not in VALID_TARGET_TYPES:
        raise HTTPException(422, "Unsupported report target")
    if not allow_request(f"cc:report:{user.id}", 10, 3600):
        raise HTTPException(429, "Too many reports. Please try again later")
    target = {"listing": Listing, "user": User, "conversation": Conversation}[data.target_type]
    if not db.get(target, data.target_id):
        raise HTTPException(404, "Report target not found")
    recent = db.scalar(select(Report).where(Report.reporter_id == user.id, Report.target_type == data.target_type, Report.target_id == data.target_id, Report.status == "open"))
    if recent:
        return {"id": recent.id, "status": recent.status}
    item = Report(reporter_id=user.id, **data.model_dump())
    db.add(item); db.flush()
    audit_record(db, user.id, "report.created", "report", item.id, f"{data.target_type}={data.target_id}")
    db.commit(); db.refresh(item)
    return {"id": item.id, "status": item.status}

@router.get("")
def reports(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    rows = db.scalars(select(Report).order_by(desc(Report.created_at))).all()
    return [{"id": r.id, "reporter_id": r.reporter_id, "target_type": r.target_type, "target_id": r.target_id, "reason": r.reason, "notes": r.notes, "status": r.status, "created_at": r.created_at, "resolved_at": r.resolved_at} for r in rows]

@router.post("/{report_id}/resolve")
def resolve(report_id: int, data: AdminResolveIn, user: User = Depends(require_admin), db: Session = Depends(get_db)):
    r = db.get(Report, report_id)
    if not r: raise HTTPException(404, "Report not found")
    if data.status not in {"resolved", "dismissed"}: raise HTTPException(400, "Invalid resolution")
    r.status = data.status; r.resolved_at = datetime.utcnow()
    audit_record(db, user.id, f"report.{data.status}", "report", r.id, f"{r.target_type}={r.target_id}")
    db.commit()
    return {"id": r.id, "status": r.status}
