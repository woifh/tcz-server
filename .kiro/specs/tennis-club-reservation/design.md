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
    name: str (computed property, returns "firstname lastname" for backward compatibility)
    
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
    is_short_notice: bool (default=False, indicates if booking was made within 15 minutes of start time)
    reason: str (nullable, for admin cancellations)
    created_at: datetime
    
    # Relationships
    court: Court
    booked_for: Member
    booked_by: Member
    
    # Constraints
    unique_constraint(court_id, date, start_time)
```

#### Block Model (Enhanced)
```python
class Block(db.Model):
    id: int (primary key)
    court_id: int (foreign key → Court.id, not null)
    date: date (not null)
    start_time: time (not null)
    end_time: time (not null)
    reason_id: int (foreign key → BlockReason.id, not null)
    sub_reason: str (nullable, additional detail for the block)
    series_id: int (foreign key → BlockSeries.id, nullable, links recurring blocks)
    is_modified: bool (default=False, indicates if instance was modified from series pattern)
    created_by_id: int (foreign key → Member.id, not null)
    created_at: datetime
    
    # Relationships
    court: Court
    reason: BlockReason
    series: BlockSeries
    created_by: Member
```

#### BlockSeries Model (New)
```python
class BlockSeries(db.Model):
    id: int (primary key)
    name: str (not null, descriptive name for the series)
    start_date: date (not null)
    end_date: date (not null)
    start_time: time (not null)
    end_time: time (not null)
    recurrence_pattern: str (not null, values: 'daily'|'weekly'|'monthly')
    recurrence_days: str (nullable, JSON array for weekly pattern, e.g., "[1,3,5]" for Mon/Wed/Fri)
    reason_id: int (foreign key → BlockReason.id, not null)
    sub_reason: str (nullable)
    created_by_id: int (foreign key → Member.id, not null)
    created_at: datetime
    
    # Relationships
    blocks: List[Block] (backref: series)
    reason: BlockReason
    created_by: Member
```

#### BlockReason Model (New)
```python
class BlockReason(db.Model):
    id: int (primary key)
    name: str (unique, not null, max 50 chars)
    is_active: bool (default=True, allows soft deletion)
    created_by_id: int (foreign key → Member.id, not null)
    created_at: datetime
    
    # Relationships
    blocks: List[Block]
    templates: List[BlockTemplate]
    sub_reason_templates: List[SubReasonTemplate]
    created_by: Member
```

#### SubReasonTemplate Model (New)
```python
class SubReasonTemplate(db.Model):
    id: int (primary key)
    reason_id: int (foreign key → BlockReason.id, not null)
    template_name: str (not null, max 100 chars)
    created_by_id: int (foreign key → Member.id, not null)
    created_at: datetime
    
    # Relationships
    reason: BlockReason
    created_by: Member
```

#### BlockTemplate Model (New)
```python
class BlockTemplate(db.Model):
    id: int (primary key)
    name: str (unique, not null, max 100 chars)
    court_selection: str (JSON array of court IDs, e.g., "[1,2,3]")
    start_time: time (not null)
    end_time: time (not null)
    reason_id: int (foreign key → BlockReason.id, not null)
    sub_reason: str (nullable)
    recurrence_pattern: str (nullable, values: 'daily'|'weekly'|'monthly'|null for single blocks)
    recurrence_days: str (nullable, JSON array for weekly pattern)
    created_by_id: int (foreign key → Member.id, not null)
    created_at: datetime
    
    # Relationships
    reason: BlockReason
    created_by: Member
```

#### BlockAuditLog Model (New)
```python
class BlockAuditLog(db.Model):
    id: int (primary key)
    operation: str (not null, values: 'create'|'update'|'delete'|'bulk_delete')
    block_id: int (nullable, for single block operations)
    series_id: int (nullable, for series operations)
    operation_data: str (JSON, stores operation details)
    admin_id: int (foreign key → Member.id, not null)
    timestamp: datetime (default=current_timestamp)
    
    # Relationships
    admin: Member
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
    def get_member_active_reservations(member_id, include_short_notice=True) -> List[Reservation]
    def get_member_regular_reservations(member_id) -> List[Reservation]
    def check_availability(court_id, date, start_time) -> bool
    def get_reservations_by_date(date) -> List[Reservation]
    def is_short_notice_booking(date, start_time, current_time=None) -> bool
    def classify_booking_type(date, start_time, current_time=None) -> str
```

#### ValidationService
```python
class ValidationService:
    def validate_booking_time(start_time) -> bool
    def validate_member_reservation_limit(member_id, is_short_notice=False) -> bool
    def validate_member_short_notice_limit(member_id) -> bool
    def validate_no_conflict(court_id, date, start_time) -> bool
    def validate_not_blocked(court_id, date, start_time) -> bool
    def validate_cancellation_allowed(reservation_id, current_time=None) -> bool
    def validate_all_booking_constraints(court_id, date, start_time, member_id, is_short_notice=False) -> Tuple[bool, str]
    
    # Enhanced validation for short notice bookings:
    # - validate_member_reservation_limit() excludes short notice bookings from 2-reservation limit
    # - validate_member_short_notice_limit() enforces 1 active short notice booking per member
    # - validate_all_booking_constraints() allows booking slots that have started but not ended for short notice
    # - validate_cancellation_allowed() prevents cancellation within 15 minutes AND once slot has started
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

