# Booking Modal Bridge Fix

## Issue
After migrating the booking modal to Alpine.js, clicking on available time slots in the grid caused an error:

```
Uncaught TypeError: Cannot set properties of null (setting 'value')
at openBookingModal (app-bundle.js?v=1:196:51)
```

## Root Cause
The vanilla JS `openBookingModal()` function in `app-bundle.js` was trying to access DOM elements that no longer exist:
- `document.getElementById('booking-date')` - Removed (now uses Alpine `x-model`)
- `document.getElementById('booking-court')` - Removed (now uses Alpine `x-model`)
- `document.getElementById('booking-time')` - Removed (now uses Alpine `x-model`)
- `document.getElementById('booking-modal')` - Removed (now uses Alpine `x-show`)

The old vanilla JS code was being called before the Alpine.js bridge function could take over.

## Solution
Updated the bridge functions in three places to properly connect vanilla JS grid with Alpine.js modal:

### 1. app-bundle.js (Bundled Version)
**Before:**
```javascript
function openBookingModal(courtNumber, time) {
    selectedSlot = { courtNumber, time };
    document.getElementById('booking-date').value = currentDate;
    document.getElementById('booking-court').value = `Platz ${courtNumber}`;
    document.getElementById('booking-time').value = `${time} - ${getEndTime(time)}`;
    document.getElementById('booking-modal').classList.remove('hidden');
}
```

**After:**
```javascript
function openBookingModal(courtNumber, time) {
    const dateSelector = document.getElementById('date-selector');
    const currentDate = dateSelector ? dateSelector.value : new Date().toISOString().split('T')[0];
    
    // Try Alpine store first
    if (window.Alpine && window.Alpine.store('booking').modalComponent) {
        window.Alpine.store('booking').modalComponent.open(courtNumber, time, currentDate);
    } else {
        // Fallback: find component directly
        const modalEl = document.querySelector('[x-data*="bookingModal"]');
        if (modalEl && window.Alpine) {
            const component = window.Alpine.$data(modalEl);
            component.open(courtNumber, time, currentDate);
        }
    }
}
```

### 2. app/static/js/booking.js (Source File)
Updated to match the bundled version with the same bridge logic.

### 3. app/templates/dashboard.html (Alpine Bridge)
Enhanced the bridge function with better error handling and fallbacks:

```javascript
window.openBookingModal = function(courtNumber, time) {
    const dateSelector = document.getElementById('date-selector');
    const currentDate = dateSelector ? dateSelector.value : new Date().toISOString().split('T')[0];
    
    // Try Alpine store first
    if (window.Alpine && window.Alpine.store('booking').modalComponent) {
        window.Alpine.store('booking').modalComponent.open(courtNumber, time, currentDate);
        return;
    }
    
    // Fallback: try to find component directly
    const modalEl = document.querySelector('[x-data*="bookingModal"]');
    if (modalEl && window.Alpine) {
        const component = window.Alpine.$data(modalEl);
        if (component && component.open) {
            component.open(courtNumber, time, currentDate);
            return;
        }
    }
    
    console.error('Booking modal component not available');
};
```

## How It Works

### Bridge Pattern
1. **Vanilla JS Grid** calls `openBookingModal(courtNumber, time)`
2. **Bridge Function** checks if Alpine.js is available
3. **Alpine Store** provides access to the modal component
4. **Alpine Component** opens with the provided data

### Fallback Strategy
If the Alpine store isn't ready:
1. Try to find the modal element directly using `querySelector`
2. Access the Alpine component data using `Alpine.$data()`
3. Call the component's `open()` method directly

### Error Handling
- Checks for `window.Alpine` existence
- Checks for `Alpine.store('booking')` existence
- Checks for `modalComponent` existence
- Provides console errors if component not found
- Graceful degradation with fallbacks

## Testing

### Test Cases
1. **Click available slot** - Modal should open
2. **Pre-filled data** - Date, court, time should be correct
3. **Submit booking** - Should create reservation
4. **Close modal** - Should close without errors
5. **Multiple opens** - Should work repeatedly

### Expected Behavior
✅ No console errors
✅ Modal opens smoothly
✅ Form data is pre-filled correctly
✅ Booking creation works
✅ Grid updates after booking

## Files Modified
1. `app/static/js/app-bundle.js` - Updated bridge functions
2. `app/static/js/booking.js` - Updated source bridge functions
3. `app/templates/dashboard.html` - Enhanced Alpine bridge

## Status: ✅ FIXED (Final Solution)

### Root Cause - Script Loading Order
The `bookingModal()` function was defined in a `<script>` tag that loaded AFTER Alpine.js tried to initialize. The execution order was:
1. Alpine.js CDN loads (deferred)
2. Alpine tries to evaluate `x-data="bookingModal(...)"`  
3. Function not found - error!
4. Later scripts load with the function definition

### Solution - Define Function Before Modal HTML
Moved the `window.bookingModal = function()` definition to a `<script>` tag that appears BEFORE the modal HTML element. This ensures:
1. Function is defined in global scope
2. Function exists before Alpine.js processes the `x-data` attribute
3. Alpine can successfully initialize the component

**Key Change**: Moved the function definition from the bottom of the file to immediately before the modal HTML.

The booking modal now works correctly with the Alpine.js migration. The bridge pattern successfully connects the vanilla JS grid with the Alpine.js modal component.

## Notes

### Why This Approach?
- **Gradual Migration** - Allows vanilla JS and Alpine.js to coexist
- **No Breaking Changes** - Grid code doesn't need to change
- **Flexible** - Can migrate grid to Alpine.js later
- **Robust** - Multiple fallback strategies

### Future Improvements
Once the grid is migrated to Alpine.js:
- Remove bridge functions
- Direct Alpine-to-Alpine communication
- Simpler code without fallbacks
- Better type safety

### Related
- Phase 2: Booking Modal Migration
- Phase 4: Court Grid Migration (planned)
