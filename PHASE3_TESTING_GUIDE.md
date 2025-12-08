# Phase 3: Reservations List Testing Guide

## Overview
The reservations list page has been migrated from server-side rendering to Alpine.js with client-side rendering and API integration.

## Prerequisites
1. Server is running: http://127.0.0.1:5000
2. Logged in as: `admin@test.com` / `admin123`
3. Have at least one active reservation (create one if needed)

## Test 1: Page Load and Data Fetching

### Steps
1. Navigate to: http://127.0.0.1:5000/reservations/
2. Observe the page loading

### Expected Result
✅ Loading spinner appears briefly
✅ "Lade Buchungen..." text shows
✅ Reservations table appears after loading
✅ All reservations are displayed
✅ No console errors

### Troubleshooting
- If stuck on loading: Check Network tab for API errors
- If no data: Verify `/reservations/?format=json` endpoint works

## Test 2: Reservations Display

### Steps
1. Look at the reservations table
2. Check each column

### Expected Result
✅ Court number shows correctly (e.g., "Platz 1")
✅ Date is formatted as DD.MM.YYYY
✅ Time shows start and end (e.g., "10:00 - 11:00")
✅ "Gebucht für" shows correct person
✅ "Gebucht von" shows correct person
✅ "Stornieren" button appears for each reservation

## Test 3: Successful Cancellation

### Steps
1. Click "Stornieren" on any reservation
2. Observe the behavior

### Expected Result
✅ Button text changes to "Storniere..."
✅ Button becomes disabled (grayed out)
✅ Success toast appears: "Buchung erfolgreich storniert"
✅ Reservation disappears from list immediately
✅ No page reload
✅ Other reservations remain visible

## Test 4: Multiple Cancellations

### Steps
1. If you have multiple reservations, cancel them one by one
2. Observe each cancellation

### Expected Result
✅ Each cancellation works independently
✅ Can't click other buttons while one is cancelling
✅ List updates correctly after each cancellation
✅ Toast appears for each cancellation

## Test 5: Empty State

### Steps
1. Cancel all your reservations
2. Observe the empty state

### Expected Result
✅ Table disappears
✅ Message appears: "Sie haben derzeit keine aktiven Buchungen."
✅ Back link still visible
✅ No errors in console

## Test 6: Error Handling - Network Error

### Steps
1. Open DevTools (F12)
2. Go to Network tab
3. Enable "Offline" mode
4. Refresh the page

### Expected Result
✅ Loading spinner appears
✅ Error message appears: "Fehler beim Laden der Buchungen"
✅ No infinite loading
✅ No console errors (except network errors)

### Cleanup
- Disable "Offline" mode
- Refresh page to load normally

## Test 7: Error Handling - Cancellation Error

### Steps
1. Open DevTools Console
2. Type: `fetch('/reservations/99999', {method: 'DELETE'})`
3. Press Enter (this simulates cancelling a non-existent reservation)

### Expected Result
✅ Error toast appears
✅ List remains unchanged
✅ No page crash

## Test 8: Loading State During Cancellation

### Steps
1. Open DevTools Network tab
2. Throttle network to "Slow 3G"
3. Click "Stornieren" on a reservation
4. Observe the button

### Expected Result
✅ Button shows "Storniere..." immediately
✅ Button is disabled
✅ Can't click button again
✅ Eventually completes and removes item

### Cleanup
- Reset network throttling to "No throttling"

## Test 9: Date Formatting

### Steps
1. Look at the date column
2. Verify dates are formatted correctly

### Expected Result
✅ Dates show as DD.MM.YYYY (German format)
✅ Leading zeros present (e.g., "08.12.2025" not "8.12.2025")
✅ All dates formatted consistently

## Test 10: Responsive Design

### Steps
1. Resize browser window to mobile size (< 768px)
2. Check table display

### Expected Result
✅ Table scrolls horizontally if needed
✅ All columns remain visible
✅ Buttons remain clickable
✅ Text doesn't overflow

## Test 11: Back Link

### Steps
1. Click "← Zurück zur Übersicht"

### Expected Result
✅ Navigates to dashboard
✅ No errors

## Test 12: Refresh Behavior

### Steps
1. Load the page
2. Wait for reservations to load
3. Press F5 to refresh

### Expected Result
✅ Page reloads
✅ Loading state appears again
✅ Reservations load fresh from API
✅ No stale data

## Test 13: Multiple Tabs

### Steps
1. Open reservations page in two browser tabs
2. Cancel a reservation in Tab 1
3. Refresh Tab 2

### Expected Result
✅ Tab 1: Reservation disappears immediately
✅ Tab 2: After refresh, shows updated list
✅ Both tabs show consistent data

## Test 14: API Response Validation

### Steps
1. Open DevTools Network tab
2. Refresh the page
3. Find the request to `/reservations/?format=json`
4. Check the response

### Expected Result
✅ Status: 200 OK
✅ Response is JSON
✅ Contains `reservations` array
✅ Each reservation has: id, court_number, date, start_time, end_time, booked_for, booked_by

## Browser Console Checks

### No Errors
Open console and verify:
- No red error messages
- No Alpine.js warnings
- No "undefined" errors

### Alpine Component Check
Type in console:
```javascript
Alpine.$data(document.querySelector('[x-data*="reservationsList"]'))
```
Should return the component with `reservations`, `loading`, `error`, etc.

## Performance Checks

### Network Tab
1. Open DevTools Network tab
2. Load the page
3. Check requests

**Expected:**
- GET `/reservations/?format=json` - < 500ms
- DELETE `/reservations/{id}` - < 500ms
- No duplicate requests
- No unnecessary requests

### Timing
- Initial load: < 1s
- Cancellation: < 1s
- UI update: Instant (no delay)

## Common Issues and Solutions

### Issue: Reservations don't load
**Solution:**
- Check Network tab for API errors
- Verify you're logged in
- Check that you have reservations

### Issue: Cancellation doesn't work
**Solution:**
- Check Network tab for DELETE request
- Look for error response
- Verify reservation ID is correct

### Issue: Page stuck on loading
**Solution:**
- Check console for JavaScript errors
- Verify API endpoint is responding
- Check that Alpine.js is loaded

### Issue: Date format is wrong
**Solution:**
- Check `formatDate()` function
- Verify date string format from API
- Check browser locale settings

## Success Criteria

All tests pass when:
- ✅ No console errors
- ✅ Reservations load correctly
- ✅ Cancellation works smoothly
- ✅ Loading states work
- ✅ Error handling is graceful
- ✅ No page reloads
- ✅ Toast notifications appear
- ✅ Empty state works
- ✅ Performance is smooth

## Comparison with Server-Side Version

### What's Better
- ✅ No page reloads
- ✅ Instant UI updates
- ✅ Loading states
- ✅ Better error handling
- ✅ Per-item loading indicators
- ✅ Toast notifications

### What's the Same
- ✅ Visual appearance
- ✅ Functionality
- ✅ Data accuracy
- ✅ Security (same API endpoints)

## Next Steps After Testing

Once all tests pass:
1. Document any issues found
2. Update `ALPINE_MIGRATION_PROGRESS.md` with test results
3. Proceed to Phase 4: Court Availability Grid (final phase)

## Rollback Plan

If critical issues are found:
1. Revert `app/templates/reservations.html` to previous commit
2. Document issues for future resolution
3. Old server-side version is in git history