#### BlockService (Enhanced)
```python
class BlockService:
    # Basic block operations
    def create_block(court_id, date, start_time, end_time, reason_id, sub_reason, admin_id) -> Tuple[Block, str]
    def get_blocks_by_date(date) -> List[Block]
    def cancel_conflicting_reservations(block: Block) -> List[Reservation]
    
    # Recurring block series operations
    def create_recurring_block_series(court_ids, start_date, end_date, start_time, end_time, 
                                    recurrence_pattern, recurrence_days, reason_id, sub_reason, admin_id) -> Tuple[List[Block], str]
    def get_series_blocks(series_id) -> List[Block]
    def update_entire_series(series_id, **updates) -> Tuple[bool, str]
    def update_future_series(series_id, from_date, **updates) -> Tuple[bool, str]
    def update_single_instance(block_id, **updates) -> Tuple[bool, str]
    def delete_series_options(series_id, option, from_date=None) -> Tuple[bool, str]
    
    # Multi-court operations
    def create_multi_court_blocks(court_ids, date, start_time, end_time, reason_id, sub_reason, admin_id) -> Tuple[List[Block], str]
    def bulk_delete_blocks(block_ids, admin_id) -> Tuple[bool, str]
    
    # Template operations
    def create_block_template(name, template_data, admin_id) -> Tuple[BlockTemplate, str]
    def get_block_templates() -> List[BlockTemplate]
    def apply_block_template(template_id, date_overrides) -> dict
    def delete_block_template(template_id, admin_id) -> Tuple[bool, str]
    
    # Filtering and search
    def filter_blocks(date_range, court_ids, reason_ids, block_types) -> List[Block]
    def get_conflict_preview(court_ids, date, start_time, end_time) -> List[Reservation]
    
    # Audit operations
    def log_block_operation(operation, block_data, admin_id) -> None
    def get_audit_log(filters) -> List[BlockAuditLog]
```

#### BlockReasonService (New)
```python
class BlockReasonService:
    # Reason management
    def create_block_reason(name, admin_id) -> Tuple[BlockReason, str]
    def update_block_reason(reason_id, name, admin_id) -> Tuple[bool, str]
    def delete_block_reason(reason_id, admin_id) -> Tuple[bool, str]
    def get_all_block_reasons() -> List[BlockReason]
    def get_reason_usage_count(reason_id) -> int
    
    # Sub-reason template management
    def create_sub_reason_template(reason_id, template_name, admin_id) -> Tuple[SubReasonTemplate, str]
    def get_sub_reason_templates(reason_id) -> List[SubReasonTemplate]
    def delete_sub_reason_template(template_id, admin_id) -> Tuple[bool, str]
    
    # Default reason setup
    def initialize_default_reasons() -> None
    def cleanup_future_blocks_with_reason(reason_name) -> int
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

#### Block Routes (`/admin/blocks`) (admin only) (Enhanced)
- `GET /admin/blocks?date=YYYY-MM-DD` - List blocks for date
- `GET /admin/blocks?date_range=YYYY-MM-DD,YYYY-MM-DD&court_ids=1,2&reason_ids=1,2&block_type=single|series` - Filter blocks
- `POST /admin/blocks` - Create single block
- `POST /admin/blocks/series` - Create recurring block series
- `POST /admin/blocks/multi-court` - Create blocks for multiple courts
- `PUT /admin/blocks/<id>` - Update single block instance
- `PUT /admin/blocks/series/<series_id>` - Update entire series
- `PUT /admin/blocks/series/<series_id>/future?from_date=YYYY-MM-DD` - Update future series instances
- `DELETE /admin/blocks/<id>` - Delete single block
- `DELETE /admin/blocks/series/<series_id>?option=single|future|all&from_date=YYYY-MM-DD` - Delete series with options
- `POST /admin/blocks/bulk-delete` - Bulk delete selected blocks
- `GET /admin/blocks/conflict-preview` - Preview conflicting reservations
- `GET /admin/blocks/audit-log` - Get audit log with filters

#### Block Template Routes (`/admin/block-templates`) (admin only) (New)
- `GET /admin/block-templates` - List all block templates
- `POST /admin/block-templates` - Create block template
- `PUT /admin/block-templates/<id>` - Update block template
- `DELETE /admin/block-templates/<id>` - Delete block template
- `POST /admin/block-templates/<id>/apply` - Apply template to create blocks

#### Block Reason Routes (`/admin/block-reasons`) (admin only) (New)
- `GET /admin/block-reasons` - List all block reasons
- `POST /admin/block-reasons` - Create block reason
- `PUT /admin/block-reasons/<id>` - Update block reason
- `DELETE /admin/block-reasons/<id>` - Delete block reason (with usage check)
- `GET /admin/block-reasons/<id>/usage` - Get usage count for reason
- `GET /admin/block-reasons/<id>/sub-reason-templates` - List sub-reason templates
- `POST /admin/block-reasons/<id>/sub-reason-templates` - Create sub-reason template
- `DELETE /admin/sub-reason-templates/<id>` - Delete sub-reason template

#### Dashboard Routes (`/`)
- `GET /` - Main dashboard with court grid
- `GET /dashboard` - User dashboard

## Data Models

### Database Schema

```sql
-- Members table
CREATE TABLE member (
    id INT AUTO_INCREMENT PRIMARY KEY,
    firstname VARCHAR(50) NOT NULL,
    lastname VARCHAR(50) NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('member', 'administrator') DEFAULT 'member',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_email (email),
    INDEX idx_lastname (lastname)
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
    is_short_notice BOOLEAN DEFAULT FALSE,
    reason VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (court_id) REFERENCES court(id) ON DELETE CASCADE,
    FOREIGN KEY (booked_for_id) REFERENCES member(id) ON DELETE CASCADE,
    FOREIGN KEY (booked_by_id) REFERENCES member(id) ON DELETE CASCADE,
    UNIQUE KEY unique_booking (court_id, date, start_time),
    INDEX idx_date (date),
    INDEX idx_booked_for (booked_for_id),
    INDEX idx_booked_by (booked_by_id),
    INDEX idx_short_notice (is_short_notice)
);

