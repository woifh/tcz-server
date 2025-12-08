# Phase 2: Booking Modal Testing Guide

## Overview
The booking modal has been migrated from vanilla JavaScript to Alpine.js. This guide covers all test cases to verify the migration was successful.

## Prerequisites
1. Server is running: http://127.0.0.1:5000
2. Logged in as: `admin@test.com` / `admin123`
3. On dashboard page: http://127.0.0.1:5000/

## Test 1: Opening the Modal

### Steps
1. Look at the court availability grid
2. Find a green (available) time slot
3. Click on the green slot

### Expected Result
✅ Modal appears with dark backdrop
✅ Modal is centered on screen
✅ Form shows pre-filled data:
  - Date matches the selected date
  - Court shows "Platz X" (correct court number)
  - Time shows "HH:MM - HH:MM" (1-hour slot)
  - "Gebucht für" dropdown shows current user

### Troubleshooting
- If modal doesn't open: Check browser console for errors
- If data is wrong: Verify `openBookingModal()` is being called correctly

## Test 2: Favourites in Dropdown

### Steps
1. Open the booking modal
2. Click on the "Gebucht für" dropdown
3. Check the options

### Expected Result
✅ First option is current user with "(Ich)"
✅ If favourites exist, they appear below
✅ Each favourite shows their name

### Setup (if no favourites)
1. Go to `/members/favourites`
2. Add a favourite using the search
3. Return to dashboard
4. Open booking modal again

## Test 3: Successful Booking

### Steps
1. Open booking modal on an available slot
2. Leave "Gebucht für" as yourself
3. Click "Buchung bestätigen"

### Expected Result
✅ Button text changes to "Wird gebucht..."
✅ Button becomes disabled
✅ Modal closes automatically
✅ Green success toast appears: "Buchung erfolgreich erstellt!"
✅ Grid refreshes - slot turns red
✅ "Meine kommenden Buchungen" section updates
✅ New booking appears in the list

## Test 4: Booking for a Favourite

### Steps
1. Ensure you have at least one favourite
2. Open booking modal
3. Select a favourite from "Gebucht für" dropdown
4. Click "Buchung bestätigen"

### Expected Result
✅ Booking is created for the selected person
✅ Success toast appears
✅ Grid updates
✅ Booking shows the favourite's name (not yours)

## Test 5: Escape Key to Close

### Steps
1. Open booking modal
2. Press the Escape key

### Expected Result
✅ Modal closes immediately
✅ No booking is created
✅ Grid remains unchanged

## Test 6: Click Outside to Close

### Steps
1. Open booking modal
2. Click on the dark backdrop (outside the white modal box)

### Expected Result
✅ Modal closes immediately
✅ No booking is created
✅ Grid remains unchanged

## Test 7: Cancel Button

### Steps
1. Open booking modal
2. Click the "Abbrechen" button

### Expected Result
✅ Modal closes immediately
✅ No booking is created
✅ Grid remains unchanged

## Test 8: Error Handling - Duplicate Booking

### Steps
1. Book a time slot successfully
2. Try to book the same slot again (refresh page if needed)
3. Click on the now-red slot
4. If it opens modal, try to submit

### Expected Result
✅ Either:
  - Modal doesn't open for booked slots (correct behavior), OR
  - Error message appears in modal: "Fehler beim Erstellen der Buchung"
✅ Modal stays open to show error
✅ User can close modal and try again

## Test 9: Disabled State During Submission

### Steps
1. Open booking modal
2. Click "Buchung bestätigen"
3. Quickly try to:
   - Click the button again
   - Click "Abbrechen"
   - Press Escape
   - Click outside

### Expected Result
✅ Button shows "Wird gebucht..." text
✅ Button is disabled (grayed out)
✅ Cancel button is disabled
✅ Cannot close modal during submission
✅ After submission completes, modal closes

## Test 10: Form Data Persistence

### Steps
1. Open booking modal for Court 1 at 10:00
2. Note the displayed information
3. Close modal (Escape or Cancel)
4. Open modal for Court 3 at 14:00

### Expected Result
✅ New modal shows Court 3 (not Court 1)
✅ New modal shows 14:00 time (not 10:00)
✅ Form data is correctly updated each time

