# CampusCart — System Architecture

CampusCart is a campus-scoped peer-to-peer marketplace. The application owns identity, campus membership, marketplace state, offers, swaps, pickup, handoff, reviews and moderation. External services handle only provider-specific work.

```text
Next.js
  |
  v
FastAPI
  |------ PostgreSQL
  |------ Redis
  |------ Worker
  |          |
  |          +---- notifications / background jobs
  |
  +------ SMTP / Twilio Verify
  +------ Razorpay
  +------ S3-compatible media storage
```

## Core invariants

- A seller cannot buy or make an offer on their own listing.
- Ownership is checked on the API, not only in the browser.
- Contact OTP verifies contact ownership and is not treated as university enrollment proof.
- Public listing data does not expose a seller's private pickup address.
- Payment status is updated only after server-side provider validation.
- A normal transaction cannot skip required payment or pickup states.
- Handoff is completed only after the required participant confirmations are recorded.
- Accepted swaps keep the two exchanged listings synchronized through completion/cancellation.

## Reliability boundaries

Provider calls live in `backend/app/services/`. Readiness checks cover PostgreSQL and Redis. Requests carry a request ID, and the application records basic timing information for troubleshooting.
