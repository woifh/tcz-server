# Design Document

## Overview

The tennis club court reservation system is a Flask-based web application that enables members to book tennis courts and administrators to manage availability. The system uses a three-tier architecture with a Flask backend, MySQL database, and responsive HTML/Tailwind CSS frontend. All user-facing content is localized in German.

The application enforces business rules including the 2-active-reservations limit, prevents booking conflicts, and sends email notifications for all booking events. Administrators can block courts and override reservations, with automatic notifications to affected members.

## Architecture

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Browser                              │
│  (HTML + Tailwind CSS + JavaScript/Alpine.js)               │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTPS
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                   PythonAnywhere WSGI                        │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              Flask Application                         │  │
│  │  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐ │  │
│  │  │   Routes    │  │   Services   │  │    Models    │ │  │
│  │  │  (Views)    │→ │   (Logic)    │→ │  (SQLAlchemy)│ │  │
│  │  └─────────────┘  └──────────────┘  └──────────────┘ │  │
│  └───────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │
          ┌──────────────┴──────────────┐
          ↓                             ↓
┌──────────────────┐          ┌──────────────────┐
│  MySQL Database  │          │   SMTP Server    │
│  (PythonAnywhere)│          │  (Email Sending) │
└──────────────────┘          └──────────────────┘
```

### Technology Stack

- **Backend Framework**: Flask 3.0+
- **ORM**: SQLAlchemy 2.0+
- **Authentication**: Flask-Login
- **Email**: Flask-Mail with SMTP
- **Database**: MySQL 8.0+
- **Frontend**: HTML5, Tailwind CSS 3.0+, Alpine.js (minimal)
- **Deployment**: PythonAnywhere WSGI
- **Python Version**: 3.10+

### Directory Structure

```
tennis-club-reservation/
├── app/
│   ├── __init__.py              # Flask app factory
│   ├── models.py                # SQLAlchemy models
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py              # Login/logout routes
│   │   ├── reservations.py      # Booking routes
│   │   ├── members.py           # Member management
│   │   ├── courts.py            # Court availability
│   │   └── admin.py             # Admin functions
│   ├── services/
│   │   ├── __init__.py
│   │   ├── reservation_service.py
│   │   ├── email_service.py
│   │   ├── validation_service.py
│   │   └── block_service.py
│   ├── templates/
│   │   ├── base.html
│   │   ├── login.html
│   │   ├── dashboard.html
│   │   ├── booking_form.html
│   │   ├── admin_panel.html
│   │   └── member_list.html
│   └── static/
│       ├── css/
│       │   └── styles.css       # Tailwind output
│       └── js/
│           └── app.js           # Frontend logic
├── migrations/                   # Database migrations
├── tests/
│   ├── test_models.py
│   ├── test_services.py
│   └── test_routes.py
├── config.py                     # Configuration
├── wsgi.py                       # WSGI entry point
├── requirements.txt
└── tailwind.config.js
```

## Components and Interfaces

### Models (SQLAlchemy)

#### Member Model
```python
class Member(db.Model, UserMixin):
    id: int (primary key)
    firstname: str (not null, max 50 chars)
    lastname: str (not null, max 50 chars)
    email: str (unique, not null)
    password_hash: str (not null)
    role: str (default='member', values: 'member'|'administrator')
    created_at: datetime
    
    # Properties
    @property
    name: str (returns "firstname lastname" for backward compatibility)
    
    # Relationships
    reservations_made: List[Reservation] (backref: booked_by)
    reservations_for: List[Reservation] (backref: booked_for)
    favourites: List[Member] (many-to-many self-referential)
    notifications: List[Notification]
```

#### Court Model
```python
class Court(db.Model):
    id: int (primary key)
    number: int (unique, 1-6, not null)
    status: str (default='available', values: 'available'|'blocked')
    
    # Relationships
    reservations: List[Reservation]
    blocks: List[Block]
```

#### Reservation Model
```python
class Reservation(db.Model):
    id: int (primary key)
    court_id: int (foreign key → Court.id, not null)
    date: date (not null)
    start_time: time (not null)
    end_time: time (not null)
    booked_for_id: int (foreign key → Member.id, not null)
    booked_by_id: int (foreign key → Member.id, not null)
    status: str (default='active', values: 'active'|'cancelled'|'completed')
    reason: str (nullable, for admin cancellations)
    created_at: datetime
    
    # Relationships
    court: Court
    booked_for: Member
    booked_by: Member
    
    # Constraints
    unique_constraint(court_id, date, start_time)
