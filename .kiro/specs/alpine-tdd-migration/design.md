# Design Document: Alpine.js TDD Migration

## Overview

This design document outlines the architecture and implementation strategy for migrating the Tennis Club Reservation System's frontend from vanilla JavaScript to Alpine.js using Test-Driven Development (TDD). The migration will be incremental, starting with comprehensive tests before refactoring each component.

The current system has:
- Vanilla JavaScript files: `app.js`, `booking.js`, `grid.js`, `reservations.js`, `utils.js`
- Partial Alpine.js implementation: favourites page and reservations list
- A bundled JavaScript file: `app-bundle.js`

The goal is to:
1. Write tests first (TDD approach)
2. Migrate all vanilla JavaScript to Alpine.js components
3. Maintain 100% functionality during migration
4. Achieve comprehensive test coverage
5. Improve code maintainability and reactivity

## Architecture

### Component Structure

The application will be organized into Alpine.js components with clear separation of concerns:

```
Alpine.js Components:
├── Dashboard Component (x-data="dashboard()")
│   ├── Grid State Management
│   ├── Date Navigation
│   ├── Slot Rendering
│   └── User Reservations Display
├── Booking Modal Component (x-data="bookingModal()")
│   ├── Form State
│   ├── Validation Logic
│   ├── API Submission
│   └── Error Handling
├── Favourites Store (Alpine.store('favourites'))
│   ├── Favourites List
│   ├── Add/Remove Operations
│   └── API Synchronization
└── Reservations Component (x-data="reservationsList()")
    ├── Reservations List State
    ├── Cancellation Logic
    └── Filtering/Sorting
```

### Data Flow

```
User Interaction → Alpine Component → API Call → State Update → Reactive UI Update
                                    ↓
                              Alpine Store (shared state)
                                    ↓
                          Other Components (reactive)
```

### Testing Strategy

**Test Pyramid:**
- E2E Tests (Playwright): Critical user workflows
- Component Tests (Vitest + Alpine Test Utils): Component behavior
- Unit Tests (Vitest): Utility functions and helpers

**TDD Workflow:**
1. Write failing test
2. Implement minimal code to pass test
3. Refactor while keeping tests green
4. Repeat

## Components and Interfaces

### 1. Dashboard Component

**Purpose:** Manages the main court availability grid, date selection, and user reservations display.

**Alpine.js Component Structure:**
```javascript
function dashboard() {
    return {
        // State
        selectedDate: new Date().toISOString().split('T')[0],
        courts: [],
        timeSlots: [],
        availability: {},
        userReservations: [],
        loading: false,
        error: null,
        
        // Lifecycle
        init() {
            this.loadAvailability();
            this.loadUserReservations();
        },
        
        // Methods
        async loadAvailability() { },
        async loadUserReservations() { },
        changeDate(offset) { },
        goToToday() { },
        handleSlotClick(court, time, slot) { },
        getSlotClass(slot) { },
        canCancelSlot(slot) { }
    }
}
```

**API Interface:**
- `GET /api/courts/availability?date={date}` - Returns availability grid
- `GET /api/reservations/user/upcoming` - Returns user's upcoming reservations

**Template Directives:**
```html
<div x-data="dashboard()" x-init="init()">
    <input type="date" x-model="selectedDate" @change="loadAvailability()">
    <template x-for="slot in timeSlots">
        <div @click="handleSlotClick(court, time, slot)" 
             :class="getSlotClass(slot)">
        </div>
    </template>
</div>
```

### 2. Booking Modal Component

**Purpose:** Handles the booking creation workflow with form validation and API submission.

**Alpine.js Component Structure:**
```javascript
function bookingModal() {
    return {
        // State
        show: false,
        date: '',
        court: null,
        time: '',
        bookedFor: null,
        favourites: [],
        submitting: false,
        error: null,
        
        // Methods
        open(date, court, time) { },
        close() { },
        async submit() { },
        validate() { },
        reset() { }
    }
}
```

