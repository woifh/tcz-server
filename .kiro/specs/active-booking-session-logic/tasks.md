# Implementation Plan: Active Booking Session Logic

## Overview

This implementation plan converts the active booking session logic design into discrete coding tasks. The enhancement refines the tennis club reservation system's approach to determining which reservations count as "active" by using precise time-based logic instead of date-only comparisons. The implementation focuses on updating core service methods, validation logic, and display components while maintaining backward compatibility.

## Tasks

- [x] 1. Implement core time-based active booking session logic
  - Create `is_reservation_active_by_time()` utility function in ReservationService
  - Implement time comparison logic that considers current time vs reservation end time
  - Handle edge cases for exact time boundaries and timezone consistency
  - _Requirements: 1.1, 1.2, 1.3, 1.5, 5.1, 5.2, 5.3_

- [ ]* 1.1 Write property test for time-based active booking session determination
  - **Property 1: Time-based active booking session determination**
  - **Validates: Requirements 1.1, 1.2, 1.3, 1.5**

- [x] 2. Update ReservationService methods to use time-based logic
  - [x] 2.1 Enhance `get_member_active_reservations()` method
    - Update query logic to use time-based filtering instead of date-only
    - Add optional `current_time` parameter for testing
    - Maintain backward compatibility with existing method signature
    - _Requirements: 3.1_

  - [x] 2.2 Create new `get_member_active_booking_sessions()` method
    - Implement time-based active reservation filtering
    - Support include_short_notice parameter
    - Add comprehensive documentation and examples
    - _Requirements: 1.4, 2.1, 2.2_

  - [x] 2.3 Create new `get_member_active_short_notice_bookings()` method
    - Implement time-based filtering specifically for short notice bookings
    - Use same time logic as regular reservations
    - _Requirements: 2.5, 2.6_

- [ ]* 2.4 Write property test for short notice bookings excluded from active count
  - **Property 2: Short notice bookings excluded from active booking session count**
  - **Validates: Requirements 2.1, 2.2**

- [ ]* 2.5 Write property test for short notice booking limit with time-based logic
  - **Property 3: Short notice booking limit uses time-based logic**
  - **Validates: Requirements 2.5, 2.6**

- [x] 3. Update ValidationService methods to use enhanced logic
  - [x] 3.1 Update `validate_member_reservation_limit()` method
    - Replace date-based counting with time-based active booking session logic
    - Add optional `current_time` parameter for testing
    - Ensure short notice bookings remain excluded from count
    - _Requirements: 1.4, 2.2, 3.2_

  - [x] 3.2 Update `validate_member_short_notice_limit()` method
    - Replace date-based counting with time-based logic for short notice bookings
    - Add optional `current_time` parameter for testing
    - _Requirements: 2.5, 2.6, 3.2_

- [ ]* 3.3 Write property test for regular reservation limit allows short notice bookings
  - **Property 4: Regular reservation limit allows short notice bookings**
  - **Validates: Requirements 2.3**

- [ ] 4. Checkpoint - Ensure core service logic tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Update dashboard and display components
  - [x] 5.1 Update "Meine kommenden Buchungen" section logic
    - Modify dashboard template query to use time-based filtering
    - Ensure past reservations are immediately removed from upcoming list
    - Test with various time scenarios (morning, afternoon, evening)
    - _Requirements: 4.1, 4.5_

  - [x] 5.2 Update reservation count displays
    - Modify admin panel member reservation count displays
    - Update dashboard availability information
    - Ensure consistent labeling between "Active" and "Completed" reservations
    - _Requirements: 3.3, 4.2, 4.4_

- [ ]* 5.3 Write property test for consistent active booking session logic across components
  - **Property 5: Consistent active booking session logic across system components**
  - **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**

- [ ]* 5.4 Write property test for accurate display of active booking information
  - **Property 6: Accurate display of active booking information**
  - **Validates: Requirements 4.1, 4.2, 4.4, 4.5**

- [x] 6. Update API endpoints and routes
  - [x] 6.1 Update reservation listing endpoints
    - Modify GET `/reservations` to use time-based filtering
    - Update response format to include active/past status indicators
    - Maintain API backward compatibility
    - _Requirements: 3.5_

  - [x] 6.2 Update court availability endpoints
    - Ensure availability calculations use new active booking session logic
    - Update real-time availability information
    - _Requirements: 4.3_

- [ ]* 6.3 Write property test for real-time availability calculation updates
  - **Property 7: Real-time availability calculation updates**
  - **Validates: Requirements 4.3**

- [x] 7. Add timezone consistency and error handling
  - [x] 7.1 Implement consistent timezone handling
    - Ensure all time comparisons use Europe/Berlin timezone
    - Add timezone conversion utilities if needed
    - Handle daylight saving time transitions gracefully
    - _Requirements: 5.3, 5.4_

  - [x] 7.2 Add error handling and fallback behavior
    - Implement fallback to date-based logic if time calculations fail
    - Add comprehensive error logging for debugging
    - Update error messages to reflect time-based logic
    - _Requirements: Error Handling_

- [ ]* 7.3 Write property test for consistent timezone handling
  - **Property 8: Consistent timezone handling**
  - **Validates: Requirements 5.3**

- [x] 8. Integration testing and validation
  - [x] 8.1 Test integration with existing reservation workflows
    - Verify reservation creation still works correctly
    - Test cancellation logic with time-based validation
    - Ensure email notifications include correct status information
    - _Requirements: Integration_

  - [x] 8.2 Performance testing with time-based queries
    - Test query performance with large datasets
    - Add database indexes if needed for optimization
    - Verify real-time updates don't impact system performance
    - _Requirements: Performance_

- [ ]* 8.3 Write integration tests for enhanced logic with existing workflows
  - Test end-to-end reservation workflows with time-based logic
  - Verify compatibility with existing features
  - _Requirements: Integration_

- [x] 9. Final checkpoint - Ensure all tests pass and system integration works
  - Ensure all tests pass, ask the user if questions arise.
  - Verify that the "Meine kommenden Buchungen" section updates correctly as time progresses
  - Test edge cases like midnight transitions and exact time boundaries
  - Confirm that both regular and short notice booking limits work with new logic

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties using Hypothesis (Python property-based testing library)
- Unit tests validate specific examples and edge cases
- The implementation maintains backward compatibility while enhancing functionality
- Time-based logic uses Europe/Berlin timezone consistently throughout the system