```

#### Block Model
```python
class Block(db.Model):
    id: int (primary key)
    court_id: int (foreign key → Court.id, not null)
    date: date (not null)
    start_time: time (not null)
    end_time: time (not null)
    reason: str (not null, values: 'rain'|'maintenance'|'tournament'|'championship')
    created_by_id: int (foreign key → Member.id, not null)
    created_at: datetime
    
    # Relationships
    court: Court
    created_by: Member
```

#### Notification Model
```python
class Notification(db.Model):
    id: int (primary key)
    recipient_id: int (foreign key → Member.id, not null)
    type: str (not null, values: 'booking_created'|'booking_modified'|'booking_cancelled'|'admin_override')
    message: str (not null)
    timestamp: datetime
    read: bool (default=False)
    
    # Relationships
    recipient: Member
```

### Services

#### ReservationService
```python
class ReservationService:
    def create_reservation(court_id, date, start_time, booked_for_id, booked_by_id) -> Reservation
    def update_reservation(reservation_id, **updates) -> Reservation
    def cancel_reservation(reservation_id, reason=None) -> bool
    def get_member_active_reservations(member_id) -> List[Reservation]
    def check_availability(court_id, date, start_time) -> bool
    def get_reservations_by_date(date) -> List[Reservation]
```

#### ValidationService
```python
class ValidationService:
    def validate_booking_time(start_time) -> bool
    def validate_member_reservation_limit(member_id) -> bool
    def validate_no_conflict(court_id, date, start_time) -> bool
    def validate_not_blocked(court_id, date, start_time) -> bool
    def validate_all_booking_constraints(court_id, date, start_time, member_id) -> Tuple[bool, str]
```

#### EmailService
```python
class EmailService:
    def send_booking_created(reservation: Reservation) -> bool
    def send_booking_modified(reservation: Reservation) -> bool
    def send_booking_cancelled(reservation: Reservation, reason: str) -> bool
    def send_admin_override(affected_members: List[Member], reason: str) -> bool
    def format_german_email(template: str, **kwargs) -> str
```

#### BlockService
```python
class BlockService:
    def create_block(court_id, date, start_time, end_time, reason, admin_id) -> Block
    def get_blocks_by_date(date) -> List[Block]
    def cancel_conflicting_reservations(block: Block) -> List[Reservation]
```

### Routes

#### Authentication Routes (`/auth`)
- `GET /auth/login` - Display login form
- `POST /auth/login` - Process login
- `GET /auth/logout` - Logout user

#### Member Routes (`/members`)
- `GET /members` - List all members (admin only)
- `POST /members` - Create new member (admin only)
- `PUT /members/<id>` - Update member
- `DELETE /members/<id>` - Delete member (admin only)
- `POST /members/<id>/favourites` - Add favourite
- `DELETE /members/<id>/favourites/<fav_id>` - Remove favourite

#### Court Routes (`/courts`)
- `GET /courts` - Get all courts with availability
- `GET /courts/availability?date=YYYY-MM-DD` - Get availability grid

#### Reservation Routes (`/reservations`)
- `GET /reservations` - List user's reservations
- `GET /reservations?date=YYYY-MM-DD` - List all reservations for date
- `POST /reservations` - Create reservation
- `PUT /reservations/<id>` - Update reservation
- `DELETE /reservations/<id>` - Cancel reservation

#### Block Routes (`/blocks`) (admin only)
- `GET /blocks?date=YYYY-MM-DD` - List blocks for date
- `POST /blocks` - Create block
- `DELETE /blocks/<id>` - Remove block

#### Dashboard Routes (`/`)
- `GET /` - Main dashboard with court grid
- `GET /dashboard` - User dashboard

## Data Models

### Database Schema

```sql
-- Members table
CREATE TABLE member (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('member', 'administrator') DEFAULT 'member',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_email (email)
);

-- Courts table
CREATE TABLE court (
    id INT AUTO_INCREMENT PRIMARY KEY,
    number INT UNIQUE NOT NULL CHECK (number BETWEEN 1 AND 6),
    status ENUM('available', 'blocked') DEFAULT 'available'
);

