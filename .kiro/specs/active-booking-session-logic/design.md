# Design Document

## Overview

The Active Booking Session Logic enhancement refines the tennis club reservation system's approach to determining which reservations count as "active" for the purpose of enforcing booking limits. Instead of the current date-based approach (`date >= today`), the system will use precise time-based logic that considers whether a reservation is currently in progress or scheduled for the future.

This enhancement affects the core business logic for reservation limits, ensuring that members can make new bookings as soon as their current reservations end, rather than waiting until the next day. The change applies to both regular reservations (2-reservation limit) and short notice bookings (1-booking limit).

## Architecture

### Current vs Enhanced Logic

**Current Logic:**
```python
# Current approach - date-based only
active_reservations = Reservation.query.filter(
    Reservation.booked_for_id == member_id,
    Reservation.status == 'active',
    Reservation.date >= today,  # Only considers date
    Reservation.is_short_notice == False
).count()
```

**Enhanced Logic:**
```python
# Enhanced approach - time-based
current_datetime = datetime.now()
active_reservations = Reservation.query.filter(
    Reservation.booked_for_id == member_id,
    Reservation.status == 'active',
    # Reservation is active if it hasn't ended yet
    or_(
        Reservation.date > current_datetime.date(),  # Future date
        and_(
            Reservation.date == current_datetime.date(),  # Same date
            Reservation.end_time > current_datetime.time()  # But hasn't ended
        )
    ),
    Reservation.is_short_notice == False
).count()
```

### System Components Affected

1. **ReservationService**: Core business logic for active reservation queries
2. **ValidationService**: Reservation limit validation logic
3. **Dashboard Views**: Display of active vs past reservations (especially "Meine kommenden Buchungen")
4. **Admin Panel**: Member reservation count displays
5. **API Endpoints**: Reservation listing and status endpoints

### Enhanced Dashboard Display Logic

#### "Meine kommenden Buchungen" Section
The dashboard's "My Upcoming Reservations" section will be enhanced to use time-based filtering:

**Current Behavior:**
```python
# Shows all reservations for today and future dates
reservations = Reservation.query.filter(
    Reservation.booked_for_id == member_id,
    Reservation.status == 'active',
    Reservation.date >= today
).all()
```

**Enhanced Behavior:**
```python
# Shows only reservations that are currently active (future or in progress)
current_datetime = datetime.now()
reservations = Reservation.query.filter(
    Reservation.booked_for_id == member_id,
    Reservation.status == 'active',
    or_(
        Reservation.date > current_datetime.date(),
        and_(
            Reservation.date == current_datetime.date(),
            Reservation.end_time > current_datetime.time()
        )
    )
).all()
```

This ensures that:
- Past reservations (ended earlier today) are immediately removed from the upcoming list
- Current reservations (in progress) remain visible until they end
- Future reservations continue to be displayed
- Both regular and short notice bookings follow the same display logic

## Components and Interfaces

### Enhanced ReservationService Methods

#### get_member_active_booking_sessions()
```python
@staticmethod
def get_member_active_booking_sessions(member_id, include_short_notice=False, current_time=None):
    """
    Get active booking sessions for a member using time-based logic.
    
    Args:
        member_id: ID of the member
        include_short_notice: Whether to include short notice bookings (default False)
        current_time: Current datetime (defaults to now)
        
    Returns:
        list: List of active Reservation objects
    """
```

#### get_member_active_short_notice_bookings()
```python
@staticmethod
def get_member_active_short_notice_bookings(member_id, current_time=None):
    """
    Get active short notice bookings for a member using time-based logic.
    
    Args:
        member_id: ID of the member
        current_time: Current datetime (defaults to now)
        
    Returns:
        list: List of active short notice Reservation objects
    """
```

#### is_reservation_currently_active()
```python
@staticmethod
def is_reservation_currently_active(reservation, current_time=None):
    """
    Check if a reservation is currently active based on time.
    
    Args:
        reservation: Reservation object
        current_time: Current datetime (defaults to now)
        
    Returns:
        bool: True if reservation is active (future or in progress)
    """
```

### Enhanced ValidationService Methods

#### validate_member_reservation_limit()
```python
@staticmethod
def validate_member_reservation_limit(member_id, is_short_notice=False, current_time=None):
    """
    Validate member has not exceeded the 2-reservation limit using time-based logic.
    
    Args:
        member_id: ID of the member
        is_short_notice: Whether this is a short notice booking (default False)
        current_time: Current datetime (defaults to now)
        
    Returns:
        bool: True if member can make another reservation, False otherwise
    """
```

#### validate_member_short_notice_limit()
```python
@staticmethod
def validate_member_short_notice_limit(member_id, current_time=None):
    """
    Validate member has not exceeded the 1 short notice booking limit using time-based logic.
    
    Args:
        member_id: ID of the member
        current_time: Current datetime (defaults to now)
        
    Returns:
        bool: True if member can make another short notice booking, False otherwise
    """
```

### Time Comparison Logic

#### Core Time-Based Active Check
```python
def is_reservation_active_by_time(reservation_date, reservation_end_time, current_time):
    """
    Determine if a reservation is active based on current time.
    
    Logic:
    - Future reservations (date > current_date): Active
    - Same-day reservations: Active if end_time > current_time
    - Past reservations (date < current_date): Not active
    - Same-day ended reservations (end_time <= current_time): Not active
    
    Args:
        reservation_date: Date of the reservation
        reservation_end_time: End time of the reservation
        current_time: Current datetime
        
    Returns:
        bool: True if reservation is active
    """
    current_date = current_time.date()
    current_time_only = current_time.time()
    
    if reservation_date > current_date:
        return True  # Future reservation
    elif reservation_date == current_date:
        return reservation_end_time > current_time_only  # Same day, check if ended
    else:
        return False  # Past reservation
```

