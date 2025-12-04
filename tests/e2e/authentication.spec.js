const { test, expect } = require('@playwright/test');

test.describe('Authentication', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/auth/login');
  });

  test('should display login page', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'Anmelden' })).toBeVisible();
    await expect(page.locator('input[name="email"]')).toBeVisible();
    await expect(page.locator('input[name="password"]')).toBeVisible();
  });

  test('should login with valid admin credentials', async ({ page }) => {
    await page.locator('input[name="email"]').fill('wolfgang.hacker@gmail.com');
    await page.locator('input[name="password"]').fill('admin123');
    await page.locator('button[type="submit"]').click();
    
    await expect(page).toHaveURL('/');
    await expect(page.getByText('Platzübersicht')).toBeVisible();
  });

  test('should show error with invalid credentials', async ({ page }) => {
    await page.locator('input[name="email"]').fill('invalid@test.com');
    await page.locator('input[name="password"]').fill('wrongpassword');
    await page.locator('button[type="submit"]').click();
    
    await expect(page).toHaveURL(/\/auth\/login/);
  });

  test('should logout successfully', async ({ page }) => {
    // Login first
    await page.locator('input[name="email"]').fill('wolfgang.hacker@gmail.com');
    await page.locator('input[name="password"]').fill('admin123');
    await page.locator('button[type="submit"]').click();
    
    // Then logout
    await page.getByText('Abmelden').click();
    await expect(page).toHaveURL(/\/auth\/login/);
  });
});
