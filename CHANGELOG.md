# Changelog

## 2026-09-26

### Marketplace
- Added seller photo uploads with type, size and image-signature checks.
- Added listing editing and persisted pickup instructions.
- Added sent-offer history and offer withdrawal.

### Swaps and requests
- Added incoming/outgoing swap proposals and accept/reject actions.
- Linked accepted swaps to pickup and handoff.
- Added Wanted matches and Lost & Found claim/resolution actions.
- Added course enrollment and course-tagged listings.

### Accounts and moderation
- Added password reset through the existing OTP flow.
- Added report resolution, user/membership controls and audit history to the admin area.
- Added institutional-domain/admin campus verification.

### Infrastructure
- Added S3-compatible media storage support.
- Added provider configuration checks, backups and Playwright coverage for critical journeys.
- Added request IDs, basic timing metrics and health/readiness checks.

## Earlier engineering work

- Added Alembic migrations and database integrity indexes.
- Added authorization and transaction invariant tests.
- Added payment signature checks and idempotent refund handling.
- Added the recommendation and demand-analysis scaffolding.
### 2026-09-26 — Build fix

- Fixed the frontend campus onboarding type mismatch by aligning `joinCampus` with the backend response (`status` is now typed as `approved` or `pending_review`).

