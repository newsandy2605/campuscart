# Engineering decisions

## FastAPI + SQLAlchemy

CampusCart has several workflows with explicit authorization rules. Keeping those rules in one typed API makes it easier to enforce ownership and state transitions consistently.

## PostgreSQL

Listings, memberships, offers, transactions and payments have relationships that benefit from relational constraints and transactions. PostgreSQL is the source of truth for that durable state.

## Redis + worker process

Redis handles short-lived state such as rate limits, cache entries and revoked tokens. Background work runs outside the request path so a slow notification or recommendation refresh does not block a user action.

## Provider adapters

Email, SMS, payments and object storage are behind small service boundaries. Local development can use deterministic substitutes while production can use real providers without changing marketplace code.

## Handoff design

The buyer receives a short code derived from the transaction and a server-side secret. The seller enters that code at pickup, then both participants confirm the handoff. The database stores only the code hash. The code is intentionally separate from the user's login credentials.

## Campus verification

OTP proves contact ownership, not enrollment. Institutional verification is therefore a separate concern and can use either allowed email domains or admin review. This keeps the authentication model honest instead of treating an SMS code as a student ID.

## Migration ownership

Alembic owns schema evolution. New schema changes are introduced as new migrations rather than modifying an already-applied migration.
