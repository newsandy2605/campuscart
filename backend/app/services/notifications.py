from datetime import datetime
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.models import Notification

def create_notification(db: Session, user_id: int, kind: str, title: str, body: str = "", link: str = ""):
    item = Notification(user_id=user_id, kind=kind, title=title, body=body, link=link)
    db.add(item)
    db.flush()
    return item

def unread_count(db: Session, user_id: int) -> int:
    return db.scalar(select(func.count()).select_from(Notification).where(Notification.user_id == user_id, Notification.read_at.is_(None))) or 0
