
from celery import Celery
from sqlalchemy import select
from app.config import settings
from app.db import SessionLocal
from app.models import Campus, SellerProfile
from app.services.reputation import refresh_seller_score

celery_app = Celery("campuscart", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.beat_schedule = {
    "refresh-reputations": {"task": "campuscart.refresh_all_reputations", "schedule": 1800.0},
}

@celery_app.task(name="campuscart.refresh_all_reputations")
def refresh_all_reputations():
    with SessionLocal() as db:
        seller_ids = db.scalars(select(SellerProfile.id)).all()
        for seller_id in seller_ids:
            refresh_seller_score(db, seller_id)
    return len(seller_ids)
