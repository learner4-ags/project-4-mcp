import { test, expect } from '@playwright/test';
test('thermal console renders v2 reading and health badge', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('heading',{name:'Thermal Console'})).toBeVisible();
  await expect(page.locator('#reading')).toHaveText('72');
  await expect(page.locator('#health')).toHaveText('OK');
});