-- Reservations table
CREATE TABLE reservation (
    id INT AUTO_INCREMENT PRIMARY KEY,
    court_id INT NOT NULL,
    date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    booked_for_id INT NOT NULL,
    booked_by_id INT NOT NULL,
    status ENUM('active', 'cancelled', 'completed') DEFAULT 'active',
    reason VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (court_id) REFERENCES court(id) ON DELETE CASCADE,
    FOREIGN KEY (booked_for_id) REFERENCES member(id) ON DELETE CASCADE,
    FOREIGN KEY (booked_by_id) REFERENCES member(id) ON DELETE CASCADE,
    UNIQUE KEY unique_booking (court_id, date, start_time),
    INDEX idx_date (date),
    INDEX idx_booked_for (booked_for_id),
    INDEX idx_booked_by (booked_by_id)
);

-- Blocks table
CREATE TABLE block (
    id INT AUTO_INCREMENT PRIMARY KEY,
    court_id INT NOT NULL,
    date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    reason ENUM('rain', 'maintenance', 'tournament', 'championship') NOT NULL,
    created_by_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (court_id) REFERENCES court(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by_id) REFERENCES member(id),
    INDEX idx_date (date),
    INDEX idx_court_date (court_id, date)
);

-- Favourites table (many-to-many self-referential)
CREATE TABLE favourite (
    member_id INT NOT NULL,
    favourite_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (member_id, favourite_id),
    FOREIGN KEY (member_id) REFERENCES member(id) ON DELETE CASCADE,
    FOREIGN KEY (favourite_id) REFERENCES member(id) ON DELETE CASCADE,
    CHECK (member_id != favourite_id)
);

