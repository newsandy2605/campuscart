from app.models import AuditLog


def record(db, actor_user_id, action, resource_type, resource_id, detail="", ip_address=""):
    db.add(AuditLog(actor_user_id=actor_user_id, action=action, resource_type=resource_type, resource_id=str(resource_id), detail=detail, ip_address=ip_address or ""))