-- Enhanced Blocks table with series support and customizable reasons
CREATE TABLE block_reason (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_by_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by_id) REFERENCES member(id),
    INDEX idx_name (name),
    INDEX idx_active (is_active)
);

-- Block series for recurring blocks
CREATE TABLE block_series (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    recurrence_pattern ENUM('daily', 'weekly', 'monthly') NOT NULL,
    recurrence_days JSON,
    reason_id INT NOT NULL,
    sub_reason VARCHAR(255),
    created_by_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (reason_id) REFERENCES block_reason(id),
    FOREIGN KEY (created_by_id) REFERENCES member(id),
    INDEX idx_dates (start_date, end_date),
    INDEX idx_reason (reason_id)
);

-- Enhanced blocks table
CREATE TABLE block (
    id INT AUTO_INCREMENT PRIMARY KEY,
    court_id INT NOT NULL,
    date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    reason_id INT NOT NULL,
    sub_reason VARCHAR(255),
    series_id INT,
    is_modified BOOLEAN DEFAULT FALSE,
    created_by_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (court_id) REFERENCES court(id) ON DELETE CASCADE,
    FOREIGN KEY (reason_id) REFERENCES block_reason(id),
    FOREIGN KEY (series_id) REFERENCES block_series(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by_id) REFERENCES member(id),
    INDEX idx_date (date),
    INDEX idx_court_date (court_id, date),
    INDEX idx_series (series_id),
    INDEX idx_reason (reason_id)
);

-- Sub-reason templates for common scenarios
CREATE TABLE sub_reason_template (
    id INT AUTO_INCREMENT PRIMARY KEY,
    reason_id INT NOT NULL,
    template_name VARCHAR(100) NOT NULL,
    created_by_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (reason_id) REFERENCES block_reason(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by_id) REFERENCES member(id),
    INDEX idx_reason (reason_id)
);

-- Block templates for reusable configurations
CREATE TABLE block_template (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    court_selection JSON NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    reason_id INT NOT NULL,
    sub_reason VARCHAR(255),
    recurrence_pattern ENUM('daily', 'weekly', 'monthly'),
    recurrence_days JSON,
    created_by_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (reason_id) REFERENCES block_reason(id),
    FOREIGN KEY (created_by_id) REFERENCES member(id),
    INDEX idx_name (name),
    INDEX idx_reason (reason_id)
);

-- Audit log for block operations
CREATE TABLE block_audit_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    operation ENUM('create', 'update', 'delete', 'bulk_delete') NOT NULL,
    block_id INT,
    series_id INT,
    operation_data JSON,
    admin_id INT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (admin_id) REFERENCES member(id),
    INDEX idx_timestamp (timestamp),
    INDEX idx_admin (admin_id),
    INDEX idx_operation (operation)
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
5. **Date Validation**: Regular reservations cannot be created for past dates; short notice reservations can be created for slots that have started but not ended
6. **Member Limit Validation**: Member cannot have more than 2 active regular reservations (short notice bookings excluded from count)
7. **Short Notice Limit Validation**: Member cannot have more than 1 active short notice booking at any time
8. **Conflict Validation**: No overlapping reservations for same court/time
9. **Block Validation**: Blocked time slots cannot be booked
10. **Short Notice Classification**: Reservations created within 15 minutes of start time are automatically classified as short notice
11. **Cancellation Time Validation**: Reservations cannot be cancelled within 15 minutes of start time or once the slot has started
12. **Short Notice Booking Window**: Short notice bookings allowed from 15 minutes before start time until end of slot
13. **Short Notice Non-Cancellable**: Short notice bookings can never be cancelled (inherent from timing rules)

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

### Property 8a: Self-favouriting is prevented
*For any* member, attempting to add themselves to their own favourites list should be rejected with an error.
**Validates: Requirements 3.4**

### Property 8b: Favourites are independent many-to-many relationships
*For any* two members A and B, Member A adding Member B to favourites should not automatically add Member A to Member B's favourites list.
**Validates: Requirements 3.5**

### Property 8c: Booking allowed for any member
*For any* member creating a reservation, the system should allow booking for any registered member, not only those in the favourites list.
**Validates: Requirements 3.6**

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

### Property 35: Create action toast notifications
*For any* successful create operation, the system should display a toast notification that automatically disappears after 3 seconds without requiring user interaction.
**Validates: Requirements 15.1**