-- Notifications table
CREATE TABLE notification (
    id INT AUTO_INCREMENT PRIMARY KEY,
    recipient_id INT NOT NULL,
    type ENUM('booking_created', 'booking_modified', 'booking_cancelled', 'admin_override') NOT NULL,
    message TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    read BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (recipient_id) REFERENCES member(id) ON DELETE CASCADE,
    INDEX idx_recipient (recipient_id),
    INDEX idx_timestamp (timestamp)
);
```

### Data Validation Rules

1. **Time Slot Validation**: start_time must be between 06:00 and 20:00, end_time = start_time + 1 hour
2. **Court Number Validation**: Court number must be 1-6
3. **Email Validation**: Email must be valid format and unique
4. **Password Validation**: Minimum 8 characters (enforced at application level)
5. **Date Validation**: Reservations cannot be created for past dates
6. **Member Limit Validation**: Member cannot have more than 2 active reservations
7. **Conflict Validation**: No overlapping reservations for same court/time
8. **Block Validation**: Blocked time slots cannot be booked

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*


### Property 1: Reservation creation stores all required fields
*For any* valid court, date, time, booked_for member, and booked_by member, creating a reservation should result in a database record containing all five fields with correct values.
**Validates: Requirements 1.1, 1.2**

### Property 2: Two-reservation limit enforcement
*For any* member with fewer than 2 active reservations, creating a new reservation should succeed; for any member with 2 active reservations, creating a new reservation should be rejected.
**Validates: Requirements 1.3, 11.3**

### Property 3: Booking notifications sent to both parties
*For any* reservation creation, the system should send email notifications to both the booked_by member and the booked_for member.
**Validates: Requirements 1.4**

### Property 4: Dual-member access control
*For any* reservation, both the booked_for member and the booked_by member should be able to view, modify, and cancel that reservation, while other members should not have these permissions.
**Validates: Requirements 2.1, 2.2, 2.3**

### Property 5: Modification notifications sent to both parties
*For any* reservation modification, the system should send email notifications to both the booked_by member and the booked_for member.
**Validates: Requirements 2.4**

### Property 6: Cancellation notifications sent to both parties
*For any* reservation cancellation, the system should send email notifications to both the booked_by member and the booked_for member.
**Validates: Requirements 2.5**

### Property 7: Favourites add and remove operations
*For any* two distinct members A and B, adding B to A's favourites should result in B appearing in A's favourites list; removing B should result in B no longer appearing in the list.
**Validates: Requirements 3.1, 3.2**

### Property 8: Favourites displayed in booking dropdown
*For any* member with a non-empty favourites list, the booking form should display all favourites in the booked_for dropdown.
**Validates: Requirements 3.3**

### Property 9: Available slots render green
*For any* court and time slot that is not reserved or blocked, the grid cell should be displayed in green.
**Validates: Requirements 4.2**

### Property 10: Reserved slots render red with member names
*For any* reservation, the corresponding grid cell should be displayed in red and contain text showing both the booked_for and booked_by member names.
**Validates: Requirements 4.3**

### Property 11: Blocked slots render grey
*For any* blocked court and time slot, the grid cell should be displayed in grey.
**Validates: Requirements 4.4**

### Property 12: Clicking available cell opens pre-filled form
*For any* available grid cell, clicking it should open the booking form with the court, date, and time fields pre-filled with the cell's values.
**Validates: Requirements 4.5**

### Property 13: Blocks prevent new reservations
*For any* court and time period with an active block, attempts to create reservations for that court during the blocked period should be rejected.
**Validates: Requirements 5.1, 11.2**

### Property 14: Blocks cascade-cancel existing reservations
*For any* block created on a court with existing reservations in the blocked time period, those reservations should be automatically cancelled.
**Validates: Requirements 5.2**

### Property 15: Block cancellations include reason in notification
*For any* reservation cancelled due to a block, the email notifications sent to the booked_by and booked_for members should include the block reason.
**Validates: Requirements 5.3**

### Property 16: Block creation stores all fields
*For any* valid court, date, time range, and reason, creating a block should result in a database record containing all fields with correct values.
**Validates: Requirements 5.4**

### Property 17: Member creation stores all fields
*For any* valid firstname, lastname, email, password, and role, creating a member should result in a database record containing all fields with the password properly hashed.
**Validates: Requirements 6.1, 13.3**

### Property 18: Member updates modify stored data
*For any* existing member and valid field updates, updating the member should result in the database record reflecting the new values.
**Validates: Requirements 6.2**

### Property 19: Member deletion removes from database
*For any* existing member, deleting that member should result in the member no longer appearing in database queries.
**Validates: Requirements 6.3**

### Property 20: Member list displays all members
*For any* set of registered members, the member list view should display all members with their details.
**Validates: Requirements 6.5**

### Property 21: Admin deletion removes reservation
*For any* existing reservation, when an administrator deletes it, the reservation should be removed from the database.
**Validates: Requirements 7.1**

### Property 22: Admin deletion sends notifications
*For any* reservation deleted by an administrator, email notifications should be sent to both the booked_by and booked_for members.
**Validates: Requirements 7.2**

### Property 23: Admin override includes reason in notification
*For any* reservation overridden by an administrator with a reason, the email notifications should include that reason.
**Validates: Requirements 7.3, 8.4**

### Property 24: All email notifications use German language
*For any* email notification sent by the system (creation, modification, cancellation, admin override), the subject line and body content should be in German.
**Validates: Requirements 8.1, 8.2, 8.3, 8.5**

### Property 25: All interface text is German
*For any* page or component in the user interface, all static text (labels, buttons, headings, messages) should be in German.
**Validates: Requirements 10.1, 10.3, 10.5**

### Property 26: Dates formatted in German convention
*For any* date displayed in the interface, it should be formatted according to German conventions (DD.MM.YYYY).
**Validates: Requirements 10.4**

### Property 27: Reservation conflicts are rejected
*For any* court and time slot with an existing active reservation, attempts to create another reservation for the same court and time should be rejected.
**Validates: Requirements 11.1, 11.5**

### Property 28: Valid login creates session
*For any* member with valid credentials, logging in should create an authenticated session that allows access to protected features.
**Validates: Requirements 13.1**

### Property 29: Invalid login is rejected
*For any* login attempt with invalid credentials (wrong email or password), the system should reject the login and display an error message.
**Validates: Requirements 13.2**

### Property 30: Logout terminates session
*For any* authenticated member, logging out should terminate the session and prevent access to protected features.
**Validates: Requirements 13.4**

### Property 31: Unauthenticated access is restricted
*For any* protected route (reservations, member management), unauthenticated requests should be rejected and redirected to login.
**Validates: Requirements 13.5**

### Property 32: Time slot validation
*For any* reservation attempt, the system should accept start times between 06:00 and 20:00 (inclusive) and reject all other times.
**Validates: Requirements 14.1, 14.3**

### Property 33: One-hour duration enforcement
*For any* reservation created, the duration (end_time - start_time) should equal exactly one hour.
**Validates: Requirements 14.2**

### Property 34: Delete actions require confirmation
*For any* delete operation in the UI, the system should display a confirmation dialog and only proceed if the user explicitly confirms.
**Validates: Requirements 15.3**

### Property 35: Success messages auto-dismiss
*For any* successful create or update operation, the system should display a toast notification that automatically disappears after 3 seconds without requiring user interaction.
**Validates: Requirements 15.1, 15.2, 15.5**

## User Feedback and Notifications

### Success Messages

All successful operations (create, update, delete) display non-blocking toast notifications that:
- Appear in the top-right corner of the screen
- Auto-dismiss after 3 seconds
- Use green background for success
- Display German text
- Do not require user interaction to dismiss

**Implementation:**
```javascript
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `fixed top-4 right-4 px-6 py-3 rounded-lg shadow-lg ${
        type === 'success' ? 'bg-green-600' : 'bg-red-600'
    } text-white z-50`;
    toast.textContent = message;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.remove();
    }, 3000);
}
```

### Confirmation Dialogs

Delete operations require explicit confirmation before proceeding:
- Display a modal dialog with clear warning
- Require user to click "Bestätigen" (Confirm) or "Abbrechen" (Cancel)
- Only proceed with deletion after confirmation
- Show success toast after successful deletion

**Example:**
```javascript
if (confirm('Möchten Sie diese Buchung wirklich löschen?')) {
    // Proceed with deletion
    deleteReservation(id);
}
```

### Success Message Examples

| Action | German Message |
|--------|----------------|
| Reservation Created | Buchung erfolgreich erstellt |
| Reservation Updated | Buchung erfolgreich aktualisiert |
| Reservation Deleted | Buchung erfolgreich gelöscht |
| Member Created | Mitglied erfolgreich erstellt |
| Member Updated | Mitglied erfolgreich aktualisiert |
| Member Deleted | Mitglied erfolgreich gelöscht |
| Favourite Added | Favorit erfolgreich hinzugefügt |
| Favourite Removed | Favorit erfolgreich entfernt |
| Block Created | Sperrung erfolgreich erstellt |

## Error Handling

### Error Categories

1. **Validation Errors** (HTTP 400)
   - Invalid time slots (outside 06:00-21:00)
   - Member exceeds 2-reservation limit
   - Booking conflicts
   - Blocked time slots
   - Invalid email format
   - Weak passwords

2. **Authentication Errors** (HTTP 401)
   - Invalid credentials
   - Expired sessions
   - Missing authentication

3. **Authorization Errors** (HTTP 403)
   - Non-admin accessing admin routes
   - Member accessing another's reservation (not booked_for or booked_by)

4. **Not Found Errors** (HTTP 404)
   - Non-existent reservation
   - Non-existent member
   - Non-existent court

5. **Server Errors** (HTTP 500)
   - Database connection failures
   - Email sending failures
   - Unexpected exceptions

### Error Response Format

```json
{
  "error": {
    "code": "BOOKING_CONFLICT",
    "message": "Dieser Platz ist bereits für diese Zeit gebucht",
    "details": {
      "court": 3,
      "date": "2025-12-15",
      "time": "14:00"
    }
  }
}
```

### Error Handling Strategy

1. **Input Validation**: Validate all inputs at the service layer before database operations
2. **Transaction Management**: Use database transactions for operations that modify multiple records
3. **Graceful Degradation**: If email sending fails, log the error but don't fail the reservation
4. **User-Friendly Messages**: All error messages displayed to users in German
5. **Logging**: Log all errors with context for debugging
6. **Rollback**: Automatically rollback database changes on errors

### German Error Messages

| Error Code | German Message |
|------------|----------------|
| BOOKING_CONFLICT | Dieser Platz ist bereits für diese Zeit gebucht |
| RESERVATION_LIMIT | Sie haben bereits 2 aktive Buchungen |
| BLOCKED_SLOT | Dieser Platz ist für diese Zeit gesperrt |
| INVALID_TIME | Buchungen sind nur zwischen 06:00 und 21:00 Uhr möglich |
| INVALID_CREDENTIALS | E-Mail oder Passwort ist falsch |
| UNAUTHORIZED | Sie haben keine Berechtigung für diese Aktion |
| NOT_FOUND | Die angeforderte Ressource wurde nicht gefunden |
| EMAIL_FAILED | E-Mail konnte nicht gesendet werden |

## Testing Strategy

### Unit Testing

Unit tests will verify specific functionality of individual components:

**Model Tests**:
- Member model password hashing
- Reservation model time validation
- Court model number constraints
- Relationship integrity (favourites, reservations)

**Service Tests**:
- ReservationService booking logic
- ValidationService constraint checking
- EmailService message formatting
- BlockService cascade cancellation

**Route Tests**:
- Authentication flow
- Authorization checks
- Request/response formats
- Error handling

**Example Unit Tests**:
```python
def test_password_hashing():
    """Test that passwords are hashed, not stored in plain text"""
    member = Member(firstname="Test", lastname="User", email="test@example.com")
    member.set_password("password123")
    assert member.password_hash != "password123"
    assert member.check_password("password123")

