import { test, expect } from '@playwright/test';

test.describe('authenticated product surfaces', () => {
  test.skip(!process.env.E2E_EMAIL || !process.env.E2E_PASSWORD, 'Set E2E_EMAIL and E2E_PASSWORD for authenticated checks.');

  test('sign in and inspect critical flows', async ({ page }) => {
    await page.goto('/login');
    await page.getByLabel(/email/i).fill(process.env.E2E_EMAIL!);
    await page.getByLabel(/password/i).fill(process.env.E2E_PASSWORD!);
    await page.getByRole('button', { name: /sign in|log in/i }).click();
    await page.waitForLoadState('networkidle');

    for (const path of ['/marketplace', '/seller', '/wanted', '/lost-found', '/swap', '/courses', '/transactions']) {
      await page.goto(path);
      await expect(page.locator('body')).not.toContainText(/Application error|Unhandled Runtime Error/i);
    }
  });
});
