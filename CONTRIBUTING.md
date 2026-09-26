# Contributing to CampusCart

CampusCart is developed as a small full-stack application rather than a collection of independent demos. Keep changes focused, make business rules explicit, and prefer extending an existing service over adding another abstraction.

## Local setup

1. Copy `.env.example` to `.env`.
2. Start the stack with `docker compose up --build`.
3. Seed the development database with `docker compose exec backend python seed.py`.
4. Open the web app at `http://localhost:3000`.

## Before committing

Run the backend tests and a frontend production build. For changes that affect a user journey, run the relevant Playwright test as well.

```powershell
cd backend
python -m pytest

cd ..\frontend
npm run build
npm run test:e2e
```

## Database changes

Use Alembic for schema changes. Create a new migration instead of editing a migration that may already have been applied elsewhere.

## API changes

Keep request and response schemas in `backend/app/schemas.py` and enforce authorization in the API layer. Do not rely on the browser to enforce ownership rules.

## Secrets

Never commit `.env`, provider credentials, API secrets, or test dumps. Development placeholders belong in the environment templates only.
