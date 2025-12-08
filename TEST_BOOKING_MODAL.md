# Testing Booking Modal Fix

## Steps to Test

1. **Hard Refresh Browser**
   - Chrome/Edge: Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)
   - Firefox: Ctrl+F5 (Windows) or Cmd+Shift+R (Mac)
   - This clears the cached HTML and JavaScript

2. **Open Browser Console**
   - Press F12 or right-click → Inspect → Console tab

3. **Check for Function**
   - In the console, type: `typeof window.bookingModal`
   - Should return: `"function"`
   - If it returns `"undefined"`, the function isn't loading

4. **Check Console Logs**
   - Look for: `bookingModal function defined: function`
   - This confirms the script ran

5. **Test Modal**
   - Click any green (available) time slot
   - Modal should open without errors

## Expected Console Output (Good)
```
bookingModal function defined: function
Tennis Club Reservation System loaded - Bundled version
```

## Current Error (Bad)
```
Alpine Expression Error: bookingModal is not a function
```

## If Still Broken
The issue is that Alpine.js is loading with `defer` and processing the DOM before our inline script runs. We may need to:
1. Remove `defer` from Alpine.js CDN
2. OR use Alpine.data() to register the component
3. OR move Alpine.js to load AFTER our scripts

## Quick Fix to Try
In browser console, manually define the function:
```javascript
window.bookingModal = function(userId, userName) {
    return {
        isOpen: false,
        currentUserId: userId,
        currentUserName: userName,
        favourites: [],
        submitting: false,
        error: '',
        formData: { date: '', courtNumber: null, courtDisplay: '', startTime: '', timeDisplay: '', bookedForId: userId },
        init() { this.loadFavourites(); },
        async loadFavourites() { /* ... */ },
        open(courtNumber, time, date) { /* ... */ },
        close() { this.isOpen = false; },
        getEndTime(startTime) { /* ... */ },
        async submitBooking() { /* ... */ }
    };
};
```

Then refresh and try clicking a slot.