### Property 35a: Update action toast notifications
*For any* successful update operation, the system should display a toast notification that automatically disappears after 3 seconds without requiring user interaction.
**Validates: Requirements 15.2**

### Property 35b: Delete action toast notifications
*For any* successful delete operation (after confirmation), the system should display a toast notification that automatically disappears after 3 seconds without requiring user interaction.
**Validates: Requirements 15.4**

### Property 35c: Delete cancellation closes dialog
*For any* delete action that is cancelled by the user, the confirmation dialog should close without performing the deletion.
**Validates: Requirements 15.5**

### Property 36: Password minimum length enforcement
*For any* password creation or update, the system should reject passwords with fewer than 8 characters.
**Validates: Requirements 13.6**

### Property 37: Email failures do not block operations
*For any* reservation operation where email notification fails, the reservation should still be created/updated/cancelled successfully and the failure should be logged.
**Validates: Requirements 16.1, 16.2, 16.3**

### Property 38: Times stored in UTC
*For any* reservation created, the start_time and end_time should be stored in UTC in the database.
**Validates: Requirements 17.1**

### Property 39: Times displayed in Europe/Berlin timezone
*For any* reservation displayed to a user, the times should be converted from UTC to Europe/Berlin timezone.
**Validates: Requirements 17.2, 17.4**

### Property 40: Short notice booking classification
*For any* reservation created within 15 minutes of the slot start time, the system should classify it as a short notice booking and set is_short_notice to true.
**Validates: Requirements 18.1**

### Property 41: Short notice bookings excluded from reservation limit
*For any* member with short notice bookings, those bookings should not count toward the member's active reservation limit of 2 reservations.
**Validates: Requirements 18.2, 18.3**

### Property 42: Regular reservation limit with short notice bookings allowed
*For any* member with 2 regular active reservations, the system should still allow creation of short notice bookings.
**Validates: Requirements 18.4**

### Property 42a: Short notice booking limit enforcement
*For any* member with 1 active short notice booking, attempting to create another short notice booking should be rejected until the existing short notice booking is completed or cancelled.
**Validates: Requirements 18.5, 18.6**

### Property 43: Short notice booking time window
*For any* time slot, short notice bookings should be allowed from 15 minutes before start time until the end of the slot.
**Validates: Requirements 18.7, 18.8, 18.9**

### Property 44: Short notice bookings follow all other constraints
*For any* short notice booking attempt, the system should apply all booking constraints except the reservation limit (court availability, authentication, time slot validity).
**Validates: Requirements 18.10**

### Property 45: Short notice bookings display with orange background
*For any* short notice booking displayed in the court grid, the cell should have an orange background color to distinguish it from regular reservations.
**Validates: Requirements 18.11, 4.4**

### Property 46: Cancellation prevented within 15 minutes and during slot time
*For any* reservation (regular or short notice) where the current time is within 15 minutes of the start time or at/after the start time, cancellation attempts should be rejected.
**Validates: Requirements 2.3, 2.4**

### Property 47: Short notice bookings cannot be cancelled
*For any* short notice booking, cancellation attempts should always be rejected since short notice bookings are by definition created within the cancellation prohibition window.
**Validates: Requirements 18.12**

### Property 48: Recurring block series generation
*For any* valid recurring block parameters (start date, end date, recurrence pattern, time range), creating a recurring block series should generate the correct number of individual block instances with proper dates and times according to the recurrence pattern.
**Validates: Requirements 19.1**

### Property 49: Weekly recurring blocks respect day selection
*For any* weekly recurring block with specific days selected, only blocks on those selected days should be created between the start and end dates.
**Validates: Requirements 19.2**

### Property 50: Recurring block series linking
*For any* recurring block series created, all individual block instances should be linked with the same series_id.
**Validates: Requirements 19.3**

### Property 51: Recurring blocks require end date
*For any* attempt to create a recurring block without an end date, the operation should be rejected with an error message.
**Validates: Requirements 19.4**

### Property 52: Series-wide edits affect all future instances
*For any* recurring block series and valid edit parameters, editing the entire series should apply changes to all future instances in the series while preserving past instances.
**Validates: Requirements 19.5, 19.6**

### Property 53: Single instance edits don't affect other instances
*For any* single instance edit in a recurring block series, only that specific instance should be modified while other instances in the series remain unchanged.
**Validates: Requirements 19.7**

### Property 54: Multi-court block creation
*For any* set of selected courts and valid block parameters, creating blocks for multiple courts should result in blocks being created for all selected courts with identical time periods, dates, and reasons.
**Validates: Requirements 19.10**

### Property 55: Block template storage and retrieval
*For any* valid block template data (name, time range, reason, court selection, recurrence settings), creating a template should store all fields correctly and make them available for future use.
**Validates: Requirements 19.11, 20.15**

### Property 56: Block template application
*For any* existing block template, applying the template should pre-fill the block creation form with all saved template values.
**Validates: Requirements 19.12**

### Property 57: Block filtering functionality
*For any* combination of filter criteria (date range, court, reason, block type), the filtering should return only blocks that match all specified criteria.
**Validates: Requirements 19.13**

### Property 58: Bulk block deletion
*For any* set of selected blocks, bulk deletion should remove all selected blocks after confirmation.
**Validates: Requirements 19.14**

### Property 59: Series deletion options
*For any* recurring block series, deletion should offer options to delete single occurrence, all future occurrences, or entire series, and execute the selected option correctly.
**Validates: Requirements 19.15**

