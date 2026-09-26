# CampusCart

CampusCart is a campus-scoped marketplace for students who want to buy, sell, or swap used items locally. Listings, offers, messaging, pickup scheduling, handoff and reviews are kept in one application so the transaction does not have to move between separate tools.

## Stack

- Next.js + TypeScript
- FastAPI + SQLAlchemy
- PostgreSQL + Alembic
- Redis + Celery
- Razorpay (optional payment provider)
- Twilio Verify / SMTP (optional OTP providers)
- S3-compatible object storage (optional media provider)

## Run locally

From the repository root:

```powershell
Copy-Item .env.example .env -Force
docker compose up --build
docker compose exec backend python seed.py
```

Open `http://localhost:3000`. The API is available at `http://localhost:8100`; `/docs` exposes the FastAPI development documentation.

For local development, keep `DEV_OTP_ECHO=true` and `PAYMENT_PROVIDER=local`. Real provider credentials are only needed when testing those integrations.

## Tests

Backend:

```powershell
cd backend
python -m pytest
```

Frontend/browser tests:

```powershell
cd frontend
npm install
npx playwright install chromium
npm run test:e2e
```

## Project docs

- [`docs/PROJECT_OVERVIEW.md`](docs/PROJECT_OVERVIEW.md) — product and technical overview
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — system boundaries and state rules
- [`docs/ENGINEERING_DECISIONS.md`](docs/ENGINEERING_DECISIONS.md) — decisions and trade-offs
- [`docs/SECURITY_MODEL.md`](docs/SECURITY_MODEL.md) — authentication, authorization and provider security
- [`docs/TESTING.md`](docs/TESTING.md) — test strategy and useful commands
- [`docs/PRODUCTION_RUNBOOK.md`](docs/PRODUCTION_RUNBOOK.md) — deployment checklist
- [`docs/KNOWN_LIMITATIONS.md`](docs/KNOWN_LIMITATIONS.md) — current constraints

## Development data

`backend/seed.py` creates a small local dataset so the application can be explored without external services. Seed credentials are development-only and must not be reused for deployment.
