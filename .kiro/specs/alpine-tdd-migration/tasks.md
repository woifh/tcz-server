# Implementation Plan: Alpine.js TDD Migration

- [x] 1. Set up testing infrastructure
  - Install Vitest, Playwright, and testing dependencies
  - Configure Vitest for component and unit testing
  - Configure Playwright for E2E testing
  - Create test setup files and utilities for Alpine.js testing
  - _Requirements: 6.1, 6.2, 6.3_

- [x] 2. Write E2E tests for dashboard and booking workflow (TDD)
  - [x] 2.1 Write E2E test for complete booking workflow
    - Test: Navigate to dashboard, select date, click available slot, fill form, submit, verify success
    - _Requirements: 3.1_
  
  - [x] 2.2 Write E2E test for cancellation workflow
    - Test: Navigate to dashboard, click own reservation, confirm cancellation, verify grid updates
    - _Requirements: 3.2_
  
  - [x] 2.3 Write E2E test for date navigation
    - Test: Click previous/next day buttons, click "Heute" button, verify grid updates
    - _Requirements: 3.3_
  
  - [x] 2.4 Write E2E test for error handling
    - Test: Attempt to book reserved slot, attempt to book blocked slot, verify error messages
    - _Requirements: 3.4_
  
  - [x] 2.5 Write E2E test for favourites integration
    - Test: Add favourite, open booking modal, verify favourite in dropdown, book for favourite
    - _Requirements: 3.5_

- [x] 3. Create Alpine.js dashboard component with TDD
  - [x] 3.1 Write unit tests for dashboard component
    - Test state initialization, date navigation, slot click handling, grid rendering
    - _Requirements: 4.1_
  
  - [x] 3.2 Implement dashboard component structure
    - Create `app/static/js/components/dashboard.js`
    - Define component state and methods
    - _Requirements: 1.1_
  
  - [x] 3.3 Implement date navigation logic
    - Implement changeDate(), goToToday() methods
    - _Requirements: 1.2_
  
  - [x] 3.4 Implement availability grid loading
    - Implement loadAvailability() with API integration
    - _Requirements: 1.1, 1.2_
  
  - [x] 3.5 Implement slot click handling
    - Implement handleSlotClick() for available slots and user reservations
    - _Requirements: 1.3, 1.4_
  
  - [x] 3.6 Implement slot styling logic
    - Implement getSlotClass() for color coding
    - _Requirements: 1.5_
  
  - [ ]* 3.7 Write property test for grid reactivity
    - **Property 1: Grid reactivity preservation**
    - **Validates: Requirements 1.2**
  
  - [ ]* 3.8 Write property test for slot color coding
    - **Property 10: Slot color coding accuracy**
    - **Validates: Requirements 1.5**

- [x] 4. Update dashboard template with Alpine.js directives
  - Replace vanilla JS event handlers with Alpine.js directives (x-data, x-model, @click, etc.)
  - Update `app/templates/dashboard.html`
  - Remove references to old vanilla JS files
  - _Requirements: 5.3_

- [x] 5. Create Alpine.js booking modal component with TDD
  - [x] 5.1 Write unit tests for booking modal component
    - Test open/close behavior, form validation, submission, error handling
    - _Requirements: 4.2_
  
  - [x] 5.2 Implement booking modal component structure
    - Create `app/static/js/components/booking-modal.js`
    - Define component state and methods
    - _Requirements: 2.1_
  
  - [x] 5.3 Implement modal open/close logic
    - Implement open(), close(), reset() methods
    - _Requirements: 2.1, 2.5_
  
  - [x] 5.4 Implement form validation
    - Implement validate() method
    - _Requirements: 2.2_
  
  - [x] 5.5 Implement form submission with API integration
    - Implement submit() method with error handling
    - _Requirements: 2.2, 2.3, 2.4_
  
  - [x] 5.6 Integrate with favourites store
    - Load favourites into booking modal dropdown
    - _Requirements: 2.1, 7.4_
  
  - [ ]* 5.7 Write property test for modal data consistency
    - **Property 2: Booking modal data consistency**
    - **Validates: Requirements 2.1**
  
  - [ ]* 5.8 Write property test for form validation
    - **Property 7: Form validation consistency**
    - **Validates: Requirements 2.2, 8.4**
  
  - [ ]* 5.9 Write property test for modal escape handling
    - **Property 9: Modal escape handling**
    - **Validates: Requirements 2.5**

- [x] 6. Update booking modal template with Alpine.js directives
  - Replace vanilla JS modal logic with Alpine.js directives
  - Update modal in `app/templates/dashboard.html`
  - _Requirements: 5.3_