**API Interface:**
- `POST /api/reservations` - Creates a new reservation
  - Request: `{ date, court_id, start_time, booked_for_id }`
  - Response: `{ success, reservation, message }`

**Template Directives:**
```html
<div x-data="bookingModal()" 
     x-show="show" 
     @keydown.escape.window="close()"
     @click.self="close()">
    <form @submit.prevent="submit()">
        <select x-model="bookedFor">
            <template x-for="fav in favourites">
                <option :value="fav.id" x-text="fav.name"></option>
            </template>
        </select>
        <div x-show="error" x-text="error"></div>
        <button type="submit" :disabled="submitting">Bestätigen</button>
    </form>
</div>
```

### 3. Favourites Store

**Purpose:** Centralized state management for user's favourite members, accessible across components.

**Alpine.js Store Structure:**
```javascript
Alpine.store('favourites', {
    // State
    items: [],
    loading: false,
    error: null,
    
    // Methods
    async load() { },
    async add(memberId) { },
    async remove(favouriteId) { },
    getById(id) { },
    getAll() { }
})
```

**API Interface:**
- `GET /api/favourites` - Returns user's favourites
- `POST /api/favourites` - Adds a favourite
- `DELETE /api/favourites/{id}` - Removes a favourite

### 4. Reservations Component

**Purpose:** Displays and manages user's reservations list with cancellation functionality.

**Alpine.js Component Structure:**
```javascript
function reservationsList() {
    return {
        // State
        reservations: [],
        loading: false,
        error: null,
        filter: 'upcoming', // 'upcoming' | 'past' | 'all'
        
        // Methods
        async load() { },
        async cancel(reservationId) { },
        filterReservations() { },
        formatDate(date) { },
        formatTime(time) { }
    }
}
```

**API Interface:**
- `GET /api/reservations/user` - Returns all user reservations
- `DELETE /api/reservations/{id}` - Cancels a reservation

## Data Models

### Availability Slot
```javascript
{
    court_id: number,
    court_name: string,
    time: string, // "HH:00"
    status: 'available' | 'reserved' | 'blocked',
    reservation: {
        id: number,
        member_name: string,
        member_id: number,
        is_short_notice: boolean
    } | null,
    block: {
        id: number,
        reason: string
    } | null
}
```

### Reservation
```javascript
{
    id: number,
    date: string, // "YYYY-MM-DD"
    start_time: string, // "HH:00"
    end_time: string, // "HH:00"
    court_id: number,
    court_name: string,
    member_id: number,
    member_name: string,
    booked_for_id: number,
    booked_for_name: string,
    is_short_notice: boolean,
    created_at: string
}
```