def test_reservation_time_validation():
    """Test that reservations outside 06:00-21:00 are rejected"""
    with pytest.raises(ValidationError):
        Reservation(court_id=1, date=date.today(), 
                   start_time=time(5, 0), end_time=time(6, 0))

def test_block_cascade_cancellation():
    """Test that creating a block cancels conflicting reservations"""
    reservation = create_test_reservation(court=1, time="14:00")
    block = BlockService.create_block(court_id=1, date=reservation.date,
                                     start_time=time(14, 0), end_time=time(15, 0),
                                     reason="maintenance", admin_id=1)
    assert Reservation.query.get(reservation.id).status == "cancelled"
```

### Property-Based Testing

Property-based tests will verify universal properties across many randomly generated inputs using the **Hypothesis** library for Python.

**Configuration**:
- Minimum 100 iterations per property test
- Use Hypothesis strategies for generating test data
- Each property test tagged with design document reference

**Test Data Generators**:
```python
from hypothesis import given, strategies as st
from datetime import time, date, timedelta

# Generate valid booking times (06:00-20:00)
booking_times = st.times(min_value=time(6, 0), max_value=time(20, 0))

# Generate valid court numbers (1-6)
court_numbers = st.integers(min_value=1, max_value=6)

# Generate future dates
future_dates = st.dates(min_value=date.today(), max_value=date.today() + timedelta(days=90))