### Property 60: Block tooltip information
*For any* block displayed in calendar view, the tooltip should contain all relevant block details including time, reason, affected courts, series information, and modification status.
**Validates: Requirements 19.17**

### Property 61: Conflict preview accuracy
*For any* block creation that conflicts with existing reservations, the conflict preview should display all affected reservations accurately.
**Validates: Requirements 19.18**

### Property 62: Block operation audit logging
*For any* block operation (create, update, delete), the system should create an audit log entry with correct operation details, timestamp, and administrator identification.
**Validates: Requirements 19.19**

### Property 63: Block reason management interface
*For any* administrator accessing the block reason management interface, all existing block reasons should be displayed with correct add, edit, and delete options.
**Validates: Requirements 20.1**

### Property 64: Block reason creation and availability
*For any* new block reason created by an administrator, the reason should be stored correctly and become available for selection in block creation forms.
**Validates: Requirements 20.2**

### Property 65: Block reason editing with historical preservation
*For any* existing block reason that is edited, the reason name should be updated for future use while preserving the original name in historical block data.
**Validates: Requirements 20.3**

### Property 66: Block reason deletion with usage warning
*For any* block reason currently in use by existing blocks, deletion attempts should display a warning message and require confirmation before proceeding.
**Validates: Requirements 20.4**

### Property 67: Block reason deletion with historical preservation
*For any* confirmed deletion of a block reason in use, all past blocks should retain the original reason, all future blocks using that reason should be deleted, and the reason should be removed from future creation options.
**Validates: Requirements 20.5**

### Property 68: Unused block reason deletion
*For any* block reason not currently in use, deletion should remove it from the system and future block creation options after confirmation.
**Validates: Requirements 20.6**

### Property 69: Sub-reason storage and display
*For any* block created with both main reason and sub-reason, both should be stored correctly and displayed together in block details and lists.
**Validates: Requirements 20.7, 20.10, 20.11**

### Property 70: Sub-reason template management
*For any* sub-reason template created for a block reason, the template should be stored correctly and made available for future use when creating blocks with that reason.
**Validates: Requirements 20.12**

### Property 71: Filtering by reason and sub-reason
*For any* filtering operation, the system should allow filtering by both main reason and sub-reason categories and return accurate results.
**Validates: Requirements 20.13**

### Property 72: Default block reasons initialization
*For any* system initialization, default block reasons (Maintenance, Weather, Tournament, Championship, Tennis Course) should be created and made available for administrator modification.
**Validates: Requirements 20.14**

## Short Notice Booking Implementation

### Overview

The short notice booking feature allows members to book courts within 15 minutes of the slot start time without counting against their 2-reservation limit. This feature was implemented to maximize court utilization by allowing last-minute bookings.

### Key Features

1. **Automatic Classification**: Bookings made within 15 minutes of start time are automatically classified as short notice
2. **Reservation Limit Exemption**: Short notice bookings don't count toward the 2-reservation limit
3. **Single Short Notice Limit**: Members can have only 1 active short notice booking at a time
4. **Visual Distinction**: Short notice bookings display with orange background color in the court grid
5. **Non-Cancellable**: Short notice bookings cannot be cancelled (inherent from timing rules)
6. **Extended Booking Window**: Can book slots that have already started but not yet ended

### Implementation Details

#### Database Schema
- Added `is_short_notice` boolean field to `reservation` table with default `FALSE`
- Added index on `is_short_notice` field for performance
- Migration script handles existing reservations

#### Backend Logic
- `ReservationService.is_short_notice_booking()` determines classification based on timing
- `ValidationService.validate_member_reservation_limit()` excludes short notice bookings from count
- `ValidationService.validate_member_short_notice_limit()` enforces 1 active short notice booking per member
- `ValidationService.validate_all_booking_constraints()` allows booking started slots for short notice
- Enhanced cancellation validation prevents cancellation within 15 minutes AND once started

#### Frontend Display
- Court grid shows orange background (`#f97316`) for short notice bookings
- Dashboard legend includes "Kurzfristig gebucht" with orange indicator
- Success messages differentiate between regular and short notice bookings
- Click on short notice booking shows info message explaining non-cancellable policy

#### API Changes
- POST `/reservations/` automatically sets `is_short_notice` flag
- GET `/courts/availability` returns `short_notice` status in grid data
- GET `/reservations/` includes `is_short_notice` field in response
- Enhanced validation messages for different cancellation scenarios

### Business Rules

1. **Classification**: Booking within 15 minutes of start time → short notice
2. **Booking Window**: 15 minutes before start time until end of slot
3. **Reservation Limit**: Short notice bookings excluded from 2-reservation limit
4. **Short Notice Limit**: Members can have only 1 active short notice booking at a time
5. **Cancellation**: Cannot cancel within 15 minutes of start OR once started
6. **All Other Constraints**: Court availability, authentication, time slots still apply

### German Language Support

- "Kurzfristig gebucht für [Name] von [Name]" - Grid display text
- "Kurzfristige Buchung erfolgreich erstellt!" - Success message
- "Kurzfristige Buchungen können nicht storniert werden" - Cancellation info
- "Sie haben bereits eine aktive kurzfristige Buchung. Nur eine kurzfristige Buchung pro Mitglied ist erlaubt." - Short notice limit error message
- "Diese Buchung wurde innerhalb von 15 Minuten vor Spielbeginn erstellt" - Explanation

