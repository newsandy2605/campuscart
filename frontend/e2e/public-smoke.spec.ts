import { test, expect } from '@playwright/test';

test('public auth surfaces load', async ({ page }) => {
  for (const path of ['/login', '/register', '/forgot-password']) {
    await page.goto(path);
    await expect(page.locator('body')).toContainText(/CampusCart/i);
  }
});

test('marketplace surface loads', async ({ page }) => {
  await page.goto('/marketplace');
  await expect(page.locator('body')).toContainText(/Marketplace|Sign in|Campus/i);
});
