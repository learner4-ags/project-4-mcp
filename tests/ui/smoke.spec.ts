import { test, expect } from '@playwright/test';
test('starter thermal console renders', async ({ page }) => { await page.goto('/'); await expect(page.getByRole('heading',{name:'Thermal Console'})).toBeVisible(); await expect(page.locator('#reading')).toHaveText('72'); });
