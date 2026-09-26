
import os
from fastapi.testclient import TestClient
os.environ["DATABASE_URL"] = os.environ.get("DATABASE_URL", "sqlite:///./smoke.db")
os.environ["DEV_OTP_ECHO"] = "true"
# This import happens after the DB env is set.
from app.main import app

def main():
    client = TestClient(app)
    r = client.get("/health")
    assert r.status_code == 200, r.text
    r = client.get("/api/campuses")
    assert r.status_code == 200, r.text
    print("Smoke test passed:", r.json())

if __name__ == "__main__":
    main()
