# Production runbook

This checklist assumes the application is deployed as separate web, API, worker, PostgreSQL and Redis services. Keep provider credentials in the platform's secret store or environment-variable manager.

## Application secrets

Generate separate random values for `JWT_SECRET` and `HANDOFF_SECRET`. Do not reuse the same secret.

## Database and Redis

Provision managed PostgreSQL and Redis. Set `DATABASE_URL` and `REDIS_URL` for both the API and worker services. Run Alembic migrations before serving traffic.

## Email and SMS

For email OTP, configure the SMTP host, port, sender and password. For SMS, set `SMS_PROVIDER=twilio` and provide the Twilio Verify credentials. Keep `DEV_OTP_ECHO=false` in production.

## Payments

Start with Razorpay test credentials and a signed webhook endpoint. Test successful payment, failed payment, duplicate delivery, invalid signatures and refunds. Switch to live credentials only after those cases work.

## Media

Use `STORAGE_PROVIDER=s3` with an S3-compatible bucket and a public media base URL. Local filesystem storage is intended for development or a single machine.

## Campus verification

Choose either institutional-domain verification, admin review, or both. Do not describe contact OTP as proof of student status.

## Monitoring and operations

Set `SENTRY_DSN` for application errors. Keep `/health` and `/ready` available to the platform health checks. Back up PostgreSQL and test restores against a disposable database.

## Final deployment check

Before exposing the application to users:

1. Run backend tests.
2. Build the frontend.
3. Run Playwright against the deployed environment.
4. Upload and retrieve a real listing photo.
5. Complete a Razorpay test payment and webhook.
6. Verify OTP delivery.
7. Check moderation and audit logging.
8. Complete a purchase and a swap through pickup and handoff.
9. Restore a PostgreSQL backup into a disposable database.
