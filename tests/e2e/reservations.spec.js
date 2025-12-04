const { test, expect } = require('@playwright/test');

test.describe('Reservations', () => {
  test.beforeEach(async ({ page }) => {
    // Login before each test
    await page.goto('/auth/login');
    await page.locator('input[name="email"]').fill('wolfgang.hacker@gmail.com');
    await page.locator('input[name="password"]').fill('admin123');
    await page.locator('button[type="submit"]').click();
    await expect(page).toHaveURL('/');
  });

  test('should open booking modal when clicking available slot', async ({ page }) => {
    // Wait for grid to load
    await expect(page.locator('#grid-body')).not.toContainText('Lade Verfügbarkeit');
    
    // Wait for JavaScript to be fully loaded
    await page.waitForFunction(() => typeof window.openBookingModal === 'function');
    
    // Wait for available slots to be present
    await page.locator('.bg-green-500').first().waitFor({ state: 'visible' });
    
    // Call the openBookingModal function directly (simulating a click on court 1 at 06:00)
    await page.evaluate(() => window.openBookingModal(1, '06:00'));
    
    // Modal should be visible
    await expect(page.locator('#booking-modal')).toBeVisible();
    await expect(page.getByText('Buchung erstellen')).toBeVisible();
    await expect(page.locator('#booking-date')).toBeVisible();
    await expect(page.locator('#booking-court')).toBeVisible();
    await expect(page.locator('#booking-time')).toBeVisible();
    await expect(page.locator('#booking-for')).toBeVisible();
  });

  test('should close booking modal when clicking cancel', async ({ page }) => {
    // Wait for grid to load
    await expect(page.locator('#grid-body')).not.toContainText('Lade Verfügbarkeit');
    
    // Wait for JavaScript to be fully loaded
    await page.waitForFunction(() => typeof window.openBookingModal === 'function');
    
    // Wait for available slots
    await page.locator('.bg-green-500').first().waitFor({ state: 'visible' });
    
    // Open modal directly
    await page.evaluate(() => window.openBookingModal(1, '06:00'));
    await expect(page.locator('#booking-modal')).toBeVisible();
    
    // Click cancel
    await page.getByRole('button', { name: /Abbrechen/ }).click();
    
    // Modal should be hidden
    await expect(page.locator('#booking-modal')).not.toBeVisible();
  });

  test('should create a reservation', async ({ page }) => {
    // First, cancel an existing reservation to free up a slot (max 2 reservations per user)
    await page.goto('/reservations/');
    
    // Wait for page to load
    await page.waitForLoadState('networkidle');
    
    // Check if there are any reservations to cancel
    const cancelButtons = page.locator('button:has-text("Stornieren")');
    const cancelCount = await cancelButtons.count();
    
    if (cancelCount > 0) {
      // Set up dialog handler for the confirmation
      page.on('dialog', dialog => dialog.accept());
      
      // Cancel the first reservation (this will trigger a form submit and page reload)
      await cancelButtons.first().click();
      
      // Wait for navigation to complete
      await page.waitForLoadState('networkidle');
      
      // Check for success message in flash messages
      const successMessage = page.locator('.alert-success, .bg-green-100, :has-text("erfolgreich storniert")');
      if (await successMessage.count() > 0) {
        await expect(successMessage.first()).toBeVisible();
      }
    }
    
    // Go back to dashboard
    await page.goto('/');
    
    // Wait for grid to load
    await expect(page.locator('#grid-body')).not.toContainText('Lade Verfügbarkeit');
    
    // Wait for JavaScript to be fully loaded
    await page.waitForFunction(() => typeof window.openBookingModal === 'function');
    
    // Wait for available slots
    await page.locator('.bg-green-500').first().waitFor({ state: 'visible' });
    
    // Open modal directly
    await page.evaluate(() => window.openBookingModal(1, '06:00'));
    
    // Wait for modal and form to be visible
    await expect(page.locator('#booking-modal')).toBeVisible();
    await expect(page.locator('#booking-for')).toBeVisible();
    
    // Fill form and submit
    await page.locator('#booking-for').selectOption({ index: 0 }); // Select first option (self)
    await page.getByRole('button', { name: /Buchung bestätigen/ }).click();
    
    // Should show success message
    await expect(page.getByText('Buchung erfolgreich erstellt')).toBeVisible({ timeout: 10000 });
    
    // Modal should close
    await expect(page.locator('#booking-modal')).not.toBeVisible();
  });

  test('should display reservations list', async ({ page }) => {
    await page.goto('/reservations/');
    await expect(page.getByRole('heading', { name: 'Meine Buchungen' })).toBeVisible();
  });

  test('should navigate to reservations page from dashboard', async ({ page }) => {
    await page.getByRole('link', { name: /Meine Buchungen/ }).first().click();
    await expect(page).toHaveURL(/\/reservations/);
  });
});