### Favourite
```javascript
{
    id: number,
    member_id: number,
    member_name: string,
    member_email: string
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Grid reactivity preservation
*For any* date selection change, the availability grid should update to reflect the new date's data without requiring a page reload.
**Validates: Requirements 1.2**

### Property 2: Booking modal data consistency
*For any* available slot clicked, the booking modal should open with the exact court, date, and time of the clicked slot pre-filled.
**Validates: Requirements 2.1**

### Property 3: Reservation cancellation authorization
*For any* reservation displayed in the grid, only reservations belonging to the current user should be clickable for cancellation.
**Validates: Requirements 1.4**

### Property 4: Favourites store synchronization
*For any* change to the favourites list (add or remove), all components consuming the favourites store should update reactively to reflect the change.
**Validates: Requirements 7.2, 7.3**

### Property 5: Error state isolation
*For any* component error, the error should be contained within that component without affecting other components' functionality.
**Validates: Requirements 8.2**

### Property 6: API failure recovery
*For any* failed API request, the system should display an appropriate error message and allow the user to retry the operation.
**Validates: Requirements 8.3**

### Property 7: Form validation consistency
*For any* booking form submission with invalid data, the system should prevent submission and display specific validation errors.
**Validates: Requirements 2.2, 8.4**

### Property 8: State persistence across navigation
*For any* date navigation action (previous/next/today), the selected date state should update correctly and persist until changed again.
**Validates: Requirements 1.2, 3.3**

### Property 9: Modal escape handling
*For any* open modal, pressing Escape or clicking outside should close the modal and reset its state.
**Validates: Requirements 2.5**

### Property 10: Slot color coding accuracy
*For any* slot in the availability grid, the visual styling should accurately reflect its status (available/reserved/blocked/short-notice).
**Validates: Requirements 1.5**

## Error Handling

### Error Categories

1. **Network Errors**
   - Connection failures
   - Timeout errors
   - Server unavailable (500, 502, 503)
   - Strategy: Display retry button, log error, maintain last known state

2. **Validation Errors**
   - Invalid form inputs
   - Business rule violations (e.g., max reservations exceeded)
   - Strategy: Display field-specific errors in German, prevent submission

3. **Authorization Errors**
   - Unauthorized actions (403)
   - Session expired (401)
   - Strategy: Redirect to login, display appropriate message

4. **Not Found Errors**
   - Resource doesn't exist (404)
   - Strategy: Display user-friendly message, offer navigation options

5. **Component Errors**
   - JavaScript runtime errors
   - Alpine.js component failures
   - Strategy: Log to console, display fallback UI, isolate error

### Error Display Strategy

```javascript
// Component-level error handling
{
    error: null,
    
    async performAction() {
        try {
            this.error = null;
            // ... action logic
        } catch (err) {
            this.error = this.formatError(err);
            console.error('Action failed:', err);
        }
    },
    
    formatError(err) {
        if (err.response) {
            return err.response.data.message || 'Ein Fehler ist aufgetreten';
        }
        if (err.request) {
            return 'Netzwerkfehler. Bitte versuchen Sie es erneut.';
        }
        return 'Ein unerwarteter Fehler ist aufgetreten.';
    }
}
```

## Testing Strategy

### 1. E2E Tests (Playwright)

**Test Framework:** Playwright
**Test Location:** `tests/e2e/`
**Minimum Iterations:** N/A (E2E tests are deterministic scenarios)

**Test Scenarios:**

1. **Complete Booking Workflow**
   - Navigate to dashboard
   - Select a date
   - Click available slot
   - Fill booking form
   - Submit and verify success
   - Verify grid updates

2. **Cancellation Workflow**
   - Navigate to dashboard with existing reservation
   - Click own reservation
   - Confirm cancellation
   - Verify grid updates

3. **Date Navigation**
   - Click previous day
   - Verify grid updates
   - Click next day
   - Verify grid updates
   - Click "Heute" button
   - Verify returns to today

4. **Error Handling**
   - Attempt to book already reserved slot
   - Verify error message displays
   - Attempt to book blocked slot
   - Verify appropriate message

5. **Favourites Integration**
   - Add a favourite
   - Open booking modal
   - Verify favourite appears in dropdown
   - Book for favourite
   - Verify reservation created for correct person

**Example E2E Test:**
```javascript
test('complete booking workflow', async ({ page }) => {
    await page.goto('/dashboard');
    
    // Select tomorrow's date
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    await page.fill('#date-selector', tomorrow.toISOString().split('T')[0]);
    
    // Wait for grid to load
    await page.waitForSelector('.slot-available');
    
    // Click first available slot
    await page.click('.slot-available');
    
    // Verify modal opens
    await expect(page.locator('#booking-modal')).toBeVisible();
    
    // Submit booking
    await page.click('button[type="submit"]');
    
    // Verify success message
    await expect(page.locator('.alert-success')).toBeVisible();
    
    // Verify grid updated
    await expect(page.locator('.slot-reserved')).toBeVisible();
});
```

### 2. Component Tests (Vitest + Alpine Test Utils)

**Test Framework:** Vitest with Alpine.js testing utilities
**Test Location:** `tests/unit/components/`
**Minimum Iterations:** 100 per property-based test

**Test Coverage:**

1. **Dashboard Component**
   - State initialization
   - Date navigation logic
   - Slot click handling
   - Grid rendering
   - User reservations loading

2. **Booking Modal Component**
   - Open/close behavior
   - Form validation
   - Submission handling
   - Error display
   - State reset

3. **Favourites Store**
   - Load favourites
   - Add favourite
   - Remove favourite
   - Store reactivity

4. **Reservations Component**
   - Load reservations
   - Cancel reservation
   - Filter logic
   - Date/time formatting

**Example Component Test:**
```javascript
import { test, expect } from 'vitest';
import Alpine from 'alpinejs';
import { dashboard } from '../../../app/static/js/components/dashboard.js';

