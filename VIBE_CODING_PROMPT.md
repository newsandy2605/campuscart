# Vibe-coding brief — CampusCart

Use this repository as the source of truth. Do not generate a parallel project or duplicate folders. Preserve the desktop-only design language: Design 3 app shell, Design 1 marketplace/payment personality, Design 2 listing detail. Move-Out Mode is intentionally absent.

Engineering priorities:
1. Preserve server-side authorization and transaction invariants.
2. Never expose Razorpay secrets, SMTP passwords or Twilio Auth Tokens to the browser.
3. Use Alembic for all future database changes.
4. Keep contact OTP separate from campus membership semantics.
5. Add/extend automated tests for every new state transition.
6. Keep provider integrations behind service adapters so local mode remains deterministic.
7. Validate with `python -m pytest`, `npm run build`, `/health` and `/ready`.
8. Prefer small, explicit changes over rewrites.
