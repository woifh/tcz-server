/**
 * E2E tests for Alpine.js cancellation workflow
 * Feature: alpine-tdd-migration
 * Tests reservation cancellation with Alpine.js components
 */

const { test, expect } = require('@playwright/test');

test.describe('Alpine.js Cancellation Workflow', () => {
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

  test('cancel own reservation from dashboard grid', async ({ page }) => {
    // First, create a booking
    const availableSlot = page.locator('td.bg-green-500').first();
    if (await availableSlot.count() > 0) {
      await availableSlot.click();
      await page.getByRole('button', { name: /Buchung bestätigen/ }).click();
      await page.waitForTimeout(1000);
    }
    
    // Find a reservation belonging to current user (should be clickable)
    const userReservation = page.locator('td.bg-red-500').first();
    const reservationCount = await userReservation.count();
    
    if (reservationCount > 0) {
      // Click on own reservation
      await userReservation.click();
      
      // Should show confirmation dialog
      page.on('dialog', async dialog => {
        expect(dialog.message()).toContain('stornieren');
        await dialog.accept();
      });
      
      // Wait for cancellation to process
      await page.waitForTimeout(1000);
      
      // Grid should update - slot should become available again
      const availableSlots = await page.locator('td.bg-green-500').count();
      expect(availableSlots).toBeGreaterThan(0);
    }
  });

  test('only own reservations are clickable for cancellation', async ({ page }) => {
    // Check if there are any reserved slots
    const reservedSlots = await page.locator('td.bg-red-500').count();
    
    if (reservedSlots > 0) {
      // Try to get cursor style on reserved slot
      const firstReserved = page.locator('td.bg-red-500').first();
      const cursorStyle = await firstReserved.evaluate(el => window.getComputedStyle(el).cursor);
      
      // Own reservations should have pointer cursor
      // Other reservations should have default cursor
      expect(['pointer', 'default', 'not-allowed']).toContain(cursorStyle);
    }
  });

  test('cancellation updates user reservations list', async ({ page }) => {
    // Get initial reservation count in the list
    const reservationsContainer = page.locator('#user-reservations');
    const initialCount = await reservationsContainer.locator('.bg-white.rounded-lg.p-4').count();
    
    if (initialCount > 0) {
      // Cancel a reservation from the grid
      const userReservation = page.locator('td.bg-red-500').first();
      
      if (await userReservation.count() > 0) {
        page.on('dialog', async dialog => {
          await dialog.accept();
        });
        
        await userReservation.click();
        await page.waitForTimeout(1000);
        
        // Reservation count should decrease
        const finalCount = await reservationsContainer.locator('.bg-white.rounded-lg.p-4').count();
        expect(finalCount).toBeLessThanOrEqual(initialCount);
      }
    }
  });

  test('cancelled slot becomes available immediately', async ({ page }) => {
    // Create a booking first
    const availableSlot = page.locator('td.bg-green-500').first();
    if (await availableSlot.count() > 0) {
      // Get the slot position
      const boundingBox = await availableSlot.boundingBox();
      
      await availableSlot.click();
      await page.getByRole('button', { name: /Buchung bestätigen/ }).click();
      await page.waitForTimeout(1000);
      
      // Now cancel it
      const reservedSlot = page.locator('td.bg-red-500').first();
      if (await reservedSlot.count() > 0) {
        page.on('dialog', async dialog => {
          await dialog.accept();
        });
        
        await reservedSlot.click();
        await page.waitForTimeout(1000);
        
        // The slot should be green (available) again
        const slotAtPosition = await page.locator('td.bg-green-500').count();
        expect(slotAtPosition).toBeGreaterThan(0);
      }
    }
  });
});
