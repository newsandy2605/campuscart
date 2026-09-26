# CampusCart — final completeness pass

This archive contains the comprehensive implementation pass requested on 2026-09-26. Existing application features were retained; the pass closes previously identified backend/frontend gaps and adds production/test scaffolding.

## Included

- Native laptop image selection and upload for seller listings, up to six validated images per listing.
- Local persisted media storage for development plus S3-compatible storage for deployment.
- Listing editing, photo deletion, pickup instructions, and course tagging.
- Buyer offer history/withdrawal and seller offer management.
- Smart Swap inbox/sent/accept/reject flow with transaction tracking.
- Swap transaction completion/cancellation now updates both exchanged listings.
- Wanted matching with direct seller messaging from a matched listing.
- Lost & Found claims, claim notes, confirmation, rejection and resolution with audit events.
- Course discovery/enrollment, course-tagged marketplace inventory, and admin course creation.
- Campus verification modes (`domain_or_admin`, `admin_only`, development-only contact mode), campus domain management and verification review.
- Admin user management, listing moderation, report resolution and audit history.
- Password reset via OTP/reset token flow already exposed through the UI.
- Production validation for JWT/Handoff secrets, SMTP OTP, Twilio (when enabled), Razorpay, S3 and CORS.
- Razorpay/Twilio/SMTP provider contract tests.
- PostgreSQL backup/restore scripts.
- Offline recommendation-event export/evaluation with real-data-only metrics.
- Playwright public smoke tests plus authenticated critical-flow tests.
- Security headers, rate limits and Sentry integration remain enabled where configured.

## Secrets

No real OTP, Razorpay, Twilio, S3, SMTP or Sentry credentials are included. Environment templates contain placeholders. Replace them outside source control before production deployment.

## VS Code terminal checks

From the project root:

```powershell
python -m compileall -q backend/app backend/tests scripts

cd backend
python -m pytest
cd ..

cd frontend
npm install
npx playwright install chromium
npm run build
npm run test:e2e
```

For the authenticated Playwright flow, set `E2E_SELLER_EMAIL`, `E2E_SELLER_PASSWORD`, `E2E_BUYER_EMAIL`, `E2E_BUYER_PASSWORD`, and optionally `E2E_ADMIN_EMAIL`, `E2E_ADMIN_PASSWORD` before `npm run test:e2e`.

## Local Docker

```powershell
docker compose up --build
```

The backend starts Alembic migrations automatically. Local development uses the local payment adapter and development OTP echo unless overridden. Production must set `APP_ENV=production`, disable `DEV_OTP_ECHO`, and provide the required provider credentials described in `docs/PRODUCTION_RUNBOOK.md`.

## Verification performed in the build workspace

- Python compilation: passed.
- Alembic revision chain: passed; head is `d7b7e1c6d1f7`.
- Frontend TypeScript syntax/transpile audit: passed.
- Frontend internal API import/export audit: passed.
- Secret-pattern scan: passed.
- Original archive comparison: no functional/source files removed.

A full `pytest` run and Next.js production build were not executable in the packaging workspace because the runtime lacked the project dependencies `psycopg`, `redis` and `celery`, and Docker was unavailable. The repository dependency manifests are updated for those packages; run the commands above in VS Code after installing dependencies.
