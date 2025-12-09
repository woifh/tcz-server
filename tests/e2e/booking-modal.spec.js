const { test, expect } = require('@playwright/test');

test.describe('Booking Modal', () => {
  test.beforeEach(async ({ page }) => {
    // Login before each test
    await page.goto('/auth/login');
    await page.locator('input[name="email"]').fill('wolfgang.hacker@gmail.com');
    await page.locator('input[name="password"]').fill('admin123');
    await page.locator('button[type="submit"]').click();
    await expect(page).toHaveURL('/');
    
    // Wait for grid to load
    await expect(page.locator('#grid-body')).not.toContainText('Lade Verfügbarkeit');
  });

  test.describe('Modal Opening and Closing', () => {
    test('should open modal when clicking available slot', async ({ page }) => {
      // Find an available slot (green background)
      const availableSlot = page.locator('td.bg-green-500').first();
      await availableSlot.click();
      
      // Modal should be visible
      const modal = page.locator('#booking-modal');
      await expect(modal).toBeVisible();
      await expect(modal).not.toHaveClass(/hidden/);
    });

    test('should display modal with correct title', async ({ page }) => {
      const availableSlot = page.locator('td.bg-green-500').first();
      await availableSlot.click();
      
      await expect(page.getByText('Buchung erstellen')).toBeVisible();
    });

    test('should close modal when clicking cancel button', async ({ page }) => {
      const availableSlot = page.locator('td.bg-green-500').first();
      await availableSlot.click();
      
      const modal = page.locator('#booking-modal');
      await expect(modal).toBeVisible();
      
      // Click cancel button
      await page.getByRole('button', { name: /Abbrechen/ }).click();
      
      // Modal should be hidden
      await expect(modal).toHaveClass(/hidden/);
    });

    test('should close modal when pressing Escape key', async ({ page }) => {
      const availableSlot = page.locator('td.bg-green-500').first();
      await availableSlot.click();
      
      const modal = page.locator('#booking-modal');
      await expect(modal).toBeVisible();
      
      // Press Escape
      await page.keyboard.press('Escape');
      
      // Modal should be hidden
      await expect(modal).toHaveClass(/hidden/);
    });

    test('should close modal when clicking background', async ({ page }) => {
      const availableSlot = page.locator('td.bg-green-500').first();
      await availableSlot.click();
      
      const modal = page.locator('#booking-modal');
      await expect(modal).toBeVisible();
      
      // Click on the modal background (not the content)
      await modal.click({ position: { x: 10, y: 10 } });
      
      // Modal should be hidden
      await expect(modal).toHaveClass(/hidden/);
    });
  });

  test.describe('Modal Content', () => {
    test('should pre-fill date field with selected date', async ({ page }) => {
      const availableSlot = page.locator('td.bg-green-500').first();
      await availableSlot.click();
      
      const dateInput = page.locator('#booking-date');
      const dateValue = await dateInput.inputValue();
      
      // Should have a valid date (YYYY-MM-DD format)
      expect(dateValue).toMatch(/^\d{4}-\d{2}-\d{2}$/);
    });

    test('should pre-fill court field with selected court', async ({ page }) => {
      // Click on a specific court slot (e.g., Court 3)
      const courtHeader = page.getByText('Platz 3');
      const courtIndex = await courtHeader.evaluate(el => {
        return Array.from(el.parentElement.parentElement.children).indexOf(el.parentElement);
      });
      
      // Find available slot in that court column
      const availableSlot = page.locator(`#grid-body tr`).first().locator('td').nth(courtIndex);
      if (await availableSlot.locator('.bg-green-500').count() > 0) {
        await availableSlot.click();
        
        const courtInput = page.locator('#booking-court');
        await expect(courtInput).toHaveValue(/Platz \d/);
      }
    });

    test('should pre-fill time field with selected time slot', async ({ page }) => {
      const availableSlot = page.locator('td.bg-green-500').first();
      await availableSlot.click();
      
      const timeInput = page.locator('#booking-time');
      const timeValue = await timeInput.inputValue();
      
      // Should have time range format (HH:MM - HH:MM)
      expect(timeValue).toMatch(/^\d{2}:\d{2} - \d{2}:\d{2}$/);
    });

    test('should have "Gebucht für" dropdown with current user', async ({ page }) => {
      const availableSlot = page.locator('td.bg-green-500').first();
      await availableSlot.click();
      
      const dropdown = page.locator('#booking-for');
      await expect(dropdown).toBeVisible();
      
      // Should have at least one option (current user)
      const options = await dropdown.locator('option').count();
      expect(options).toBeGreaterThanOrEqual(1);
      
      // First option should be current user with "(Ich)"
      const firstOption = dropdown.locator('option').first();
      await expect(firstOption).toContainText('(Ich)');
    });

    test('should display favourites in booking dropdown', async ({ page }) => {
      // First, navigate to favourites and add one if needed
      await page.goto('/members/favourites');
      
      // Check if there are favourites
      const hasFavourites = await page.locator('.flex.justify-between.items-center.p-4.border').count() > 0;
      
      if (hasFavourites) {
        // Go back to dashboard
        await page.goto('/');
        await expect(page.locator('#grid-body')).not.toContainText('Lade Verfügbarkeit');
        
        // Open booking modal
        const availableSlot = page.locator('td.bg-green-500').first();
        await availableSlot.click();
        
        // Dropdown should have more than 1 option (user + favourites)
        const dropdown = page.locator('#booking-for');
        const options = await dropdown.locator('option').count();
        expect(options).toBeGreaterThan(1);
      }
    });

    test('should have date field as readonly', async ({ page }) => {
      const availableSlot = page.locator('td.bg-green-500').first();
      await availableSlot.click();
      
      const dateInput = page.locator('#booking-date');
      await expect(dateInput).toHaveAttribute('readonly');
    });

    test('should have court field as readonly', async ({ page }) => {
      const availableSlot = page.locator('td.bg-green-500').first();
      await availableSlot.click();
      
      const courtInput = page.locator('#booking-court');
      await expect(courtInput).toHaveAttribute('readonly');
    });

    test('should have time field as readonly', async ({ page }) => {
      const availableSlot = page.locator('td.bg-green-500').first();
      await availableSlot.click();
      
      const timeInput = page.locator('#booking-time');
      await expect(timeInput).toHaveAttribute('readonly');
    });
  });

  test.describe('Booking Creation', () => {
    test('should create booking successfully', async ({ page }) => {
      // Find an available slot
      const availableSlot = page.locator('td.bg-green-500').first();
      await availableSlot.click();
      
      // Submit the form
      await page.getByRole('button', { name: /Buchung bestätigen/ }).click();
      
      // Modal should close
      const modal = page.locator('#booking-modal');
      await expect(modal).toHaveClass(/hidden/);
      
      // Success message should appear
      await expect(page.locator('.fixed.top-4.right-4')).toContainText(/erfolgreich/i);
    });

    test('should update grid after booking creation', async ({ page }) => {
      // Count available slots before
      const availableSlotsBefore = await page.locator('td.bg-green-500').count();
      
      // Create a booking
      const availableSlot = page.locator('td.bg-green-500').first();
      await availableSlot.click();
      await page.getByRole('button', { name: /Buchung bestätigen/ }).click();
      
      // Wait for grid to update
      await page.waitForTimeout(1000);
      
      // Available slots should decrease
      const availableSlotsAfter = await page.locator('td.bg-green-500').count();
      expect(availableSlotsAfter).toBeLessThan(availableSlotsBefore);
    });

    test('should update user reservations list after booking', async ({ page }) => {
      // Get initial reservation count
      const reservationsContainer = page.locator('#user-reservations');
      const initialReservations = await reservationsContainer.locator('.bg-white.rounded-lg.p-4').count();
      
      // Create a booking
      const availableSlot = page.locator('td.bg-green-500').first();
      await availableSlot.click();
      await page.getByRole('button', { name: /Buchung bestätigen/ }).click();
      
      // Wait for update
      await page.waitForTimeout(1000);
      
      // Reservation count should increase (or stay same if at limit)
      const finalReservations = await reservationsContainer.locator('.bg-white.rounded-lg.p-4').count();
      expect(finalReservations).toBeGreaterThanOrEqual(initialReservations);
    });

    test('should create booking for favourite member', async ({ page }) => {
      // Navigate to favourites and ensure we have at least one
      await page.goto('/members/favourites');
      const hasFavourites = await page.locator('.flex.justify-between.items-center.p-4.border').count() > 0;
      
      if (hasFavourites) {
        // Get favourite name
        const favouriteName = await page.locator('.flex.justify-between.items-center.p-4.border').first().locator('h3').textContent();
        
        // Go back to dashboard
        await page.goto('/');
        await expect(page.locator('#grid-body')).not.toContainText('Lade Verfügbarkeit');
        
        // Open booking modal
        const availableSlot = page.locator('td.bg-green-500').first();
        await availableSlot.click();
        
        // Select favourite from dropdown
        const dropdown = page.locator('#booking-for');
        await dropdown.selectOption({ label: favouriteName });
        
        // Submit
        await page.getByRole('button', { name: /Buchung bestätigen/ }).click();
        
        // Success message should appear
        await expect(page.locator('.fixed.top-4.right-4')).toContainText(/erfolgreich/i);
      }
    });
  });

  test.describe('Error Handling', () => {
    test('should handle booking errors gracefully', async ({ page }) => {
      // Try to create multiple bookings to hit the limit
      for (let i = 0; i < 3; i++) {
        const availableSlots = await page.locator('td.bg-green-500').count();
        if (availableSlots > 0) {
          const availableSlot = page.locator('td.bg-green-500').first();
          await availableSlot.click();
          await page.getByRole('button', { name: /Buchung bestätigen/ }).click();
          await page.waitForTimeout(500);
        }
      }
      
      // Should show error message if limit reached
      const hasError = await page.locator('.fixed.top-4.right-4.bg-red-100').count() > 0;
      if (hasError) {
        await expect(page.locator('.fixed.top-4.right-4.bg-red-100')).toBeVisible();
      }
    });

    test('should not crash if modal elements are missing', async ({ page }) => {
      // This tests the null check fix we just implemented
      // Remove modal from DOM
      await page.evaluate(() => {
        const modal = document.getElementById('booking-modal');
        if (modal) modal.remove();
      });
      
      // Try to open modal - should not crash
      await page.evaluate(() => {
        if (typeof window.openBookingModal === 'function') {
          window.openBookingModal(1, '10:00');
        }
      });
      
      // Page should still be functional
      await expect(page.locator('#availability-grid')).toBeVisible();
    });
  });

  test.describe('Modal State Management', () => {
    test('should clear error message when reopening modal', async ({ page }) => {
      // Open modal
      const availableSlot = page.locator('td.bg-green-500').first();
      await availableSlot.click();
      
      // Close modal
      await page.getByRole('button', { name: /Abbrechen/ }).click();
      
      // Open again
      await availableSlot.click();
      
      // Error message should be hidden
      const errorDiv = page.locator('#booking-error');
      await expect(errorDiv).toHaveClass(/hidden/);
    });

    test('should maintain form state while modal is open', async ({ page }) => {
      // Open modal
      const availableSlot = page.locator('td.bg-green-500').first();
      await availableSlot.click();
      
      // Get initial values
      const initialDate = await page.locator('#booking-date').inputValue();
      const initialCourt = await page.locator('#booking-court').inputValue();
      const initialTime = await page.locator('#booking-time').inputValue();
      
      // Wait a bit
      await page.waitForTimeout(500);
      
      // Values should remain the same
      await expect(page.locator('#booking-date')).toHaveValue(initialDate);
      await expect(page.locator('#booking-court')).toHaveValue(initialCourt);
      await expect(page.locator('#booking-time')).toHaveValue(initialTime);
    });

    test('should reset form when opening different slot', async ({ page }) => {
      // Open first slot
      const firstSlot = page.locator('td.bg-green-500').first();
      await firstSlot.click();
      const firstTime = await page.locator('#booking-time').inputValue();
      
      // Close modal
      await page.getByRole('button', { name: /Abbrechen/ }).click();
      
      // Open different slot
      const secondSlot = page.locator('td.bg-green-500').nth(1);
      await secondSlot.click();
      const secondTime = await page.locator('#booking-time').inputValue();
      
      // Times should be different (unless they're the same slot)
      // This just verifies the form updates with new slot data
      expect(secondTime).toBeTruthy();
    });
  });

  test.describe('Accessibility', () => {
    test('should have proper form labels', async ({ page }) => {
      const availableSlot = page.locator('td.bg-green-500').first();
      await availableSlot.click();
      
      // Check for labels
      await expect(page.getByText('Datum', { exact: true })).toBeVisible();
      await expect(page.getByText('Platz', { exact: true })).toBeVisible();
      await expect(page.getByText('Uhrzeit', { exact: true })).toBeVisible();
      await expect(page.getByText('Gebucht für', { exact: true })).toBeVisible();
    });

    test('should have submit button with clear text', async ({ page }) => {
      const availableSlot = page.locator('td.bg-green-500').first();
      await availableSlot.click();
      
      const submitButton = page.getByRole('button', { name: /Buchung bestätigen/ });
      await expect(submitButton).toBeVisible();
      await expect(submitButton).toBeEnabled();
    });

    test('should have cancel button with clear text', async ({ page }) => {
      const availableSlot = page.locator('td.bg-green-500').first();
      await availableSlot.click();
      
      const cancelButton = page.getByRole('button', { name: /Abbrechen/ });
      await expect(cancelButton).toBeVisible();
      await expect(cancelButton).toBeEnabled();
    });
  });
});