## Enhanced Admin Panel Features

### Advanced Block Management

The enhanced admin panel provides comprehensive block management capabilities including recurring blocks, templates, and customizable reasons.

#### Calendar View

The admin panel features a calendar-based interface for visualizing and managing blocks:

**Calendar Components**:
- Monthly calendar grid with day cells showing block indicators
- Color-coded blocks by reason type (maintenance=blue, weather=gray, tournament=green, championship=gold)
- Series indicators showing linked recurring blocks
- Hover tooltips with detailed block information
- Click-to-edit functionality for individual blocks

**Visual Indicators**:
- Single blocks: Solid color bars
- Recurring series: Striped pattern with series name
- Modified instances: Dotted border indicating deviation from series pattern
- Conflicting reservations: Red warning icons

#### Recurring Block Series Management

**Series Creation**:
- Start and end date selection (both required)
- Recurrence pattern selection (daily, weekly, monthly)
- Day-of-week selection for weekly patterns
- Multi-court selection for simultaneous blocking
- Reason and sub-reason assignment

**Series Editing Options**:
- Edit entire series: Applies changes to all future instances
- Edit from date: Applies changes to instances from specified date forward
- Edit single instance: Modifies only the selected occurrence
- Visual feedback showing which instances will be affected

**Series Deletion Options**:
- Delete single occurrence: Removes only the selected instance
- Delete future occurrences: Removes all instances from specified date forward
- Delete entire series: Removes all instances (past and future)

#### Block Templates

**Template Features**:
- Save frequently used block configurations
- Include court selection, time ranges, reasons, and recurrence patterns
- Quick application to create new blocks
- Template management (create, edit, delete)

**Template Application**:
- Pre-fills block creation form with template values
- Allows date override while preserving other settings
- Supports both single blocks and recurring series templates

#### Customizable Block Reasons

**Reason Management Interface**:
- Add, edit, and delete custom block reasons
- Usage tracking to prevent deletion of reasons in use
- Historical preservation when editing or deleting reasons
- Default reasons provided but fully customizable

**Sub-Reason Support**:
- Optional additional detail for blocks (e.g., "Team A vs Team B" for Championship)
- Sub-reason templates for common scenarios
- Combined display format: "Championship - Team A vs Team B"
- Filtering support for both main reason and sub-reason

#### Bulk Operations

**Multi-Selection**:
- Checkbox selection for multiple blocks
- Bulk deletion with single confirmation
- Bulk editing for common properties
- Series-aware operations (select entire series or individual instances)

**Conflict Management**:
- Preview affected reservations before creating blocks
- Automatic cancellation of conflicting reservations
- Email notifications to affected members with block reason
- Conflict resolution options for administrators

#### Filtering and Search

**Advanced Filters**:
- Date range selection
- Court selection (single or multiple)
- Reason and sub-reason filtering
- Block type filtering (single vs recurring series)
- Administrator filtering (who created the block)

