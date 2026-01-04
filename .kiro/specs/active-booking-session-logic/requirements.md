# Requirements Document

## Introduction

This document specifies the requirements for enhancing the active booking session logic in the tennis club reservation system. The current system considers all reservations with status='active' and date >= today as "active reservations" for the purpose of the 2-reservation limit. This enhancement refines the logic to consider the actual current time and exclude short-term reservations from the active count, providing more accurate booking availability.

## Glossary

- **System**: The tennis club court reservation web application
- **Active Booking Session**: A reservation that is either in the future or currently in progress (started but not yet ended) and counts toward the member's reservation limit
- **Current Time**: The actual current date and time when the system evaluates reservation status
- **Regular Reservation**: A standard court booking that counts toward the 2-reservation limit
- **Short Notice Booking**: A reservation created within 15 minutes of the slot start time that does not count toward the member's active reservation limit
- **Reservation Time Window**: The one-hour period from start_time to end_time of a reservation
- **Past Reservation**: A reservation whose end time has already passed and no longer counts as active
- **Future Reservation**: A reservation whose start time is after the current time and counts as active
- **Current Reservation**: A reservation that has started but not yet ended and counts as active

## Requirements

### Requirement 1

**User Story:** As a system administrator, I want the active booking session logic to consider actual time instead of just date, so that the 2-reservation limit is enforced more accurately based on when reservations are actually in use.

#### Acceptance Criteria

1. WHEN the current time is before a reservation's start time, THE System SHALL count that reservation as an active booking session
2. WHEN the current time is during a reservation's time window (between start_time and end_time), THE System SHALL count that reservation as an active booking session
3. WHEN the current time is after a reservation's end time, THE System SHALL not count that reservation as an active booking session
4. WHEN evaluating the 2-reservation limit, THE System SHALL only count reservations that qualify as active booking sessions
5. THE System SHALL use the actual current date and time for all active booking session evaluations

### Requirement 2

**User Story:** As a club member, I want short notice bookings to be excluded from the active booking session count, so that they don't interfere with my regular reservation planning.

#### Acceptance Criteria

1. WHEN a reservation has is_short_notice=true, THE System SHALL not count it as an active booking session regardless of its timing
2. WHEN calculating the 2-reservation limit, THE System SHALL exclude all short notice bookings from the active count
3. WHEN a member has 2 regular active booking sessions, THE System SHALL still allow creation of short notice bookings
4. WHEN displaying active reservations to users, THE System SHALL clearly distinguish between regular and short notice bookings
5. WHEN evaluating the 1 short notice booking limit, THE System SHALL only count short notice bookings that are currently active (future or in progress) using the same time-based logic as regular reservations
6. WHEN a member's short notice booking has ended (current time is after the end time), THE System SHALL allow the member to create another short notice booking

### Requirement 3

**User Story:** As a system developer, I want the active booking session logic to be consistently applied across all system components, so that reservation limits are enforced uniformly.

#### Acceptance Criteria

1. WHEN the ReservationService.get_member_active_reservations() method is called, THE System SHALL return only reservations that qualify as active booking sessions
2. WHEN the ValidationService.validate_member_reservation_limit() method is called, THE System SHALL use the active booking session logic to count reservations
3. WHEN the admin panel displays member reservation counts, THE System SHALL show active booking session counts using the new logic
4. WHEN the dashboard shows "My Reservations", THE System SHALL distinguish between active booking sessions and past reservations
5. THE System SHALL update all existing methods that rely on active reservation counts to use the new active booking session logic

### Requirement 4

**User Story:** As a club member, I want to see accurate information about my current booking status, so that I understand how many reservation slots I have available.

#### Acceptance Criteria

1. WHEN a member views their reservation dashboard, THE System SHALL display the count of active booking sessions separately from past reservations
2. WHEN a member attempts to create a new reservation, THE System SHALL show an accurate count of current active booking sessions
3. WHEN a reservation transitions from active to past (end time passes), THE System SHALL immediately reflect this change in availability calculations
4. WHEN displaying reservation status, THE System SHALL use clear labels to distinguish between "Active" (future/current) and "Completed" (past) reservations
5. WHEN displaying the "Meine kommenden Buchungen" (My Upcoming Reservations) section, THE System SHALL only show reservations that are currently active (future or in progress) and SHALL not display past reservations
6. THE System SHALL provide real-time updates to active booking session counts as time progresses

### Requirement 5

**User Story:** As a system operator, I want the active booking session logic to handle edge cases correctly, so that the system behaves predictably in all scenarios.

#### Acceptance Criteria

1. WHEN the current time exactly matches a reservation's start time, THE System SHALL count it as an active booking session
2. WHEN the current time exactly matches a reservation's end time, THE System SHALL not count it as an active booking session
3. WHEN evaluating reservations across different time zones, THE System SHALL use consistent timezone handling for all time comparisons
4. WHEN the system clock changes (daylight saving time), THE System SHALL handle active booking session calculations correctly
5. WHEN a reservation spans midnight (21:00-22:00 on the last booking slot), THE System SHALL correctly evaluate its active status