- [x] 7. Enhance Alpine.js favourites store with TDD
  - [x] 7.1 Write unit tests for favourites store
    - Test load, add, remove operations and reactivity
    - _Requirements: 4.3_
  
  - [x] 7.2 Implement favourites store enhancements
    - Create/enhance `app/static/js/components/favourites-store.js`
    - Implement load(), add(), remove() methods
    - _Requirements: 7.1, 7.2, 7.3_
  
  - [x] 7.3 Integrate favourites store with booking modal
    - Ensure booking modal consumes favourites from store
    - _Requirements: 7.4_
  
  - [ ]* 7.4 Write property test for favourites store synchronization
    - **Property 4: Favourites store synchronization**
    - **Validates: Requirements 7.2, 7.3**

- [x] 8. Update favourites template with Alpine.js directives
  - Ensure favourites page uses Alpine.js store
  - Update `app/templates/favourites.html` if needed
  - _Requirements: 7.1, 7.5_

- [x] 9. Enhance Alpine.js reservations component with TDD
  - [x] 9.1 Write unit tests for reservations component
    - Test load, cancel, filter operations
    - _Requirements: 4.4_
  
  - [x] 9.2 Implement reservations component enhancements
    - Enhance existing component in `app/templates/reservations.html`
    - Implement load(), cancel() methods
    - _Requirements: 1.4_
  
  - [ ]* 9.3 Write property test for cancellation authorization
    - **Property 3: Reservation cancellation authorization**
    - **Validates: Requirements 1.4**

- [x] 10. Create utility modules with TDD
  - [x] 10.1 Write unit tests for API utilities
    - Test request formatting, response parsing, error handling
    - _Requirements: 4.4_
  
  - [x] 10.2 Implement API utility module
    - Create `app/static/js/utils/api.js`
    - Implement fetch wrappers with error handling
    - _Requirements: 8.1, 8.3_
  
  - [x] 10.3 Write unit tests for date utilities
    - Test date formatting, calculations
    - _Requirements: 4.5_
  
  - [x] 10.4 Implement date utility module
    - Create `app/static/js/utils/date-utils.js`
    - Implement formatDate(), formatTime() functions
    - _Requirements: 1.2_
  
  - [x] 10.5 Write unit tests for validators
    - Test validation functions
    - _Requirements: 4.5_
  
  - [x] 10.6 Implement validator module
    - Create `app/static/js/utils/validators.js`
    - Implement validation functions
    - _Requirements: 2.2, 8.4_
  
  - [ ]* 10.7 Write property test for API failure recovery
    - **Property 6: API failure recovery**
    - **Validates: Requirements 8.3**

- [x] 11. Implement error handling across components
  - [x] 11.1 Add error state to all components
    - Add error property and formatError() method to each component
    - _Requirements: 8.1, 8.2_
  
  - [x] 11.2 Implement error display in templates
    - Add error message displays to all templates
    - _Requirements: 8.1_
  
  - [x] 11.3 Add retry mechanisms for failed requests
    - Implement retry logic in API utility
    - _Requirements: 8.3_
  
  - [ ]* 11.4 Write property test for error state isolation
    - **Property 5: Error state isolation**
    - **Validates: Requirements 8.2**

- [x] 12. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 13. Remove old vanilla JavaScript files
  - Delete `app/static/js/app.js`
  - Delete `app/static/js/booking.js`
  - Delete `app/static/js/grid.js`
  - Delete `app/static/js/app-bundle.js`
  - Keep `app/static/js/utils.js` if still needed, otherwise delete
  - _Requirements: 5.2_

- [x] 14. Update HTML templates to remove old script references
  - Remove script tags referencing deleted vanilla JS files
  - Ensure all templates use Alpine.js components
  - _Requirements: 5.3_

- [x] 15. Run full test suite and verify coverage
  - [x] 15.1 Run all E2E tests
    - Execute Playwright tests and verify all pass
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_
  
  - [x] 15.2 Run all component and unit tests
    - Execute Vitest tests and verify all pass
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_
  
  - [x] 15.3 Generate and review coverage report
    - Ensure adequate test coverage
    - _Requirements: 6.4_

- [x] 16. Verify no regressions and user experience
  - [x] 16.1 Manual testing of all workflows
    - Test booking, cancellation, date navigation, favourites
    - _Requirements: 5.1, 5.4_
  
  - [x] 16.2 Check browser console for errors
    - Verify no console errors or warnings
    - _Requirements: 5.5_
  
  - [x] 16.3 Test on multiple browsers
    - Test on Chrome, Firefox, Safari
    - _Requirements: 5.1_

- [x] 17. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 18. Update documentation
  - Update README.md with new testing information
  - Document Alpine.js component architecture
  - Add developer guide for writing Alpine.js components
  - _Requirements: 5.1_
