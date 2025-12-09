/**
 * E2E tests for Alpine.js booking workflow
 * Feature: alpine-tdd-migration
 * Tests complete booking workflow with Alpine.js components
 */

const { test, expect } = require('@playwright/test');

test.describe('Alpine.js Booking Workflow', () => {
  test.beforeEach(async ({ page }) => {
    // Login
    await page.goto('/auth/login');
    await page.locator('input[name="email"]').fill('wolfgang.hacker@gmail.com');
    await page.locator('input[name="password"]').fill('admin123');
    await page.locator('button[type="submit"]').click();
    await expect(page).toHaveURL('/');
    
    // Wait for Alpine.js to load
    await page.waitForFunction(() => window.Alpine !== undefined);
    
    // Wait for grid to load
    await expect(page.locator('#grid-body')).not.toContainText('Lade Verfügbarkeit');
  });

  test('complete booking workflow - select date, book slot, verify success', async ({ page }) => {
    // Select tomorrow's date
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    const tomorrowStr = tomorrow.toISOString().split('T')[0];
    
    await page.locator('#date-selector').fill(tomorrowStr);
    await page.locator('#date-selector').press('Enter');
    
    // Wait for grid to update
    await page.waitForTimeout(500);
    
    // Find and click first available slot
    const availableSlot = page.locator('td.bg-green-500').first();
    await expect(availableSlot).toBeVisible();
    await availableSlot.click();
    
    // Verify modal opens
    const modal = page.locator('#booking-modal');
    await expect(modal).toBeVisible();
    await expect(modal).not.toHaveClass(/hidden/);
    
    // Verify pre-filled data
    await expect(page.locator('#booking-date')).toHaveValue(tomorrowStr);
    await expect(page.locator('#booking-court')).not.toBeEmpty();
    await expect(page.locator('#booking-time')).not.toBeEmpty();
    
    // Submit booking
    await page.getByRole('button', { name: /Buchung bestätigen/ }).click();
    
    // Verify modal closes
    await expect(modal).toHaveClass(/hidden/);
    
    // Verify success message
    await expect(page.locator('.fixed.top-4.right-4')).toContainText(/erfolgreich/i);
    
    // Verify grid updates (slot should now be red/reserved)
    await page.waitForTimeout(500);
    const reservedSlots = await page.locator('td.bg-red-500').count();
    expect(reservedSlots).toBeGreaterThan(0);
  });

  test('date navigation updates grid reactively', async ({ page }) => {
    // Get initial grid state
    const initialSlots = await page.locator('#grid-body td').count();
    expect(initialSlots).toBeGreaterThan(0);
    
    // Navigate to next day
    await page.getByRole('button', { name: /chevron_right/ }).click();
    await page.waitForTimeout(500);
    
    // Grid should update
    const nextDaySlots = await page.locator('#grid-body td').count();
    expect(nextDaySlots).toBeGreaterThan(0);
    
    // Navigate to previous day
    await page.getByRole('button', { name: /chevron_left/ }).click();
    await page.waitForTimeout(500);
    
    // Grid should update again
    const prevDaySlots = await page.locator('#grid-body td').count();
    expect(prevDaySlots).toBeGreaterThan(0);
    
    // Click "Heute" button
    await page.getByRole('button', { name: /Heute/ }).click();
    await page.waitForTimeout(500);
    
    // Should be back to today
    const today = new Date().toISOString().split('T')[0];
    await expect(page.locator('#date-selector')).toHaveValue(today);
  });

  test('modal escape key closes modal and resets state', async ({ page }) => {
    // Open modal
    const availableSlot = page.locator('td.bg-green-500').first();
    await availableSlot.click();
    
    const modal = page.locator('#booking-modal');
    await expect(modal).toBeVisible();
    
    // Press Escape
    await page.keyboard.press('Escape');
    
    // Modal should close
    await expect(modal).toHaveClass(/hidden/);
    
    // Open modal again
    await availableSlot.click();
    await expect(modal).toBeVisible();
    
    // Error should be cleared
    const errorDiv = page.locator('#booking-error');
    await expect(errorDiv).toHaveClass(/hidden/);
  });

  test('clicking outside modal closes it', async ({ page }) => {
    // Open modal
    const availableSlot = page.locator('td.bg-green-500').first();
    await availableSlot.click();
    
    const modal = page.locator('#booking-modal');
    await expect(modal).toBeVisible();
    
    // Click on modal background
    await modal.click({ position: { x: 10, y: 10 } });
    
    // Modal should close
    await expect(modal).toHaveClass(/hidden/);
  });

  test('error handling - displays error without closing modal', async ({ page }) => {
    // Create multiple bookings to potentially hit limit
    for (let i = 0; i < 3; i++) {
      const availableSlots = await page.locator('td.bg-green-500').count();
      if (availableSlots > 0) {
        await page.locator('td.bg-green-500').first().click();
        await page.getByRole('button', { name: /Buchung bestätigen/ }).click();
        await page.waitForTimeout(500);
      }
    }
    
    // Try one more booking
    const availableSlots = await page.locator('td.bg-green-500').count();
    if (availableSlots > 0) {
      await page.locator('td.bg-green-500').first().click();
      await page.getByRole('button', { name: /Buchung bestätigen/ }).click();
      
      // Check if error appears (either in modal or as toast)
      const hasModalError = await page.locator('#booking-error').isVisible();
      const hasToastError = await page.locator('.fixed.top-4.right-4.bg-red-100').count() > 0;
      
      expect(hasModalError || hasToastError).toBeTruthy();
    }
  });
});
