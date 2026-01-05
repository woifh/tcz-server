# Implementation Plan: Block Reasons Management

## Overview

This implementation plan focuses on creating a comprehensive admin interface for managing block reasons. The backend API and services are already implemented, so we'll focus on building the frontend interface using Alpine.js and Tailwind CSS to provide administrators with an intuitive way to manage block reasons.

## Tasks

- [x] 1. Set up the basic admin reasons page structure
  - Replace the placeholder content in `app/templates/admin/reasons.html`
  - Create the main layout with header, navigation, and content areas
  - Add Alpine.js data structure for managing page state
  - _Requirements: 1.1, 6.1, 6.2_

- [x] 2. Implement the block reasons table display
  - [x] 2.1 Create the reasons table with proper columns
    - Build HTML table structure with sortable headers
    - Display reason name, usage count, created by, and created date columns
    - Add action buttons (edit, delete) for each row
    - _Requirements: 1.2, 1.3_

  - [ ]* 2.2 Write property test for block reason display completeness
    - **Property 1: Block reason display completeness**
    - **Validates: Requirements 1.2**

  - [x] 2.3 Implement data loading from the API
    - Add Alpine.js method to fetch reasons from `/admin/block-reasons`
    - Handle loading states and error conditions
    - Populate table with fetched data
    - _Requirements: 1.1, 5.2_

  - [ ]* 2.4 Write property test for usage count accuracy
    - **Property 2: Usage count accuracy**
    - **Validates: Requirements 1.3, 5.2**

- [x] 3. Implement block reason creation functionality
  - [x] 3.1 Create the "Add New Reason" modal
    - Build modal dialog with form fields
    - Add form validation for required fields
    - Implement cancel and submit actions
    - _Requirements: 2.1, 2.5_

  - [x] 3.2 Implement reason creation logic
    - Add Alpine.js method to submit new reasons to API
    - Handle success and error responses
    - Refresh the reasons list after successful creation
    - _Requirements: 2.4, 2.5_

  - [ ]* 3.3 Write property test for unique name validation during creation
    - **Property 3: Unique name validation during creation**
    - **Validates: Requirements 2.2, 2.3**

  - [ ]* 3.4 Write property test for valid reason creation
    - **Property 4: Valid reason creation**
    - **Validates: Requirements 2.4**

- [x] 4. Checkpoint - Ensure basic functionality works
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Implement inline editing functionality
  - [x] 5.1 Add inline editing to reason names
    - Convert reason name cells to editable inputs on click
    - Add save/cancel buttons for inline editing
    - Handle keyboard shortcuts (Enter to save, Escape to cancel)
    - _Requirements: 3.1, 3.5_

  - [x] 5.2 Implement reason update logic
    - Add Alpine.js method to update reasons via API
    - Handle validation errors and success responses
    - Revert to display mode after successful update
    - _Requirements: 3.4, 3.5_

  - [ ]* 5.3 Write property test for unique name validation during editing
    - **Property 5: Unique name validation during editing**
    - **Validates: Requirements 3.2, 3.3**

  - [ ]* 5.4 Write property test for historical preservation during updates
    - **Property 6: Historical preservation during updates**
    - **Validates: Requirements 3.4**

- [x] 6. Implement deletion functionality with usage protection
  - [x] 6.1 Create delete confirmation modal
    - Build confirmation dialog with usage impact explanation
    - Show different messages for used vs unused reasons
    - Add confirm/cancel actions
    - _Requirements: 4.5_

  - [x] 6.2 Implement deletion logic
    - Add Alpine.js method to delete reasons via API
    - Handle both deletion and deactivation responses
    - Update the reasons list after successful operation
    - _Requirements: 4.1, 4.2, 4.3, 4.4_

  - [ ]* 6.3 Write property test for usage-based deletion behavior
    - **Property 7: Usage-based deletion behavior**
    - **Validates: Requirements 4.1, 4.2, 4.3**

  - [ ]* 6.4 Write property test for future block cleanup during deactivation
    - **Property 8: Future block cleanup during deactivation**
    - **Validates: Requirements 4.4**

