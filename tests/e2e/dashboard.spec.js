const { test, expect } = require('@playwright/test');

test.describe('Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    // Login before each test
    await page.goto('/auth/login');
    await page.locator('input[name="email"]').fill('wolfgang.hacker@gmail.com');
    await page.locator('input[name="password"]').fill('admin123');
    await page.locator('button[type="submit"]').click();
    await expect(page).toHaveURL('/');
  });

  test('should display dashboard with court grid', async ({ page }) => {
    await expect(page.getByText('Platzübersicht')).toBeVisible();
    await expect(page.locator('#availability-grid')).toBeVisible();
    await expect(page.getByText('Platz 1')).toBeVisible();
    await expect(page.getByText('Platz 6')).toBeVisible();
  });

  test('should display time slots from 06:00 to 21:00', async ({ page }) => {
    await expect(page.getByRole('cell', { name: '06:00' })).toBeVisible();
    await expect(page.getByRole('cell', { name: '21:00' })).toBeVisible();
  });

  test('should display legend', async ({ page }) => {
    // Wait for grid to load first
    await expect(page.locator('#grid-body')).not.toContainText('Lade Verfügbarkeit');
    
    // Check legend items - the legend container has class "flex gap-6 mb-4 text-sm"
    const legend = page.locator('.flex.gap-6.mb-4.text-sm');
    await expect(legend.getByText('Verfügbar', { exact: true })).toBeVisible();
    await expect(legend.getByText('Gebucht', { exact: true })).toBeVisible();
    await expect(legend.getByText('Gesperrt', { exact: true })).toBeVisible();
  });

  test('should display date selector with navigation arrows', async ({ page }) => {
    await expect(page.locator('#date-selector')).toBeVisible();
    await expect(page.getByRole('button', { name: /chevron_left/ })).toBeVisible();
    await expect(page.getByRole('button', { name: /chevron_right/ })).toBeVisible();
    await expect(page.getByRole('button', { name: /Heute/ })).toBeVisible();
  });

  test('should navigate to next day', async ({ page }) => {
    const today = new Date().toISOString().split('T')[0];
    await expect(page.locator('#date-selector')).toHaveValue(today);
    
    await page.getByRole('button', { name: /chevron_right/ }).click();
    
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    const tomorrowStr = tomorrow.toISOString().split('T')[0];
    await expect(page.locator('#date-selector')).toHaveValue(tomorrowStr);
  });

  test('should navigate to previous day', async ({ page }) => {
    const today = new Date().toISOString().split('T')[0];
    await expect(page.locator('#date-selector')).toHaveValue(today);
    
    await page.getByRole('button', { name: /chevron_left/ }).click();
    
    const yesterday = new Date();
    yesterday.setDate(yesterday.getDate() - 1);
    const yesterdayStr = yesterday.toISOString().split('T')[0];
    await expect(page.locator('#date-selector')).toHaveValue(yesterdayStr);
  });

  test('should return to today when clicking Heute button', async ({ page }) => {
    // Navigate away from today
    await page.getByRole('button', { name: /chevron_right/ }).click();
    
    // Click Heute button
    await page.getByRole('button', { name: /Heute/ }).click();
    
    const today = new Date().toISOString().split('T')[0];
    await expect(page.locator('#date-selector')).toHaveValue(today);
  });

  test('should display user reservations section', async ({ page }) => {
    await expect(page.getByText('Meine kommenden Buchungen')).toBeVisible();
    await expect(page.getByText('Alle anzeigen')).toBeVisible();
  });
});