## Data Models

### No Database Schema Changes Required

The enhancement uses existing database fields and does not require any schema modifications:

- `Reservation.date`: Already exists
- `Reservation.start_time`: Already exists  
- `Reservation.end_time`: Already exists
- `Reservation.status`: Already exists
- `Reservation.is_short_notice`: Already exists

### Query Optimization Considerations

The time-based queries will be more complex than the current date-only queries. Consider adding composite indexes if performance becomes an issue:

```sql
-- Potential optimization indexes
CREATE INDEX idx_reservation_active_lookup ON reservation (booked_for_id, status, date, end_time);
CREATE INDEX idx_reservation_short_notice_lookup ON reservation (booked_for_id, status, is_short_notice, date, end_time);
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Time-based active booking session determination
*For any* reservation and current time, the reservation should be counted as an active booking session if and only if the current time is before the reservation's end time (either future date or same date with end time after current time).
**Validates: Requirements 1.1, 1.2, 1.3, 1.5**

### Property 2: Short notice bookings excluded from active booking session count
*For any* member and current time, when counting active booking sessions for the 2-reservation limit, all reservations with is_short_notice=true should be excluded regardless of their timing.
**Validates: Requirements 2.1, 2.2**

### Property 3: Short notice booking limit uses time-based logic
*For any* member and current time, when evaluating the 1 short notice booking limit, only short notice bookings that are currently active (using the same time-based logic as regular reservations) should count toward the limit.
**Validates: Requirements 2.5, 2.6**

### Property 4: Regular reservation limit allows short notice bookings
*For any* member with 2 regular active booking sessions, the system should still allow creation of short notice bookings.
**Validates: Requirements 2.3**

### Property 5: Consistent active booking session logic across system components
*For any* member and current time, all system methods that count active reservations (ReservationService, ValidationService, admin panel, dashboard) should return consistent results using the time-based active booking session logic.
**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**

### Property 6: Accurate display of active booking information
*For any* member viewing their reservation information, the system should display accurate counts and labels that distinguish between active booking sessions (future/current) and past reservations based on the current time, and the "Meine kommenden Buchungen" section should only show reservations that are currently active (future or in progress).
**Validates: Requirements 4.1, 4.2, 4.4**

### Property 7: Real-time availability calculation updates
*For any* reservation that transitions from active to past (when current time passes the end time), the system should immediately reflect this change in availability calculations and reservation limit enforcement.
**Validates: Requirements 4.3**

### Property 8: Consistent timezone handling
*For any* time comparison in the active booking session logic, the system should use consistent timezone handling to ensure accurate time-based evaluations.
**Validates: Requirements 5.3**

## Error Handling

### Time-Related Edge Cases

1. **Exact Time Boundaries**: When current time exactly matches start or end times, the system uses consistent boundary rules (start time inclusive, end time exclusive)

2. **Timezone Consistency**: All time comparisons use the same timezone reference (Europe/Berlin) to avoid inconsistencies

3. **Date Transitions**: Reservations spanning midnight are handled correctly by comparing both date and time components

4. **System Clock Changes**: The system gracefully handles daylight saving time transitions by using timezone-aware datetime operations

### Validation Error Messages

Enhanced error messages provide clear feedback about active booking session limits:

```python
# Regular reservation limit with time-based counting
"Sie haben bereits 2 aktive Buchungen (zukünftige oder laufende Reservierungen)"

# Short notice booking limit with time-based counting  
"Sie haben bereits eine aktive kurzfristige Buchung (zukünftige oder laufende Reservierung)"

# Availability information with real-time updates
"Verfügbare Buchungsplätze: {available_slots} von 2 (basierend auf aktueller Zeit)"
```

### Fallback Behavior

If time-based calculations fail due to system issues, the system falls back to the previous date-based logic to ensure continued operation while logging the error for investigation.

## Testing Strategy

### Dual Testing Approach

The implementation will use both unit tests and property-based tests to ensure comprehensive coverage:

**Unit Tests** will verify:
- Specific time boundary scenarios (exact start/end times)
- Edge cases like midnight-spanning reservations
- Integration between service methods
- Error handling and fallback behavior

**Property-Based Tests** will verify:
- Universal properties across all possible reservation timings
- Consistency between different system components
- Correct behavior with randomly generated reservation scenarios
- Time-based logic with various current time values

### Property-Based Testing Configuration

Each property test will run a minimum of 100 iterations with randomly generated:
- Reservation dates and times
- Current time values
- Member IDs and reservation combinations
- Short notice booking flags

Test tags will reference design document properties:
- **Feature: active-booking-session-logic, Property 1: Time-based active booking session determination**
- **Feature: active-booking-session-logic, Property 2: Short notice bookings excluded from active booking session count**
- **Feature: active-booking-session-logic, Property 3: Short notice booking limit uses time-based logic**
- **Feature: active-booking-session-logic, Property 4: Regular reservation limit allows short notice bookings**
- **Feature: active-booking-session-logic, Property 5: Consistent active booking session logic across system components**
- **Feature: active-booking-session-logic, Property 6: Accurate display of active booking information**
- **Feature: active-booking-session-logic, Property 7: Real-time availability calculation updates**
- **Feature: active-booking-session-logic, Property 8: Consistent timezone handling**

### Test Data Generation

Property tests will use smart generators that:
- Create realistic reservation time ranges (06:00-22:00)
- Generate current times that create interesting boundary conditions
- Mix regular and short notice bookings appropriately
- Ensure timezone consistency across all generated data

### Integration Testing

Integration tests will verify that the enhanced logic works correctly with:
- Existing reservation creation workflows
- Admin panel displays and operations
- Dashboard and user interface components
- Email notification systems
- Database query performance under load