# Generate member data
member_data = st.fixed_dictionaries({
    'name': st.text(min_size=1, max_size=100),
    'email': st.emails(),
    'password': st.text(min_size=8, max_size=50)
})
```

**Property Test Examples**:

```python
@given(court=court_numbers, booking_date=future_dates, 
       start=booking_times, member_id=st.integers(min_value=1))
def test_property_1_reservation_stores_all_fields(court, booking_date, start, member_id):
    """Feature: tennis-club-reservation, Property 1: Reservation creation stores all required fields
    Validates: Requirements 1.1, 1.2"""
    reservation = ReservationService.create_reservation(
        court_id=court, date=booking_date, start_time=start,
        booked_for_id=member_id, booked_by_id=member_id
    )
    assert reservation.court_id == court
    assert reservation.date == booking_date
    assert reservation.start_time == start
    assert reservation.booked_for_id == member_id
    assert reservation.booked_by_id == member_id

@given(member_id=st.integers(min_value=1))
def test_property_2_two_reservation_limit(member_id):
    """Feature: tennis-club-reservation, Property 2: Two-reservation limit enforcement
    Validates: Requirements 1.3, 11.3"""
    # Create 2 reservations
    create_test_reservation(booked_for_id=member_id)
    create_test_reservation(booked_for_id=member_id)
    
    # Third should fail
    with pytest.raises(ValidationError, match="2 aktive Buchungen"):
        create_test_reservation(booked_for_id=member_id)

@given(court=court_numbers, booking_date=future_dates, start=booking_times)
def test_property_27_reservation_conflicts_rejected(court, booking_date, start):
    """Feature: tennis-club-reservation, Property 27: Reservation conflicts are rejected
    Validates: Requirements 11.1, 11.5"""
    # Create first reservation
    create_test_reservation(court_id=court, date=booking_date, start_time=start)
    
    # Second reservation for same slot should fail
    with pytest.raises(ValidationError, match="bereits.*gebucht"):
        create_test_reservation(court_id=court, date=booking_date, start_time=start)
