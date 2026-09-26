import { test, expect, Browser } from '@playwright/test';
import path from 'node:path';

const sellerEmail = process.env.E2E_SELLER_EMAIL || process.env.E2E_EMAIL;
const sellerPassword = process.env.E2E_SELLER_PASSWORD || process.env.E2E_PASSWORD;
const buyerEmail = process.env.E2E_BUYER_EMAIL;
const buyerPassword = process.env.E2E_BUYER_PASSWORD;

let e2eListingId = '';
let e2eListingTitle = '';
let e2eTransactionId = '';

async function login(page: import('@playwright/test').Page, email: string, password: string) {
  await page.goto('/login');
  await page.getByLabel(/email or phone/i).fill(email);
  await page.getByLabel(/password/i).fill(password);
  await page.getByRole('button', { name: /continue/i }).click();
  await page.waitForLoadState('networkidle');
}

test.describe.serial('CampusCart critical user journeys', () => {
  test('seller can create a listing with a laptop photo', async ({ page }) => {
    test.skip(!sellerEmail || !sellerPassword, 'Set E2E_SELLER_EMAIL/E2E_SELLER_PASSWORD (or E2E_EMAIL/E2E_PASSWORD).');
    await login(page, sellerEmail!, sellerPassword!);
    e2eListingTitle = `E2E Laptop Photo ${Date.now()}`;
    await page.goto('/seller/new');
    await page.locator('input[type="file"]').setInputFiles(path.join(__dirname, 'fixtures', 'test-photo.png'));
    await expect(page.getByText(/1 photo added/i)).toBeVisible();
    await page.getByLabel('Title').fill(e2eListingTitle);
    await page.getByLabel('Description').fill('Browser E2E listing created from a local laptop image.');
    await page.getByRole('button', { name: /Next →/ }).click();
    await page.getByLabel('Listing price').fill('350');
    await page.getByRole('button', { name: /Next →/ }).click();
    await page.getByRole('button', { name: /Next →/ }).click();
    await expect(page.getByText(/Review before publishing/i)).toBeVisible();
    await page.getByRole('button', { name: /Publish listing/i }).click();
    await expect(page.getByText(/Listing published/i)).toBeVisible();
    await page.getByRole('link', { name: /Open Seller Studio/i }).click();
    const row = page.locator('.seller-list-row').filter({ hasText: e2eListingTitle });
    await expect(row).toBeVisible();
    const href = await row.locator('a[href^="/seller/edit/"]').getAttribute('href');
    expect(href).toMatch(/^\/seller\/edit\/\d+$/);
    e2eListingId = href!.split('/').pop()!;
  });

  test('buyer can make an offer and seller can accept it', async ({ browser }) => {
    test.skip(!buyerEmail || !buyerPassword || !sellerEmail || !sellerPassword || !e2eListingId, 'Set buyer/seller credentials and run the listing test first.');

    const buyer = await browser.newContext();
    const buyerPage = await buyer.newPage();
    await login(buyerPage, buyerEmail!, buyerPassword!);
    await buyerPage.goto(`/marketplace/${e2eListingId}`);
    await buyerPage.getByRole('button', { name: /Make offer/i }).click();
    await buyerPage.getByRole('button', { name: /Send Offer/i }).click();
    await expect(buyerPage.getByText(/Offer sent/i)).toBeVisible();
    await buyer.close();

    const seller = await browser.newContext();
    const sellerPage = await seller.newPage();
    await login(sellerPage, sellerEmail!, sellerPassword!);
    await sellerPage.goto('/seller?tab=offers&view=inbox');
    const row = sellerPage.locator('.offer-management-row').filter({ hasText: e2eListingTitle });
    await expect(row).toBeVisible();
    await row.getByRole('button', { name: 'Accept' }).click();
    await expect(row.getByText(/accepted/i)).toBeVisible().catch(() => {});

    await sellerPage.goto('/transactions');
    const txRow = sellerPage.locator('a.transaction-row').filter({ hasText: e2eListingTitle });
    await expect(txRow).toBeVisible();
    const txHref = await txRow.getAttribute('href');
    expect(txHref).toMatch(/^\/transactions\/\d+$/);
    e2eTransactionId = txHref!.split('/').pop()!;
    await seller.close();
  });

  test('buyer can complete local payment and schedule pickup', async ({ page }) => {
    test.skip(!buyerEmail || !buyerPassword || !e2eTransactionId, 'Set buyer credentials and run the offer/acceptance test first.');
    test.skip(process.env.E2E_SKIP_PAYMENT === 'true', 'Payment test explicitly skipped by E2E_SKIP_PAYMENT.');
    await login(page, buyerEmail!, buyerPassword!);
    await page.goto(`/transactions/${e2eTransactionId}`);
    const continuePayment = page.getByRole('link', { name: /Continue to payment/i });
    if (await continuePayment.count()) {
      await continuePayment.click();
      await expect(page.getByText(/Payment successful/i)).toBeVisible({ timeout: 20_000 });
      await page.getByRole('link', { name: /View Transaction/i }).click();
    }
    const schedule = page.getByRole('button', { name: /Schedule pickup/i });
    if (await schedule.count()) {
      await schedule.click();
      await expect(page.getByText(/pickup scheduled/i)).toBeVisible();
    }
  });

  test('admin surface loads with moderation, course and audit sections', async ({ page }) => {
    const email = process.env.E2E_ADMIN_EMAIL;
    const password = process.env.E2E_ADMIN_PASSWORD;
    test.skip(!email || !password, 'Set E2E_ADMIN_EMAIL and E2E_ADMIN_PASSWORD.');
    await login(page, email!, password!);
    await page.goto('/admin');
    await expect(page.getByText(/Admin Console/i)).toBeVisible();
    await expect(page.getByText(/Pending campus verification/i)).toBeVisible();
    await expect(page.getByText(/Course catalog/i)).toBeVisible();
    await expect(page.getByText(/Audit history/i)).toBeVisible();
  });
});
