from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from app.db import SessionLocal
from app.services.cache import get_redis_client

router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    db_ok = True
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
    except Exception:
        db_ok = False
    return {"ok": db_ok, "service": "campuscart-api", "database": db_ok}


@router.get("/ready")
def ready():
    checks = {"database": False, "redis": False}
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
        checks["database"] = True
    except Exception:
        pass
    try:
        checks["redis"] = bool(get_redis_client().ping())
    except Exception:
        pass

    if not all(checks.values()):
        raise HTTPException(status_code=503, detail={"ready": False, **checks})
    return {"ready": True, **checks}