test('dashboard initializes with today\'s date', () => {
    const component = dashboard();
    component.init();
    
    const today = new Date().toISOString().split('T')[0];
    expect(component.selectedDate).toBe(today);
});

test('changeDate updates selectedDate correctly', () => {
    const component = dashboard();
    component.selectedDate = '2025-01-15';
    
    component.changeDate(1);
    expect(component.selectedDate).toBe('2025-01-16');
    
    component.changeDate(-1);
    expect(component.selectedDate).toBe('2025-01-15');
});
```

### 3. Unit Tests (Vitest)

**Test Framework:** Vitest
**Test Location:** `tests/unit/utils/`
**Minimum Iterations:** 100 per property-based test

**Test Coverage:**

1. **Utility Functions**
   - Date formatting
   - Time calculations
   - API helpers
   - Validation functions

2. **API Interaction Functions**
   - Request formatting
   - Response parsing
   - Error handling

**Example Unit Test:**
```javascript
import { test, expect } from 'vitest';
import { formatDate, formatTime } from '../../../app/static/js/utils.js';

test('formatDate converts ISO date to German format', () => {
    expect(formatDate('2025-01-15')).toBe('15.01.2025');
    expect(formatDate('2025-12-31')).toBe('31.12.2025');
});

test('formatTime formats time correctly', () => {
    expect(formatTime('09:00')).toBe('09:00');
    expect(formatTime('14:30')).toBe('14:30');
});
```

### Test Configuration

**Vitest Configuration (`vitest.config.js`):**
```javascript
import { defineConfig } from 'vitest/config';

export default defineConfig({
    test: {
        environment: 'jsdom',
        globals: true,
        setupFiles: ['./tests/setup.js'],
        coverage: {
            provider: 'v8',
            reporter: ['text', 'json', 'html'],
            exclude: [
                'node_modules/',
                'tests/',
                '**/*.config.js'
            ]
        }
    }
});
```

**Playwright Configuration (`playwright.config.js`):**
```javascript
import { defineConfig } from '@playwright/test';

export default defineConfig({
    testDir: './tests/e2e',
    use: {
        baseURL: 'http://localhost:5000',
        screenshot: 'only-on-failure',
        video: 'retain-on-failure'
    },
    webServer: {
        command: 'flask run',
        port: 5000,
        reuseExistingServer: !process.env.CI
    }
});
```

### Property-Based Testing Requirements

- Each property-based test MUST run a minimum of 100 iterations
- Each property-based test MUST be tagged with: `// Feature: alpine-tdd-migration, Property {number}: {property_text}`
- Each correctness property MUST be implemented by a SINGLE property-based test
- Property-based tests will use Vitest with custom generators for test data

**Example Property-Based Test:**
```javascript
// Feature: alpine-tdd-migration, Property 1: Grid reactivity preservation
test('grid updates reactively for any date selection', async () => {
    const component = dashboard();
    
    for (let i = 0; i < 100; i++) {
        // Generate random date
        const randomDate = generateRandomDate();
        component.selectedDate = randomDate;
        
        await component.loadAvailability();
        
        // Verify grid reflects the selected date
        expect(component.availability.date).toBe(randomDate);
    }
});
```

## Migration Strategy

### Phase 1: Setup Testing Infrastructure
1. Install Vitest and Playwright
2. Configure test runners
3. Create test utilities for Alpine.js
4. Set up CI/CD integration

