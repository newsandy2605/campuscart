# CampusCart — Full-Stack Student Marketplace

CampusCart is a campus-scoped peer-to-peer exchange application built for desktop web. It combines marketplace discovery with student-oriented transaction workflows: contact OTP, campus selection, listings, offers, Smart Swap, Wanted matching, Demand Radar, payment verification, pickup scheduling, handoff codes, reviews, reputation, notifications and moderation.

## Stack

- Next.js + TypeScript — desktop UI
- FastAPI + SQLAlchemy — application/API layer
- PostgreSQL — relational source of truth
- Redis — rate limiting, caching and session revocation
- Celery — asynchronous/background jobs
- Alembic — schema migrations
- Razorpay — payment provider adapter
- Twilio Verify / SMTP — OTP provider adapters
- Saleor — optional commerce integration boundary

## Run locally

```powershell
cd C:\Users\hp\Desktop\cc_allwire
Copy-Item .env.example .env -Force
docker compose up --build
docker compose exec backend python seed.py
curl.exe http://localhost:8100/health
curl.exe http://localhost:8100/ready
```

Open `http://localhost:3000` and API docs at `http://localhost:8100/docs`. The Compose backend runs the Alembic migration chain before Uvicorn starts.

## Authentication model

Registration accepts any valid email address or an Indian +91 phone number. The user verifies contact ownership through email OTP or phone OTP and then chooses a campus from the database. An OTP is **not** represented as proof of university enrollment. Institutional domains are optional campus-directory metadata and can be used for automatic campus detection.

## Payments

Use `PAYMENT_PROVIDER=local` for deterministic local development. To activate Razorpay, put the Key ID/Secret/Webhook Secret in backend environment variables. Only the public Key ID is exposed to the browser; server-side code verifies the order, signature, amount and captured status before marking a transaction paid.

## Testing

```powershell
cd backend
python -m pytest
```

For latency measurements against a running service:

```powershell
python scripts\benchmark_api.py --url http://localhost:8100/health --requests 100
```

See `docs/` for architecture, security, testing and recommendation-evaluation plans.

## Demo data

The seed script creates development-only users/listings for a PTU demo campus plus a local admin account. Replace all demo credentials and secrets before any deployment outside a local environment.

## UI direction

Design 3 is the application shell, Design 1 supplies marketplace/payment personality, Design 2 supplies listing-detail direction, and Move-Out Mode is intentionally absent.


## Final completeness additions

The final pass also includes admin-managed course catalogs, swap state closure across both exchanged listings, lost-and-found claim notes, production startup validation for OTP/payment providers, and executable backup/restore plus offline recommendation evaluation scripts.
