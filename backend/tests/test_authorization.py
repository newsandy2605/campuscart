from fastapi import HTTPException
from app.deps import require_admin
from app.models import User

def test_non_admin_is_rejected():
    user = User(id=1, role="student")
    try:
        require_admin(user)
    except HTTPException as exc:
        assert exc.status_code == 403
    else:
        raise AssertionError("student should not pass admin guard")

def test_admin_passes_admin_guard():
    user = User(id=1, role="admin")
    assert require_admin(user) is user
