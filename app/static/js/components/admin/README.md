# Admin Panel Module Structure

This directory contains the refactored admin panel code, organized into modular components for better maintainability and code organization.

## Directory Structure

```
admin/
├── admin-main.js           # Main entry point and coordinator
├── core/                   # Core functionality and utilities
│   ├── admin-api.js       # API client for backend communication
│   ├── admin-constants.js # Shared constants and configuration
│   ├── admin-state.js     # Global state management
│   ├── admin-utils.js     # Utility functions (dates, forms, toast)
│   ├── blocks-manager.js  # Block operations and batch management
│   └── ui-helpers.js      # UI utilities (tabs, modals, colors)
├── forms/                  # Form components
│   ├── block-form.js      # Multi-court block creation/editing
│   └── reason-form.js     # Block reason management
├── filtering/              # Filtering functionality
│   └── block-filters.js   # Block list filtering
├── calendar/               # Calendar view
│   └── calendar-view.js   # Monthly calendar display
└── modals/                 # Modal components (if needed)
```

## Module Descriptions

### Core Modules

#### `admin-main.js`
- Main entry point that initializes all components
- Coordinates communication between modules
- Sets up global functions for HTML onclick handlers
- Handles initial data loading

#### `core/admin-api.js`
- Centralized API client for all backend requests
- Provides typed API methods for:
  - Block reasons (load, create, update, delete)
  - Blocks (load, create, update, delete, get)
  - Conflict preview
  - Audit log

#### `core/admin-state.js`
- Global state management using singleton pattern
- Manages:
  - Block reasons list
  - Current filters
  - Calendar date
  - Selected blocks

#### `core/admin-utils.js`
- Utility functions used across modules:
  - `showToast()` - Toast notification system
  - `dateUtils` - Date/time formatting and validation
  - `formUtils` - Form validation helpers
  - `domUtils` - DOM manipulation helpers

#### `core/blocks-manager.js`
- Block management operations:
  - Load and display upcoming blocks
  - Group blocks by batch
  - Delete batch with confirmation modal
  - Duplicate blocks
  - Batch operations

#### `core/ui-helpers.js`
- UI utilities:
  - `showTab()` - Tab management
  - `modalUtils` - Modal creation and management
  - `getReasonColor()` - Color coding for block reasons
  - `loadingUtils` - Loading states and messages
  - `KeyboardShortcuts` - Keyboard shortcut registration

### Form Modules

#### `forms/block-form.js`
- Multi-court block form management
- Form validation (courts, dates, times, reasons)
- Submit handlers for create and update
- Edit mode population
- "Save as New" functionality

#### `forms/reason-form.js`
- Block reason CRUD operations
- Reason list display
- Reason editing modal
- Deletion with usage warnings

### Filtering Module

#### `filtering/block-filters.js`
- Block list filtering functionality
- Advanced filter modal
- Filter state persistence (localStorage)
- Dynamic filter updates with debouncing

### Calendar Module

#### `calendar/calendar-view.js`
- Monthly calendar view
- Block visualization by day
- Month navigation
- Day details modal
- Color-coded reason display

## Usage

### Initialization

The admin panel is automatically initialized when the page loads:

```javascript
// In HTML template
<script type="module" src="{{ url_for('static', filename='js/components/admin/admin-main.js') }}"></script>
```

### Accessing Components

Components are made globally available for use in HTML templates:

```javascript
// Global window objects:
window.blocksManager   // Block operations
window.blockForm       // Form management
window.reasonForm      // Reason management
window.blockFilters    // Filtering
window.calendarView    // Calendar display
window.showTab         // Tab navigation
window.modalUtils      // Modal utilities
```

### Example: Using in HTML

```html
<!-- Delete button -->
<button onclick="window.blocksManager.deleteBatch('batch_123')">Delete</button>

<!-- Tab navigation -->
<button onclick="window.showTab('calendar')">Calendar</button>

<!-- Show modal -->
<button onclick="window.modalUtils.showConfirmation('Title', 'Message', () => console.log('Confirmed'))">
  Confirm Action
</button>
```

## Module Communication

Modules communicate through:

1. **State Manager** - Shared state via `stateManager`
2. **Event System** - Custom events (planned for future)
3. **Direct Imports** - ES6 module imports
4. **Global Window** - For HTML onclick handlers only

## Best Practices

### Adding New Functionality

1. Identify the appropriate module (core, forms, filtering, calendar)
2. Add the function to that module
3. Export the function if needed by other modules
4. Add to global scope in `admin-main.js` if needed in HTML

### Creating New Modules

1. Create file in appropriate directory
2. Use ES6 module syntax (`export class/function`)
3. Import dependencies at the top
4. Export singleton instance if needed
5. Add import to `admin-main.js`

### Naming Conventions

- **Classes**: PascalCase (e.g., `BlocksManager`)
- **Functions**: camelCase (e.g., `loadUpcomingBlocks`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `GERMAN_TEXT`)
- **Files**: kebab-case (e.g., `blocks-manager.js`)

## Migration from admin-enhanced.js

The original `admin-enhanced.js` (1933 lines) has been refactored into smaller, focused modules:

| Original Function | New Location |
|------------------|--------------|
| `initializeAdminPanel()` | `admin-main.js` → `AdminPanel.initialize()` |
| `loadBlockReasons()` | `forms/reason-form.js` → `ReasonForm.loadReasons()` |
| `handleMultiCourtSubmit()` | `forms/block-form.js` → `BlockForm.handleSubmit()` |
| `applyFilters()` | `filtering/block-filters.js` → `BlockFilters.applyFilters()` |
| `renderCalendarView()` | `calendar/calendar-view.js` → `CalendarView.renderCalendar()` |
| `deleteBatch()` | `core/blocks-manager.js` → `BlocksManager.deleteBatch()` |
| `showToast()` | `core/admin-utils.js` → `showToast()` |
| `getReasonColor()` | `core/ui-helpers.js` → `getReasonColor()` |
| `showTab()` | `core/ui-helpers.js` → `showTab()` |

## Testing

Each module can be tested independently:

```javascript
// Example: Testing blocks-manager
import { blocksManager } from './core/blocks-manager.js';

// Test loading blocks
await blocksManager.loadUpcomingBlocks();

// Test grouping
const groups = blocksManager.groupBlocksByBatch(testBlocks);
```

## Future Improvements

- [ ] Add TypeScript for type safety
- [ ] Implement event system for module communication
- [ ] Add unit tests for each module
- [ ] Create separate modal components
- [ ] Add error boundary handling
- [ ] Implement lazy loading for calendar/filters
- [ ] Add webpack bundling for production

## Maintenance

When updating modules:

1. Update the module file
2. Update this README if structure changes
3. Test affected functionality
4. Update global exports in `admin-main.js` if needed
5. Check for breaking changes in dependent modules