**Search Functionality**:
- Text search in block reasons and sub-reasons
- Series name search
- Quick filters for common scenarios (today's blocks, upcoming maintenance, etc.)

#### Audit Trail

**Operation Logging**:
- Complete audit log of all block operations
- Timestamp and administrator identification
- Operation details stored as JSON
- Filterable audit history

**Logged Operations**:
- Block creation (single and series)
- Block modifications (single instance and series-wide)
- Block deletions (single, bulk, and series)
- Template operations
- Reason management operations

### German Language Support for Enhanced Features

**Recurring Block Terms**:
- "Wiederkehrende Sperrung" - Recurring block
- "Serie bearbeiten" - Edit series
- "Einzelne Instanz bearbeiten" - Edit single instance
- "Alle zukünftigen Instanzen" - All future instances
- "Gesamte Serie löschen" - Delete entire series

**Template Terms**:
- "Sperrungsvorlage" - Block template
- "Vorlage anwenden" - Apply template
- "Vorlage speichern" - Save template

**Reason Management Terms**:
- "Sperrungsgrund verwalten" - Manage block reason
- "Untergrund" - Sub-reason
- "Grund wird verwendet" - Reason is in use
- "Historische Daten bleiben erhalten" - Historical data will be preserved

**Calendar Terms**:
- "Kalenderansicht" - Calendar view
- "Monatliche Ansicht" - Monthly view
- "Konflikt-Vorschau" - Conflict preview
- "Betroffene Buchungen" - Affected reservations

## User Feedback and Notifications

### Advanced Block Management

The enhanced admin panel provides comprehensive block management capabilities including recurring blocks, templates, and customizable reasons.

#### Calendar View

The admin panel features a calendar-based interface for visualizing and managing blocks:

**Calendar Components**:
- Monthly calendar grid with day cells showing block indicators
- Color-coded blocks by reason type (maintenance=blue, weather=gray, tournament=green, championship=gold)
- Series indicators showing linked recurring blocks
- Hover tooltips with detailed block information
- Click-to-edit functionality for individual blocks

**Visual Indicators**:
- Single blocks: Solid color bars
- Recurring series: Striped pattern with series name
- Modified instances: Dotted border indicating deviation from series pattern
- Conflicting reservations: Red warning icons

#### Recurring Block Series Management

**Series Creation**:
- Start and end date selection (both required)
- Recurrence pattern selection (daily, weekly, monthly)
- Day-of-week selection for weekly patterns
- Multi-court selection for simultaneous blocking
- Reason and sub-reason assignment

**Series Editing Options**:
- Edit entire series: Applies changes to all future instances
- Edit from date: Applies changes to instances from specified date forward
- Edit single instance: Modifies only the selected occurrence
- Visual feedback showing which instances will be affected

**Series Deletion Options**:
- Delete single occurrence: Removes only the selected instance
- Delete future occurrences: Removes all instances from specified date forward
- Delete entire series: Removes all instances (past and future)

#### Block Templates

**Template Features**:
- Save frequently used block configurations
- Include court selection, time ranges, reasons, and recurrence patterns
- Quick application to create new blocks
- Template management (create, edit, delete)

**Template Application**:
- Pre-fills block creation form with template values
- Allows date override while preserving other settings
- Supports both single blocks and recurring series templates

#### Customizable Block Reasons

**Reason Management Interface**:
- Add, edit, and delete custom block reasons
- Usage tracking to prevent deletion of reasons in use
- Historical preservation when editing or deleting reasons
- Default reasons provided but fully customizable

**Sub-Reason Support**:
- Optional additional detail for blocks (e.g., "Team A vs Team B" for Championship)
- Sub-reason templates for common scenarios
- Combined display format: "Championship - Team A vs Team B"
- Filtering support for both main reason and sub-reason

#### Bulk Operations

**Multi-Selection**:
- Checkbox selection for multiple blocks
- Bulk deletion with single confirmation
- Bulk editing for common properties
- Series-aware operations (select entire series or individual instances)

**Conflict Management**:
- Preview affected reservations before creating blocks
- Automatic cancellation of conflicting reservations
- Email notifications to affected members with block reason
- Conflict resolution options for administrators

#### Filtering and Search

**Advanced Filters**:
- Date range selection
- Court selection (single or multiple)
- Reason and sub-reason filtering
- Block type filtering (single vs recurring series)
- Administrator filtering (who created the block)

**Search Functionality**:
- Text search in block reasons and sub-reasons
- Series name search
- Quick filters for common scenarios (today's blocks, upcoming maintenance, etc.)

#### Audit Trail

**Operation Logging**:
- Complete audit log of all block operations
- Timestamp and administrator identification
- Operation details stored as JSON
- Filterable audit history

**Logged Operations**:
- Block creation (single and series)
- Block modifications (single instance and series-wide)
- Block deletions (single, bulk, and series)
- Template operations
- Reason management operations

### German Language Support for Enhanced Features

**Recurring Block Terms**:
- "Wiederkehrende Sperrung" - Recurring block
- "Serie bearbeiten" - Edit series
- "Einzelne Instanz bearbeiten" - Edit single instance
- "Alle zukünftigen Instanzen" - All future instances
- "Gesamte Serie löschen" - Delete entire series

**Template Terms**:
- "Sperrungsvorlage" - Block template
- "Vorlage anwenden" - Apply template
- "Vorlage speichern" - Save template

**Reason Management Terms**:
- "Sperrungsgrund verwalten" - Manage block reason
- "Untergrund" - Sub-reason
- "Grund wird verwendet" - Reason is in use
- "Historische Daten bleiben erhalten" - Historical data will be preserved

**Calendar Terms**:
- "Kalenderansicht" - Calendar view
- "Monatliche Ansicht" - Monthly view
- "Konflikt-Vorschau" - Conflict preview
- "Betroffene Buchungen" - Affected reservations

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
| Short Notice Reservation Created | Kurzfristige Buchung erfolgreich erstellt! |
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
| RESERVATION_LIMIT | Sie haben bereits 2 aktive reguläre Buchungen |
| BLOCKED_SLOT | Dieser Platz ist für diese Zeit gesperrt |
| INVALID_TIME | Buchungen sind nur zwischen 06:00 und 21:00 Uhr möglich |
| PAST_BOOKING | Buchungen in der Vergangenheit sind nicht möglich |
| SLOT_ENDED | Dieser Zeitslot ist bereits beendet |
| CANCELLATION_TOO_LATE | Diese Buchung kann nicht mehr storniert werden (weniger als 15 Minuten bis Spielbeginn) |
| CANCELLATION_STARTED | Diese Buchung kann nicht mehr storniert werden (Spielzeit bereits begonnen) |
| SHORT_NOTICE_NON_CANCELLABLE | Kurzfristige Buchungen können nicht storniert werden |
| INVALID_CREDENTIALS | E-Mail oder Passwort ist falsch |
| UNAUTHORIZED | Sie haben keine Berechtigung für diese Aktion |
| NOT_FOUND | Die angeforderte Ressource wurde nicht gefunden |
| EMAIL_FAILED | E-Mail konnte nicht gesendet werden | nicht gesendet werden |

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
    'firstname': st.text(min_size=1, max_size=50),
    'lastname': st.text(min_size=1, max_size=50),
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

@given(court=court_numbers, booking_date=future_dates, start=booking_times)
def test_property_40_short_notice_classification(court, booking_date, start):
    """Feature: tennis-club-reservation, Property 40: Short notice booking classification
    Validates: Requirements 18.1"""
    # Mock current time to be 10 minutes before start time
    booking_datetime = datetime.combine(booking_date, start)
    current_time = booking_datetime - timedelta(minutes=10)
    
    with patch('datetime.datetime.now', return_value=current_time):
        reservation = create_test_reservation(court_id=court, date=booking_date, start_time=start)
        assert reservation.is_short_notice == True

@given(member_id=st.integers(min_value=1))
def test_property_41_short_notice_excluded_from_limit(member_id):
    """Feature: tennis-club-reservation, Property 41: Short notice bookings excluded from reservation limit
    Validates: Requirements 18.2, 18.3"""
    # Create 2 regular reservations
    create_test_reservation(booked_for_id=member_id, is_short_notice=False)
    create_test_reservation(booked_for_id=member_id, is_short_notice=False)
    
    # Short notice booking should still be allowed
    short_notice_reservation = create_test_reservation(booked_for_id=member_id, is_short_notice=True)
    assert short_notice_reservation.is_short_notice == True
    
    # Regular reservation should fail
    with pytest.raises(ValidationError, match="2 aktive reguläre Buchungen"):
        create_test_reservation(booked_for_id=member_id, is_short_notice=False)

@given(reservation_id=st.integers(min_value=1))
def test_property_46_cancellation_prevented_within_15_minutes_and_during_slot(reservation_id):
    """Feature: tennis-club-reservation, Property 46: Cancellation prevented within 15 minutes and during slot time
    Validates: Requirements 2.3, 2.4"""
    reservation = create_test_reservation_with_id(reservation_id, 
                                                 date=date.today(), 
                                                 start_time=time(14, 0))
    
    # Test 1: Mock current time to be 10 minutes before start (should fail)
    current_time = datetime.combine(date.today(), time(13, 50))
    with patch('datetime.datetime.now', return_value=current_time):
        with pytest.raises(ValidationError, match="weniger als 15 Minuten"):
            ReservationService.cancel_reservation(reservation_id)
    
    # Test 2: Mock current time to be during the slot (should fail)
    current_time = datetime.combine(date.today(), time(14, 30))
    with patch('datetime.datetime.now', return_value=current_time):
        with pytest.raises(ValidationError, match="bereits begonnen"):
            ReservationService.cancel_reservation(reservation_id)
    
    # Test 3: Mock current time to be 20 minutes before start (should succeed)
    current_time = datetime.combine(date.today(), time(13, 40))
    with patch('datetime.datetime.now', return_value=current_time):
        result = ReservationService.cancel_reservation(reservation_id)
        assert result == True

# Enhanced admin panel property tests
@given(start_date=future_dates, end_date=future_dates, 
       recurrence_pattern=st.sampled_from(['daily', 'weekly', 'monthly']))
def test_property_48_recurring_block_series_generation(start_date, end_date, recurrence_pattern):
    """Feature: tennis-club-reservation, Property 48: Recurring block series generation
    Validates: Requirements 19.1"""
    assume(end_date >= start_date)  # Ensure valid date range
    
    series_data = {
        'court_ids': [1, 2],
        'start_date': start_date,
        'end_date': end_date,
        'start_time': time(10, 0),
        'end_time': time(12, 0),
        'recurrence_pattern': recurrence_pattern,
        'reason_id': 1,
        'admin_id': 1
    }
    
    blocks, error = BlockService.create_recurring_block_series(**series_data)
    assert error is None
    assert len(blocks) > 0
    
    # Verify all blocks have correct series linkage
    series_id = blocks[0].series_id
    for block in blocks:
        assert block.series_id == series_id
        assert block.start_time == time(10, 0)
        assert block.end_time == time(12, 0)

@given(court_ids=st.lists(st.integers(min_value=1, max_value=6), min_size=1, max_size=6))
def test_property_54_multi_court_block_creation(court_ids):
    """Feature: tennis-club-reservation, Property 54: Multi-court block creation
    Validates: Requirements 19.10"""
    block_data = {
        'court_ids': court_ids,
        'date': date.today() + timedelta(days=1),
        'start_time': time(14, 0),
        'end_time': time(16, 0),
        'reason_id': 1,
        'admin_id': 1
    }
    
    blocks, error = BlockService.create_multi_court_blocks(**block_data)
    assert error is None
    assert len(blocks) == len(court_ids)
    
    # Verify blocks created for all courts with same parameters
    for i, block in enumerate(blocks):
        assert block.court_id == court_ids[i]
        assert block.date == block_data['date']
        assert block.start_time == block_data['start_time']
        assert block.end_time == block_data['end_time']

@given(reason_name=st.text(min_size=1, max_size=50))
def test_property_64_block_reason_creation_and_availability(reason_name):
    """Feature: tennis-club-reservation, Property 64: Block reason creation and availability
    Validates: Requirements 20.2"""
    assume(reason_name.strip())  # Ensure non-empty after stripping
    
    reason, error = BlockReasonService.create_block_reason(reason_name.strip(), admin_id=1)
    assert error is None
    assert reason.name == reason_name.strip()
    
    # Verify reason is available for block creation
    available_reasons = BlockReasonService.get_all_block_reasons()
    reason_names = [r.name for r in available_reasons]
    assert reason_name.strip() in reason_names
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
   flask create-admin --firstname "Admin" --lastname "User" --email "admin@tennisclub.de"
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
