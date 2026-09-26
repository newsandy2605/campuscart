# Browser tests

Run these from the `frontend` directory in the VS Code terminal:

```powershell
npm install
npx playwright install chromium
npm run test:e2e
```

For the authenticated critical flow, provide separate accounts where possible:

```powershell
$env:E2E_BASE_URL="http://localhost:3000"
$env:E2E_SELLER_EMAIL="seller@YOUR_CAMPUS_DOMAIN"
$env:E2E_SELLER_PASSWORD="YOUR_SELLER_PASSWORD"
$env:E2E_BUYER_EMAIL="buyer@YOUR_CAMPUS_DOMAIN"
$env:E2E_BUYER_PASSWORD="YOUR_BUYER_PASSWORD"
$env:E2E_ADMIN_EMAIL="admin@YOUR_DOMAIN"
$env:E2E_ADMIN_PASSWORD="YOUR_ADMIN_PASSWORD"
npm run test:e2e
```

The suite includes public smoke coverage plus authenticated flows for laptop image upload/listing creation, offer submission/acceptance, local payment and pickup scheduling, and the admin console. Handoff is intentionally covered by backend integration tests because the UI requires a future pickup date; after a scheduled pickup reaches its allowed date, use the normal browser transaction page to confirm the seller code and buyer receipt.

For a quick authenticated page-only smoke check, `authenticated-critical.spec.ts` can run with just `E2E_EMAIL` and `E2E_PASSWORD`.