- [x] 7. Implement error handling and user feedback
  - [x] 7.1 Add toast notification system
    - Create reusable toast component for success/error messages
    - Implement auto-dismiss for success messages
    - Keep error messages visible until user dismissal
    - _Requirements: 8.1, 8.2, 8.5_

  - [x] 7.2 Add comprehensive error handling
    - Handle network errors with retry suggestions
    - Display specific validation error messages
    - Implement loading states for all operations
    - _Requirements: 8.2, 8.3_

  - [ ]* 7.3 Write property test for success message display
    - **Property 11: Success message display**
    - **Validates: Requirements 8.1**

  - [ ]* 7.4 Write property test for validation error messaging
    - **Property 12: Validation error messaging**
    - **Validates: Requirements 8.2**

- [x] 8. Implement input validation and security
  - [x] 8.1 Add client-side input validation
    - Validate reason names for appropriate characters
    - Enforce length limits and required fields
    - Provide real-time validation feedback
    - _Requirements: 9.1, 9.4_

  - [x] 8.2 Implement input sanitization
    - Sanitize all form inputs before submission
    - Prevent XSS and injection attacks
    - Validate data types and formats
    - _Requirements: 9.2, 9.5_

  - [ ]* 8.3 Write property test for input character validation
    - **Property 13: Input character validation**
    - **Validates: Requirements 9.1, 9.4**

  - [ ]* 8.4 Write property test for input sanitization
    - **Property 14: Input sanitization**
    - **Validates: Requirements 9.2**

- [x] 9. Add responsive design and accessibility
  - [x] 9.1 Implement responsive table layout
    - Make table responsive for mobile devices
    - Stack or hide less critical columns on small screens
    - Ensure touch targets are appropriately sized
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

  - [x] 9.2 Add accessibility features
    - Include proper ARIA labels and roles
    - Ensure keyboard navigation works properly
    - Add screen reader support for dynamic content
    - _Requirements: 7.4, 7.5_

- [ ] 10. Implement security and access control testing
  - [ ]* 10.1 Write property test for administrator access control
    - **Property 9: Administrator access control**
    - **Validates: Requirements 6.1, 6.2, 6.3**

  - [ ]* 10.2 Write property test for comprehensive audit logging
    - **Property 10: Comprehensive audit logging**
    - **Validates: Requirements 6.4, 6.5**

  - [ ]* 10.3 Write property test for transaction rollback consistency
    - **Property 15: Transaction rollback consistency**
    - **Validates: Requirements 9.3**

  - [ ]* 10.4 Write property test for system conflict prevention
    - **Property 16: System conflict prevention**
    - **Validates: Requirements 9.5**

- [x] 11. Final integration and testing
  - [x] 11.1 Add sorting and filtering capabilities
    - Implement column sorting for all table columns
    - Add search/filter functionality for reason names
    - Maintain sort state during operations
    - _Requirements: 1.1, 1.2_

  - [x] 11.2 Optimize performance and user experience
    - Add loading spinners for all async operations
    - Implement optimistic UI updates where appropriate
    - Cache API responses to reduce server load
    - _Requirements: 8.1, 8.3_

  - [ ]* 11.3 Write integration tests for complete workflows
    - Test complete create-edit-delete workflows
    - Test error recovery scenarios
    - Test concurrent user scenarios

- [x] 12. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## ADMIN NAVIGATION FIXES

- [x] 13. Fix admin panel navigation
  - [x] 13.1 Update overview cards to link to dedicated pages
    - Changed "Sperrungsgründe" card to link to `/admin/reasons`
    - Updated other cards to link to their respective dedicated pages
    - _Fixed: Users now go to proper Alpine.js-based interfaces_

  - [x] 13.2 Update tab navigation system
    - Converted old tab buttons to proper navigation links
    - Removed legacy tab content sections (blocks, recurring, templates, reasons, members)
    - Kept only overview and calendar tabs (calendar still uses tab system)
    - Updated JavaScript to handle simplified navigation
    - _Fixed: Users are properly directed to dedicated pages instead of old tab system_

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
- The backend API and services are already implemented and tested
- Focus is on creating a polished, user-friendly frontend interface
- **NAVIGATION ISSUE RESOLVED**: Admin panel now properly directs users to dedicated Alpine.js-based pages instead of legacy tab system