### Phase 2: Write Tests (TDD)
1. Write E2E tests for critical workflows
2. Write component tests for each Alpine.js component
3. Write unit tests for utility functions
4. Ensure all tests fail initially (no implementation yet)

### Phase 3: Migrate Dashboard Component
1. Create Alpine.js dashboard component
2. Implement minimal code to pass tests
3. Refactor vanilla JS grid logic to Alpine.js
4. Verify all tests pass
5. Remove old vanilla JS code

### Phase 4: Migrate Booking Modal
1. Create Alpine.js booking modal component
2. Implement form handling and validation
3. Integrate with favourites store
4. Verify all tests pass
5. Remove old vanilla JS code

### Phase 5: Complete Favourites Store
1. Enhance existing Alpine.js favourites store
2. Integrate with booking modal
3. Verify reactivity across components
4. Verify all tests pass

### Phase 6: Migrate Reservations Component
1. Enhance existing Alpine.js reservations component
2. Implement cancellation logic
3. Verify all tests pass
4. Remove old vanilla JS code

### Phase 7: Cleanup and Documentation
1. Remove all unused vanilla JS files
2. Update documentation
3. Verify 100% test coverage
4. Final E2E test run
5. Deploy to production

## File Structure

```
app/
├── static/
│   └── js/
│       ├── components/
│       │   ├── dashboard.js (new)
│       │   ├── booking-modal.js (new)
│       │   ├── favourites-store.js (new)
│       │   └── reservations.js (refactored)
│       └── utils/
│           ├── api.js (new)
│           ├── date-utils.js (new)
│           └── validators.js (new)
├── templates/
│   ├── dashboard.html (updated with Alpine directives)
│   ├── favourites.html (updated)
│   └── reservations.html (updated)
tests/
├── e2e/
│   ├── booking-workflow.spec.js
│   ├── cancellation-workflow.spec.js
│   ├── date-navigation.spec.js
│   └── favourites-integration.spec.js
├── unit/
│   ├── components/
│   │   ├── dashboard.test.js
│   │   ├── booking-modal.test.js
│   │   ├── favourites-store.test.js
│   │   └── reservations.test.js
│   └── utils/
│       ├── api.test.js
│       ├── date-utils.test.js
│       └── validators.test.js
└── setup.js
```

## Dependencies

### New Dependencies to Install

```json
{
  "devDependencies": {
    "@playwright/test": "^1.40.0",
    "vitest": "^1.0.0",
    "jsdom": "^23.0.0",
    "@vitest/ui": "^1.0.0",
    "alpinejs": "^3.13.3"
  }
}
```

### Installation Commands

```bash
npm install --save-dev @playwright/test vitest jsdom @vitest/ui
npx playwright install
```

## Performance Considerations

1. **Lazy Loading**: Load Alpine.js components only when needed
2. **Debouncing**: Debounce API calls for date navigation
3. **Caching**: Cache availability data for recently viewed dates
4. **Optimistic Updates**: Update UI immediately, sync with server in background
5. **Bundle Size**: Keep Alpine.js components modular to minimize bundle size

## Security Considerations

1. **XSS Prevention**: Use Alpine.js text binding (x-text) instead of HTML binding where possible
2. **CSRF Protection**: Include CSRF tokens in all API requests
3. **Input Validation**: Validate all user inputs on both client and server
4. **Authorization**: Verify user permissions before allowing actions
5. **Error Messages**: Don't expose sensitive information in error messages

## Accessibility

1. **Keyboard Navigation**: Ensure all interactive elements are keyboard accessible
2. **ARIA Labels**: Add appropriate ARIA labels to dynamic content
3. **Focus Management**: Manage focus when opening/closing modals
4. **Screen Reader Support**: Announce dynamic updates to screen readers
5. **Color Contrast**: Maintain WCAG AA compliance for all color combinations

## Browser Compatibility

- Chrome/Edge: Latest 2 versions
- Firefox: Latest 2 versions
- Safari: Latest 2 versions
- Mobile browsers: iOS Safari, Chrome Android

Alpine.js supports all modern browsers with ES6 support.
