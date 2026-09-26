# CampusCart — Security model

## Authentication

Passwords are salted and hashed. Access tokens are signed JWTs and can be revoked through Redis. OTP challenges are hashed, expire after a short period, have an attempt limit, and are invalidated when a new challenge is issued for the same destination and purpose.

## Abuse controls

Registration, login, OTP, messaging and offers use Redis-backed rate limits. Provider-side fraud controls should also be enabled when SMS verification is moved to production.

## Authorization

The API checks participant membership and ownership for transaction, listing and offer operations. Administrative endpoints require the admin role. The browser is not trusted to enforce these rules.

## Payments

Razorpay credentials stay on the server. Payment signatures, order IDs, amounts and captured status are validated before a transaction is marked paid. Refunds use the provider path and cannot be bypassed by changing a browser state.

## Handoff

The handoff secret is separate from the JWT signing secret. The generated handoff code is stored only as a hash, and completing a handoff requires the participant confirmations enforced by the transaction state machine.

## Production essentials

- Use unique, randomly generated `JWT_SECRET` and `HANDOFF_SECRET` values.
- Disable `DEV_OTP_ECHO`.
- Restrict `CORS_ORIGINS` to known HTTPS origins.
- Store provider credentials in a secret manager or environment store.
- Keep production databases and media storage outside the application container filesystem.
- Review administrator accounts and remove development credentials before launch.
- Back up PostgreSQL and periodically test restore procedures.
