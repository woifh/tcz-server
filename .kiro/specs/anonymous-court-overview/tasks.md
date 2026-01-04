# Implementation Plan: Anonymous Court Overview

## Overview

This implementation plan converts the anonymous court overview design into discrete coding tasks. The approach focuses on creating a secure, privacy-protected public view of court availability while maintaining all existing functionality for authenticated users.

## Tasks

- [x] 1. Create anonymous data filtering service
  - Create `app/services/anonymous_filter_service.py` with `AnonymousDataFilter` class
  - Implement `filter_availability_data()` method to remove member information from court availability data
  - Ensure block information (reasons, details) remains visible to anonymous users
  - _Requirements: 2.1, 2.2, 2.3, 3.1, 3.2, 5.2_

- [ ]* 1.1 Write property test for anonymous data filtering
  - **Property 1: Anonymous Data Privacy**
  - **Validates: Requirements 2.1, 2.2, 2.3**

- [x] 2. Modify court availability endpoint for dual access
  - Update `app/routes/courts.py` to remove `@login_required` decorator from `get_availability()` 
  - Add logic to detect anonymous vs authenticated users using `current_user.is_authenticated`
  - Integrate `AnonymousDataFilter` to filter data for anonymous users
  - Maintain existing functionality for authenticated users
  - _Requirements: 1.2, 5.2, 6.1_

- [ ]* 2.1 Write property test for availability data consistency
  - **Property 3: Availability Data Consistency**
  - **Validates: Requirements 6.1, 6.4, 6.5**

- [ ]* 2.2 Write property test for block information consistency
  - **Property 2: Block Information Consistency**
  - **Validates: Requirements 3.1, 3.2, 3.3**

- [x] 3. Create anonymous dashboard route and template
  - Add new route `/overview` in `app/routes/dashboard.py` for anonymous court overview
  - Create `app/templates/anonymous_overview.html` template based on existing dashboard
  - Remove booking functionality, "My Reservations" section, and interactive elements
  - Maintain date navigation controls, legend, and court availability grid
  - Add login prompts and links to registration/login pages
  - _Requirements: 1.1, 1.3, 2.4, 4.1, 4.2, 4.5_

- [ ]* 3.1 Write unit test for anonymous template rendering
  - Test that anonymous template contains required elements (legend, navigation, login links)
  - Test that anonymous template excludes authenticated-only sections
  - _Requirements: 1.3, 2.4, 4.1, 4.2, 4.5_

- [x] 4. Implement root route handler
  - Add root route `/` handler in main application (`app/__init__.py` or new blueprint)
  - Redirect authenticated users to existing dashboard (`/dashboard`)
  - Redirect anonymous users to new anonymous overview (`/overview`)
  - _Requirements: 1.1_

- [ ]* 4.1 Write unit test for root route redirection
  - Test authenticated user redirection to dashboard
  - Test anonymous user redirection to overview
  - _Requirements: 1.1_

- [x] 5. Modify frontend JavaScript for anonymous users
  - Update `app/static/js/components/dashboard.js` to detect authentication status
  - Remove click handlers and hover effects for anonymous users
  - Maintain date navigation functionality for anonymous users
  - Ensure grid updates work correctly for anonymous users
  - _Requirements: 1.4, 1.5, 4.3, 4.4_

- [ ]* 5.1 Write property test for read-only interface enforcement
  - **Property 5: Read-Only Interface Enforcement**
  - **Validates: Requirements 4.3, 4.4**

- [ ]* 5.2 Write property test for date navigation functionality
  - **Property 4: Date Navigation Functionality**
  - **Validates: Requirements 1.4, 1.5**

- [x] 6. Add rate limiting for anonymous users
  - Configure rate limiting specifically for anonymous access to availability endpoint
  - Ensure rate limits are appropriate to prevent abuse while allowing normal usage
  - Add logging for anonymous access patterns
  - _Requirements: 5.1, 5.3_

- [ ]* 6.1 Write unit test for rate limiting
  - Test that rate limiting is applied to anonymous users
  - Test that appropriate HTTP 429 responses are returned when limits exceeded
  - _Requirements: 5.1_

- [ ] 7. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. Update navigation and authentication flow
  - Modify base template or navigation to include links to public overview
  - Ensure login/logout flows work correctly with new routing structure
  - Update any hardcoded redirects that might conflict with new routes
  - _Requirements: 4.5_

- [ ]* 8.1 Write integration test for authentication flow
  - Test complete user journey from anonymous access to login to authenticated access
  - Test logout flow returns to appropriate anonymous state
  - _Requirements: 4.5_

- [x] 9. Security and performance validation
  - Verify no sensitive data leakage in anonymous responses through manual testing
  - Test error handling for anonymous users (invalid dates, system errors)
  - Validate performance impact of data filtering
  - _Requirements: 5.2, 5.4_

- [ ]* 9.1 Write property test for server-side data filtering
  - **Property 6: Server-Side Data Filtering**
  - **Validates: Requirements 5.2**

- [ ] 10. Final checkpoint - Complete system validation
  - Ensure all tests pass, ask the user if questions arise.
  - Verify anonymous users can access court overview without authentication
  - Verify authenticated users retain all existing functionality
  - Confirm member privacy is protected in anonymous access

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
- The implementation maintains backward compatibility with existing authenticated functionality