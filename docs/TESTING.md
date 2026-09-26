# Testing

The test suite is split between backend business-rule tests and browser-level tests. The goal is to catch incorrect state transitions and authorization failures in the API, then verify the main user journeys through the real UI.

## Backend

```powershell
cd backend
python -m pytest
```

The suite covers authentication, OTP behavior, authorization, provider signatures, pickup/handoff rules, cancellation and other transaction invariants.

## Browser tests

From `frontend`:

```powershell
npm install
npx playwright install chromium
npm run test:e2e
```

The Playwright tests live under `frontend/e2e`. Set the `E2E_*` credentials documented in `frontend/e2e/README.md` when a test needs an authenticated account.

## Useful checks

```powershell
# backend compile check
cd backend
python -m compileall -q app tests

# frontend build
cd ..\frontend
npm run build

# API benchmark
cd ..
python scripts\benchmark_api.py --url http://localhost:8100/health --requests 100
```

Do not compare benchmark numbers across different machines and networks as if they were controlled experiments.
