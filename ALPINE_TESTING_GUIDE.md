# Alpine.js Migration Testing Guide

## Quick Start

1. **Ensure the server is running:**
   ```bash
   source venv/bin/activate
   export DATABASE_URL="sqlite:////$(pwd)/instance/tennis_club.db"
   flask run
   ```

2. **Open your browser:**
   - Navigate to: http://127.0.0.1:5000

3. **Login:**
   - Email: `admin@test.com`
   - Password: `admin123`

## Phase 1: Member Search Component Testing

### Access the Favourites Page
1. After logging in, navigate to: http://127.0.0.1:5000/members/favourites
2. You should see the "Meine Favoriten" page

### Test 1: Opening the Search Form
**Steps:**
1. Click the "Favorit hinzufügen" button
2. The search form should appear with a gray background
3. The search input should automatically receive focus

**Expected Result:**
✅ Search form appears smoothly
✅ Input field is focused and ready for typing
✅ No console errors

### Test 2: Basic Search Functionality
**Steps:**
1. Type "admin" in the search box
2. Wait 300ms (debounce delay)
3. Results should appear

**Expected Result:**
✅ Loading spinner appears briefly
✅ Search results display with name and email
✅ "Hinzufügen" button appears for each result
✅ Clear button (X) appears in the search box

### Test 3: Clear Button
**Steps:**
1. With text in the search box, click the X button
2. Search box should clear
3. Results should disappear

**Expected Result:**
✅ Input clears immediately
✅ Results disappear
✅ Clear button disappears
✅ Focus returns to search input

### Test 4: Keyboard Navigation
**Steps:**
1. Type "test" to get some results
2. Press Arrow Down key
3. First result should highlight in blue
4. Press Arrow Down again
5. Second result should highlight
6. Press Arrow Up
7. First result should highlight again
8. Press Enter

**Expected Result:**
✅ Arrow keys navigate through results
✅ Highlighted result has blue background
✅ Enter key adds the highlighted member to favourites

### Test 5: Adding to Favourites
**Steps:**
1. Search for a member
2. Click the "Hinzufügen" button on a result

**Expected Result:**
✅ Green success message appears: "Favorit erfolgreich hinzugefügt!"
✅ The added member disappears from search results
✅ The favourites list below updates automatically
✅ Success message disappears after 3 seconds

### Test 6: Empty Search Results
**Steps:**
1. Type "zzzzzzz" (something that won't match)
2. Wait for search to complete

**Expected Result:**
✅ "Keine Mitglieder gefunden" message appears
✅ No error in console

### Test 7: Closing the Search Form
**Steps:**
1. With the search form open, click "Schließen"

**Expected Result:**
✅ Search form closes
✅ Search input clears
✅ Results clear

### Test 8: Favourites List Display
**Steps:**
1. View the favourites list section

**Expected Result:**
✅ If no favourites: "Keine Favoriten vorhanden..." message
✅ If favourites exist: Each shows name, email, and "Entfernen" button
✅ List updates automatically when favourites are added

### Test 9: Removing Favourites
**Steps:**
1. Add a member to favourites (if none exist)
2. Click "Entfernen" on a favourite
3. Confirm the dialog

**Expected Result:**
✅ Confirmation dialog appears
✅ After confirming, favourite is removed
✅ Success toast appears: "Favorit erfolgreich entfernt"
✅ List updates automatically

### Test 10: Error Handling
**Steps:**
1. Open browser DevTools (F12)
2. Go to Network tab
3. Enable "Offline" mode
4. Try to search for a member

**Expected Result:**
✅ Error message appears: "Netzwerkfehler. Bitte überprüfen Sie Ihre Verbindung."
✅ No JavaScript errors in console
✅ App remains functional after re-enabling network

## Browser Console Checks

Open the browser console (F12) and verify:

### No Errors
- No red error messages
- No Alpine.js warnings
- No "undefined" function errors

### Alpine.js is Loaded
Type in console:
```javascript
Alpine.version
```
Should return: `"3.13.3"`

### Store is Available
Type in console:
```javascript
Alpine.store('favourites')
```
Should return an object with `items`, `loading`, `error`, etc.

## Visual Regression Checks

### Before/After Comparison
The page should look identical to the vanilla JS version:
- Same layout
- Same colors
- Same animations
- Same responsive behavior

### Responsive Testing
Test on different screen sizes:
- Desktop (1920x1080)
- Tablet (768x1024)
- Mobile (375x667)

## Performance Checks

### Network Tab
1. Open DevTools Network tab
2. Perform a search
3. Check the request to `/members/search?q=...`

**Expected:**
- Only ONE request per search (debouncing works)
- Response time < 200ms
- No duplicate requests

### Memory Leaks
1. Open/close search form 10 times
2. Add/remove favourites 10 times
3. Check browser memory usage

**Expected:**
- Memory usage stays stable
- No continuous growth

## Accessibility Testing

### Keyboard Navigation
- Tab through all interactive elements
- All buttons should be reachable
- Focus indicators should be visible

### Screen Reader
If you have a screen reader:
- Search results count should be announced
- Button labels should be clear
- Form labels should be present

## Common Issues and Solutions

### Issue: Search form doesn't open
**Solution:** Check console for Alpine.js errors. Ensure Alpine is loaded in base.html

### Issue: Results don't appear
**Solution:** Check Network tab for API errors. Verify `/members/search` endpoint is working

### Issue: Favourites list doesn't update
**Solution:** Check that Alpine store is initialized. Look for `alpine:init` event

### Issue: Keyboard navigation doesn't work
**Solution:** Ensure search input has focus. Check for JavaScript errors

## Success Criteria

All tests pass when:
- ✅ No console errors
- ✅ All interactive elements work
- ✅ State updates are reactive and automatic
- ✅ Performance is smooth (no lag)
- ✅ Accessibility features work
- ✅ Error handling is graceful

## Next Steps After Testing

Once all tests pass:
1. Document any issues found
2. Proceed to Phase 2: Booking Modal migration
3. Update `ALPINE_MIGRATION_PROGRESS.md` with test results

## Rollback Plan

If critical issues are found:
1. The old vanilla JS version is preserved in git history
2. Revert `app/templates/favourites.html` to previous commit
3. Document issues for future resolution
