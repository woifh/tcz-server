# Tennis Club Reservation System - Architecture

This document provides an overview of the system architecture, key components, and design decisions.

## Table of Contents

1. [System Overview](#system-overview)
2. [Technology Stack](#technology-stack)
3. [Project Structure](#project-structure)
4. [Core Components](#core-components)
5. [Database Schema](#database-schema)
6. [Security Features](#security-features)
7. [Design Patterns](#design-patterns)
8. [Deployment](#deployment)

## System Overview

The Tennis Club Reservation System is a web application for managing tennis court reservations for club members. Key features include:

- **Member Management**: User registration, authentication, and profile management
- **Court Reservations**: Create, view, edit, and cancel court bookings
- **Batch Reservations**: Create multiple reservations at once for recurring bookings
- **Court Blocking**: Administrators can block courts for maintenance or events
- **Email Notifications**: Automated emails for reservation confirmations and updates
- **Admin Dashboard**: Comprehensive administration interface with member management and audit logs

## Technology Stack

### Backend
- **Flask 3.0+** - Python web framework
- **SQLAlchemy** - ORM for database operations
- **Flask-Login** - User session management
- **Flask-Migrate** - Database migration management (Alembic)
- **Flask-Mail** - Email sending functionality
- **Flask-Limiter** - Rate limiting for API endpoints
- **PyMySQL** - MySQL database driver

### Frontend
- **Jinja2** - Server-side templating
- **Tailwind CSS 3.0+** - Utility-first CSS framework
- **JavaScript (Vanilla)** - Client-side interactivity
- **HTML5/CSS3** - Modern web standards

### Database
- **MySQL** - Production database (PythonAnywhere)
- **SQLite** - Development/testing database

### Deployment
- **PythonAnywhere** - Production hosting
- **Git/GitHub** - Version control and deployment pipeline
- **WSGI** - Production server interface

## Project Structure

```
tcz/
├── app/                      # Main application package
│   ├── __init__.py          # Application factory
│   ├── models.py            # Database models
│   ├── routes/              # Route blueprints
│   │   ├── auth.py         # Authentication routes
│   │   ├── main.py         # Main application routes
│   │   └── admin.py        # Admin dashboard routes
│   ├── services/            # Business logic layer
│   │   ├── reservation_service.py
│   │   ├── email_service.py
│   │   └── blocking_service.py
│   ├── forms/               # WTForms form definitions
│   │   ├── auth.py
│   │   ├── reservation.py
│   │   └── admin.py
│   ├── templates/           # Jinja2 templates
│   │   ├── base.html
│   │   ├── auth/
│   │   ├── reservation/
│   │   └── admin/
│   └── static/              # Static assets (CSS, JS, images)
│       ├── css/
│       ├── js/
│       └── images/
├── tests/                   # Test suite
│   ├── test_models.py
│   ├── test_routes.py
│   └── test_services.py
├── migrations/              # Database migrations
│   └── versions/
├── scripts/                 # Utility scripts
│   ├── deploy/             # Deployment scripts
│   ├── setup/              # Initial setup scripts
│   ├── database/           # Database utilities
│   └── dev/                # Development utilities
├── docs/                    # Documentation
│   ├── DEPLOYMENT.md       # Deployment guide
│   ├── ARCHITECTURE.md     # This file
│   └── archive/            # Historical documentation
├── config.py               # Configuration classes
├── wsgi.py                 # WSGI entry point
├── requirements.txt        # Python dependencies
├── .env.example            # Environment template (development)
├── .env.production.example # Environment template (production)
└── README.md               # Project overview
```

## Core Components

### Application Factory Pattern

The application uses Flask's application factory pattern (`app/__init__.py`):

```python
def create_app(config_name='development'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    limiter.init_app(app)

    # Register blueprints
    from app.routes import auth, main, admin
    app.register_blueprint(auth.bp)
    app.register_blueprint(main.bp)
    app.register_blueprint(admin.bp)

    return app
```

**Benefits:**
- Multiple configurations (development, testing, production)
- Easier testing with different app instances
- Cleaner separation of concerns

### Models Layer (`app/models.py`)

Key models:

#### Member
- User accounts with authentication
- Roles: `member`, `teamster` (Team Leader), `administrator`
- Password hashing with Werkzeug
- Relationships to reservations and audit logs
- Notification preferences (own bookings, others' bookings, blocking, overrides)

#### Court
- Tennis court entities (numbered 1-6)
- Status tracking: `available`, `maintenance`, `blocked`

#### Reservation
- Court bookings with date/time/duration
- Links to member and court
- Batch ID for recurring reservations
- Status tracking: `active`, `cancelled`

#### CourtBlock
- Administrative court blocking
- Date range and reason
- Links to creator (admin)

#### MemberAuditLog
- Tracks all member data changes
- Who changed what, when
- Before/after values

### Services Layer (`app/services/`)

Business logic is separated from routes:

#### `reservation_service.py`
- Complex reservation logic
- Availability checking
- Batch reservation creation
- Conflict detection

#### `email_service.py`
- Email notification sending
- Template rendering
- Development mode email redirection
- Error handling and logging

#### `blocking_service.py`
- Court blocking logic
- Date validation
- Conflict checking with reservations

### Routes Layer (`app/routes/`)

Request handling organized by feature:

#### `auth.py`
- Login/logout
- Registration
- Password reset
- Email verification

#### `main.py`
- Reservation CRUD
- Court availability
- Member dashboard
- Batch operations

#### `admin.py`
- Admin dashboard
- Member management (CRUD with audit)
- Court blocking
- System statistics

### Forms Layer (`app/forms/`)

WTForms for validation and CSRF protection:

```python
class ReservationForm(FlaskForm):
    court = SelectField('Court', coerce=int)
    date = DateField('Date', validators=[DataRequired()])
    start_time = TimeField('Start Time', validators=[DataRequired()])
    duration = SelectField('Duration', coerce=int, choices=[(30, '30 min'), ...])
```

## Database Schema

### Entity Relationship Diagram

```
Member (1) ───< (N) Reservation (N) >─── (1) Court
   │                    │
   │                    │
   └─< (N) MemberAuditLog    CourtBlock >─┘
           (tracks changes)  (blocks court)
```

### Key Relationships

- **Member → Reservations**: One-to-many (member can have multiple reservations)
- **Court → Reservations**: One-to-many (court can be reserved multiple times)
- **Member → MemberAuditLog**: One-to-many (audit trail of changes)
- **Member → CourtBlock**: One-to-many (admin creates blocks)
- **Court → CourtBlock**: One-to-many (court can be blocked multiple times)

### Indexes and Constraints

- **Unique constraints**: Member email, Court number
- **Foreign keys**: All relationships enforced with CASCADE options
- **Indexes**: Date/time fields for reservation queries

## Security Features

### Authentication
- **Password hashing**: Werkzeug PBKDF2 with salt
- **Session management**: Flask-Login with secure cookies
- **Remember me**: Optional persistent login

### Authorization
- **Role-based access**: Three roles - Member, Teamster (Team Leader), Administrator
- **Route protection**: `@login_required`, `@teamster_required`, and `@admin_required` decorators
- **Template-level checks**: `current_user.role` checks in Jinja2
- **JWT authentication**: Mobile API uses JWT tokens for stateless authentication

### Input Validation
- **WTForms validation**: All user input validated server-side
- **CSRF protection**: All forms include CSRF tokens
- **SQL injection prevention**: SQLAlchemy parameterized queries
- **XSS prevention**: Jinja2 automatic escaping

### Rate Limiting
- **Flask-Limiter**: Prevents brute force attacks
- **Configurable limits**: Per-route and global limits
- **Production-only**: Disabled in development for easier testing

### Security Headers
- **Content-Security-Policy**: Restricts resource loading
- **X-Frame-Options**: Prevents clickjacking
- **X-Content-Type-Options**: Prevents MIME sniffing

## Design Patterns

### Application Factory
Creates app instances with different configurations.

### Blueprint Architecture
Modular route organization by feature area.

### Service Layer Pattern
Business logic separated from request handling.

### Repository Pattern (implicit)
SQLAlchemy models act as repositories for data access.

### Dependency Injection
Extensions initialized and injected via Flask app context.

### Template Inheritance
Base template with block overrides for DRY templates.

### Form Object Pattern
WTForms encapsulate validation and rendering logic.

## Deployment

### Development
```bash
# Local SQLite database
# Flask development server
# Email redirection to developer
flask run
```

### Production (PythonAnywhere)
```bash
# MySQL database
# WSGI production server
# Real email sending
# See docs/DEPLOYMENT.md
```

### Configuration Management

Three configuration classes in `config.py`:

1. **DevelopmentConfig**: SQLite, debug mode, relaxed security
2. **TestingConfig**: In-memory database, testing mode
3. **ProductionConfig**: MySQL, security enabled, no debug

Environment variables loaded from:
- `.env` - Development
- `.env.production` - Production

### Deployment Workflow

1. **Develop locally** with SQLite
2. **Run tests** with pytest
3. **Commit and push** to GitHub
4. **Deploy to PythonAnywhere**:
   - Run `scripts/deploy/pythonanywhere.sh`
   - Pulls latest code
   - Runs migrations
   - Reloads web app

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions.

## Historical Context

This system has undergone several major refactorings:

1. **Initial implementation**: Basic reservation system
2. **Batch reservations**: Added recurring booking functionality
3. **Court blocking**: Administrative court management
4. **Email notifications**: Automated member communications
5. **Admin dashboard**: Enhanced administration capabilities with audit logs
6. **Security hardening**: Added rate limiting, CSRF, and security headers
7. **Project reorganization** (Latest): Cleaned up structure, consolidated scripts

For historical details, see [`docs/archive/`](archive/) documentation.

## Contributing

When making changes:

1. **Follow patterns**: Use existing patterns for consistency
2. **Write tests**: Add tests to `tests/` directory
3. **Document changes**: Update this file for architectural changes
4. **Use services**: Put business logic in services, not routes
5. **Validate input**: All user input must be validated
6. **Check security**: Consider security implications of changes

## Related Documentation

- **Deployment Guide**: [DEPLOYMENT.md](DEPLOYMENT.md)
- **Project Organization**: [REORGANIZATION_PLAN.md](REORGANIZATION_PLAN.md)
- **Database Scripts**: [scripts/database/README.md](../scripts/database/README.md)
- **Deployment Scripts**: [scripts/deploy/README.md](../scripts/deploy/README.md)