```

**Property Test Requirements**:
- Each correctness property MUST be implemented as a single property-based test
- Each test MUST be tagged with: `Feature: tennis-club-reservation, Property {number}: {property_text}`
- Each test MUST reference the requirements it validates
- Tests MUST run at least 100 iterations
- Tests SHOULD use smart generators that constrain to valid input space

### Integration Testing

Integration tests will verify end-to-end workflows:

- Complete booking flow (login → view grid → create reservation → receive email)
- Admin blocking flow (login as admin → block court → verify cancellations → verify emails)
- Favourites workflow (add favourite → book for favourite → verify both can modify)
- Responsive design (verify grid renders correctly on different viewport sizes)

### Email Testing

- Use Flask-Mail testing mode to capture sent emails
- Verify email recipients, subject, and body content
- Verify German language in all emails
- Test email sending failures don't break reservations

### Database Testing

- Use test database separate from production
- Reset database state between tests
- Test transaction rollback on errors
- Verify foreign key constraints
- Test cascade deletions

### Frontend Testing

- Manual testing on desktop, tablet, and mobile devices
- Verify Tailwind responsive classes work correctly
- Test touch interactions on mobile
- Verify German text displays correctly
- Test form validation and error messages

## Deployment on PythonAnywhere

### Setup Steps

1. **Create Virtual Environment**
   ```bash
   mkvirtualenv --python=/usr/bin/python3.10 tennis-club
   ```

2. **Install Dependencies**
   ```bash
   pip install flask sqlalchemy flask-login flask-mail pymysql cryptography
   ```

3. **Configure MySQL Database**
   - Create database via PythonAnywhere MySQL console
   - Set environment variables:
     ```bash
     export DATABASE_URL="mysql+pymysql://username:password@username.mysql.pythonanywhere-services.com/dbname"
     export SECRET_KEY="your-secret-key"
     export MAIL_SERVER="smtp.gmail.com"
     export MAIL_PORT=587
     export MAIL_USERNAME="your-email@gmail.com"
     export MAIL_PASSWORD="your-app-password"
     ```

4. **Run Database Migrations**
   ```bash
   flask db upgrade
   ```

5. **Create Admin User**
   ```bash
   flask create-admin --name "Admin" --email "admin@tennisclub.de"
   ```

6. **Configure WSGI**
   Create `/var/www/username_pythonanywhere_com_wsgi.py`:
   ```python
   import sys
   import os
   
   path = '/home/username/tennis-club-reservation'
   if path not in sys.path:
       sys.path.append(path)
   
   os.environ['DATABASE_URL'] = 'mysql+pymysql://...'
   os.environ['SECRET_KEY'] = '...'
   
   from app import create_app
   application = create_app()
   ```

7. **Configure Static Files**
   - Static URL: `/static/`
   - Static directory: `/home/username/tennis-club-reservation/app/static/`

8. **Test Email Sending**
   ```python
   from app import create_app, mail
   from flask_mail import Message
   
   app = create_app()
   with app.app_context():
       msg = Message("Test", recipients=["test@example.com"])
       mail.send(msg)
   ```

9. **Reload Web App**
   - Click "Reload" button in PythonAnywhere web tab

### Environment Variables

```bash
# Database
DATABASE_URL=mysql+pymysql://user:pass@host/dbname

# Flask
SECRET_KEY=your-secret-key-here
FLASK_ENV=production

# Email
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=noreply@tennisclub.de

# Application
COURTS_COUNT=6
BOOKING_START_HOUR=6
BOOKING_END_HOUR=21
MAX_ACTIVE_RESERVATIONS=2
```

### Production Considerations

1. **Security**
   - Use strong SECRET_KEY
   - Enable HTTPS
   - Use app-specific passwords for email
   - Sanitize all user inputs
   - Implement rate limiting

2. **Performance**
   - Add database indexes on frequently queried fields
   - Cache court availability grid
   - Use connection pooling for database
   - Minimize email sending latency

3. **Monitoring**
   - Log all errors to file
   - Monitor email delivery success
   - Track reservation creation/cancellation rates
   - Monitor database performance

4. **Backup**
   - Regular MySQL database backups
   - Backup environment variables
   - Version control for code

5. **Maintenance**
   - Regular dependency updates
   - Monitor PythonAnywhere service status
   - Test email delivery periodically
   - Review error logs weekly