## Test 11: Responsive Design

### Steps
1. Open booking modal
2. Resize browser window to mobile size (< 768px)
3. Check modal appearance

### Expected Result
✅ Modal remains centered
✅ Modal width adjusts to screen
✅ All form fields are readable
✅ Buttons stack properly
✅ Can still close modal

## Test 12: Integration with Vanilla JS Grid

### Steps
1. Open browser console (F12)
2. Type: `window.openBookingModal(1, '10:00')`
3. Press Enter

### Expected Result
✅ Modal opens
✅ Shows Court 1
✅ Shows 10:00 time
✅ Form is functional

This confirms the bridge between vanilla JS and Alpine.js works.

## Test 13: Multiple Open/Close Cycles

### Steps
1. Open modal
2. Close modal
3. Repeat 5 times
4. Check browser memory (DevTools > Memory)

### Expected Result
✅ Modal opens/closes smoothly each time
✅ No lag or performance degradation
✅ Memory usage stays stable
✅ No memory leaks

## Test 14: Keyboard Navigation

### Steps
1. Open modal
2. Press Tab key repeatedly
3. Navigate through all form fields

### Expected Result
✅ Tab moves through: dropdown → confirm button → cancel button
✅ Focus indicators are visible
✅ Can submit with Enter key when on confirm button
✅ Can close with Escape from any field

## Browser Console Checks

### No Errors
Open console and verify:
- No red error messages
- No Alpine.js warnings
- No "undefined" function errors

### Alpine Store Check
Type in console:
```javascript
Alpine.store('booking')
```
Should return an object with `modalComponent` property.

### Component Check
Type in console:
```javascript
Alpine.store('booking').modalComponent
```
Should return the booking modal component with methods like `open()`, `close()`, etc.

## Performance Checks

### Network Tab
1. Open DevTools Network tab
2. Create a booking
3. Check the request to `/reservations/`

**Expected:**
- POST request to `/reservations/`
- Response time < 500ms
- Status 200 or 201
- No duplicate requests

### Timing
- Modal open: < 50ms
- Modal close: < 50ms
- Form submission: < 500ms
- Grid refresh: < 1s

## Common Issues and Solutions

### Issue: Modal doesn't open
**Solution:** 
- Check console for Alpine.js errors
- Verify `Alpine.store('booking').modalComponent` exists
- Check that Alpine is initialized

### Issue: Form data is wrong
**Solution:**
- Check that `openBookingModal()` receives correct parameters
- Verify date selector has correct value
- Check `getEndTime()` function logic

### Issue: Favourites don't load
**Solution:**
- Check Network tab for `/members/{id}/favourites` request
- Verify user has favourites
- Check console for fetch errors

### Issue: Booking doesn't create
**Solution:**
- Check Network tab for `/reservations/` POST request
- Look for error response
- Verify all required fields are sent

### Issue: Grid doesn't refresh
**Solution:**
- Check that `window.loadAvailability` exists
- Verify it's being called after successful booking
- Check console for errors in grid loading

## Success Criteria

All tests pass when:
- ✅ No console errors
- ✅ Modal opens/closes smoothly
- ✅ Form data is correct
- ✅ Bookings are created successfully
- ✅ Grid and reservations list update
- ✅ Escape and click-outside work
- ✅ Error handling is graceful
- ✅ Performance is smooth
- ✅ Vanilla JS integration works

## Comparison with Vanilla JS Version

### What's Better
- ✅ Cleaner form binding with `x-model`
- ✅ Built-in escape key support
- ✅ Built-in click-outside support
- ✅ Reactive disabled states
- ✅ Inline error display
- ✅ Better loading states

### What's the Same
- ✅ Visual appearance
- ✅ Functionality
- ✅ API integration
- ✅ Grid integration

## Next Steps After Testing

Once all tests pass:
1. Document any issues found
2. Update `ALPINE_MIGRATION_PROGRESS.md` with test results
3. Proceed to Phase 3: Reservation Cancellation
4. Consider removing old booking.js code (after full migration)

## Rollback Plan

If critical issues are found:
1. Revert `app/templates/dashboard.html` to previous commit
2. Document issues for future resolution
3. Old vanilla JS version is in git history
