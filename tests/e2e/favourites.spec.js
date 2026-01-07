const { test, expect } = require('@playwright/test');

test.describe('Favourites Management', () => {
  test.beforeEach(async ({ page }) => {
    // Login before each test
    await page.goto('/auth/login');
    await page.locator('input[name="email"]').fill('wolfgang.hacker@gmail.com');
    await page.locator('input[name="password"]').fill('admin123');
    await page.locator('button[type="submit"]').click();
    await expect(page).toHaveURL('/');
  });

  test('should navigate to favourites page', async ({ page }) => {
    await page.getByRole('link', { name: /Favoriten/ }).click();
    await expect(page).toHaveURL(/\/members\/favourites/);
    await expect(page.getByText('Meine Favoriten')).toBeVisible();
  });

  test('should display favourites list', async ({ page }) => {
    await page.goto('/members/favourites');
    await expect(page.locator('#favourites-list')).toBeVisible();
  });

  test('should show add favourite button', async ({ page }) => {
    await page.goto('/members/favourites');
    await expect(page.getByRole('button', { name: /Favorit hinzufügen/ })).toBeVisible();
  });

  test('should open add favourite form', async ({ page }) => {
    await page.goto('/members/favourites');
    await page.getByRole('button', { name: /Favorit hinzufügen/ }).click();
    await expect(page.locator('#add-favourite-form')).not.toHaveClass(/hidden/);
    await expect(page.locator('#favourite-member-select')).toBeVisible();
  });

  test('should close add favourite form', async ({ page }) => {
    await page.goto('/members/favourites');
    await page.getByRole('button', { name: /Favorit hinzufügen/ }).click();
    await expect(page.locator('#add-favourite-form')).not.toHaveClass(/hidden/);
    
    await page.getByRole('button', { name: /Abbrechen/ }).click();
    await expect(page.locator('#add-favourite-form')).toHaveClass(/hidden/);
  });

  test('should only show non-favourite members in dropdown', async ({ page }) => {
    await page.goto('/members/favourites');
    await page.getByRole('button', { name: /Favorit hinzufügen/ }).click();
    
    // Wait for dropdown to load
    const options = page.locator('#favourite-member-select option');
    await expect(options).not.toHaveCount(1);
    
    // Should not contain "Alle Mitglieder sind bereits Favoriten" as the only option
    await expect(page.locator('#favourite-member-select')).not.toContainText('Alle Mitglieder sind bereits Favoriten');
  });

});
