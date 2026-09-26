# CampusCart — Security Model

## Authentication

Passwords are salted and hashed. Access tokens are signed JWTs and can be revoked through Redis. OTP challenges are hashed, expire, have a maximum attempt count, and are invalidated when a new challenge is issued for the same destination/purpose.

## Abuse controls

Registration, login, OTP, messaging and offers use Redis-backed rate limits. The OTP endpoint has both a request cooldown and a rolling request limit. In production, enable provider-side geographic restrictions and fraud controls for SMS verification.

## Authorization

Participant-only transaction endpoints verify buyer/seller membership. Seller-owned listings and offer operations enforce ownership at the API layer. Admin endpoints require the `admin` role. Payment and refund operations are restricted to transaction participants and server-side provider state is validated before marking a transaction paid.

## Payments

Razorpay credentials are backend-only. Payment signatures, order IDs, amounts and captured status are checked before the transaction state changes. Refunds are provider-side operations; paid transaction cancellation is not allowed to bypass the refund path.

## Production checklist

- Set strong, unique `JWT_SECRET` and `HANDOFF_SECRET`.
- Disable `DEV_OTP_ECHO`.
- Restrict `CORS_ORIGINS` to known HTTPS origins.
- Use real SMTP/Twilio/Razorpay secrets via environment variables or a secret manager.
- Terminate TLS at the reverse proxy/load balancer.
- Rotate provider credentials and webhook secrets periodically.
- Back up PostgreSQL and test restore procedures.
- Review admin accounts and remove demo credentials before deployment.
