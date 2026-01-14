# Tennis Club Court Reservation System

A comprehensive web-based court reservation system for tennis clubs, built with Flask, SQLAlchemy, and Tailwind CSS. Features include member management, court booking, administrative controls, and email notifications—all in German.

## 🚀 Quick Start

### Python 3.13 Compatible Setup
```bash
# One-time setup (handles Python 3.13 compatibility)
./scripts/setup/setup_env.sh

# Start development server
./scripts/dev/run_dev.sh
```

The application will be available at http://127.0.0.1:5000

### Manual Setup
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies (Python 3.13 compatible versions)
pip install -r requirements.txt

# Start development server
export FLASK_ENV=development
python wsgi.py
```

## 🎾 Features

### For Members
- **Court Reservations**: Book tennis courts with an intuitive visual grid interface
- **Availability View**: See real-time court availability (available/reserved/blocked)
- **One-Click Cancellation**: Cancel reservations directly from the dashboard by clicking on your bookings
- **Favourites System**: Maintain a list of preferred playing partners for quick booking
- **Booking on Behalf**: Book courts for yourself or any of your favourite members
- **Email Notifications**: Receive German-language emails for all booking events
- **Responsive Design**: Access from desktop, tablet, or mobile devices
- **Flexible Booking**: Reserve courts for 1-hour slots between 08:00-22:00
- **Booking Management**: View, modify, and cancel your reservations from multiple locations

### For Administrators
- **Member Management**: Create, update, and delete member accounts
- **Court Blocking**: Block courts for maintenance, weather, or events
- **Override Capabilities**: Cancel any reservation with reason tracking
- **Full Visibility**: View all reservations and blocks across the system
- **Role-Based Access**: Separate permissions for members and administrators

### Technical Features
- **Property-Based Testing**: Comprehensive test coverage using Hypothesis
- **Secure Authentication**: Password hashing with Flask-Login
- **Email Integration**: SMTP support for notifications
- **Database Migrations**: Flask-Migrate for schema management
- **German Localization**: All interface text and messages in German
- **Modern UI**: Tailwind CSS for responsive, attractive design

## 🛠️ Technology Stack

- **Backend**: Flask 3.0+, Python 3.10+
- **Database**: SQLAlchemy 2.0+ (MySQL/SQLite)
- **Authentication**: Flask-Login
- **Email**: Flask-Mail
- **Frontend**: HTML5, Tailwind CSS 3.0+, Vanilla JavaScript
- **Testing**: Pytest, Hypothesis (Property-Based Testing)
- **Deployment**: PythonAnywhere (WSGI)

## 📋 Prerequisites

- Python 3.10 or higher
- MySQL (for production) or SQLite (for development)
- SMTP server credentials (Gmail, SendGrid, etc.)

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd tennis-club-reservation
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root:

```env
# Flask Configuration
SECRET_KEY=your-secret-key-here
FLASK_ENV=development

# Database (SQLite for development)
DATABASE_URL=sqlite:///instance/tennis_club.db

# Email Configuration (optional for development)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=noreply@tennisclub.de
```

### 5. Initialize Database

```bash
# Option 1: Using the initialization script
python scripts/setup/init_database.py

# Option 2: Using Flask CLI commands
flask db upgrade
python scripts/database/seed.py

# Option 3: Create admin separately
python scripts/setup/create_admin.py
```

### 6. Run the Application

```bash
flask run
```

Visit `http://localhost:5000` in your browser.

## 🎯 Key User Workflows

### Making a Reservation
1. Log in to the system
2. Select a date from the date picker on the dashboard
3. Click on any green (available) slot in the grid
4. Choose who to book for (yourself or a favourite)
5. Click "Buchung bestätigen" to confirm
6. The slot turns red and you receive a confirmation

### Cancelling a Reservation
**From Dashboard (Quick Method):**
1. Navigate to the dashboard
2. Find your reservation (red slot with your name)
3. Click directly on the reservation
4. Confirm the cancellation dialog
5. The slot turns green (available) again

**From Reservations Page:**
1. Click "Meine Buchungen" in navigation
2. Find the reservation in your list
3. Click the cancel button
4. Confirm cancellation

### Managing Favourites
1. Click "Meine Favoriten" in navigation
2. Click "Favorit hinzufügen" button
3. Select a member from the dropdown
4. Click "Hinzufügen"
5. The member appears in your favourites list
6. Use favourites when booking to quickly select them

### Booking for Others
1. Add members to your favourites first
2. When booking, select their name from "Gebucht für" dropdown
3. They can view and cancel the reservation
4. Both of you receive email notifications

## 📚 Documentation

- **[Deployment Guide](docs/DEPLOYMENT.md)**: Step-by-step PythonAnywhere deployment
- **[Architecture](docs/ARCHITECTURE.md)**: System architecture and design decisions
- **[Database Scripts](scripts/database/README.md)**: Database utility scripts
- **[Deployment Scripts](scripts/deploy/README.md)**: Deployment workflow and scripts
- **[Setup Scripts](scripts/setup/)**: Initial setup and admin creation

## 🧪 Testing

The system includes comprehensive property-based tests using Hypothesis:

```bash
# Run all tests
pytest

# Run specific test modules
pytest tests/test_auth.py
pytest tests/test_reservation_service.py
pytest tests/test_validation_service.py

# Run with coverage
pytest --cov=app tests/
```

### Property-Based Testing

The system uses Hypothesis for property-based testing, which validates correctness properties across many randomly generated inputs:

- **Authentication**: Login, logout, session management
- **Reservations**: Creation, modification, cancellation, access control
- **Validation**: Time slots, reservation limits, conflicts, blocks
- **Member Management**: CRUD operations, favourites
- **Email**: Notifications in German for all events

## 🔧 Utility Scripts

### Setup & Initialization
```bash
# Create admin user (interactive)
python scripts/setup/create_admin.py

# Seed database with courts
python scripts/database/seed.py

# Initialize database
python scripts/setup/init_database.py
```

### Database Management
```bash
# Database migrations
flask db upgrade              # Apply migrations
flask db migrate              # Create new migration
flask db current              # Show current version

# Database utilities
python scripts/database/inspect_structure.py  # View schema
python scripts/database/inspect_data.py       # View data
python scripts/database/fix_migration.py      # Fix version issues
```

### Deployment
```bash
# Deploy to PythonAnywhere
./scripts/deploy/pythonanywhere.sh

# Test email configuration
flask test-email your-email@example.com
```

## 📁 Project Structure

```
tcz/
├── app/                      # Main application package
│   ├── __init__.py          # Flask app factory
│   ├── models.py            # Database models
│   ├── routes/              # Route blueprints
│   │   ├── auth.py         # Authentication
│   │   ├── main.py         # Main routes
│   │   └── admin.py        # Admin dashboard
│   ├── services/            # Business logic
│   │   ├── reservation_service.py
│   │   ├── email_service.py
│   │   └── blocking_service.py
│   ├── forms/               # WTForms definitions
│   ├── templates/           # Jinja2 templates
│   └── static/              # CSS, JS, images
├── tests/                   # Official test suite
├── migrations/              # Database migrations
├── scripts/                 # Utility scripts
│   ├── deploy/             # Deployment scripts
│   │   ├── pythonanywhere.sh
│   │   └── README.md
│   ├── setup/              # Initial setup
│   │   ├── create_admin.py
│   │   ├── init_database.py
│   │   └── setup_*.sh
│   ├── database/           # Database tools
│   │   ├── seed.py
│   │   ├── recreate.py
│   │   ├── fix_migration.py
│   │   └── README.md
│   └── dev/                # Development utilities
│       ├── debug/          # Archived debug scripts
│       └── archived_tests/ # Archived ad-hoc tests
├── docs/                    # Documentation
│   ├── DEPLOYMENT.md       # Deployment guide
│   ├── ARCHITECTURE.md     # System architecture
│   └── archive/            # Historical docs
├── config.py               # Configuration
├── wsgi.py                 # WSGI entry point
├── requirements.txt        # Dependencies
├── .env.example            # Dev environment template
├── .env.production.example # Prod environment template
└── README.md               # This file
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed architecture documentation.

## 🔐 Security Features

- **Password Hashing**: Secure password storage using Werkzeug
- **Session Management**: Flask-Login for secure sessions
- **Authorization**: Role-based access control (member/administrator)
- **CSRF Protection**: Built-in Flask security
- **Input Validation**: Comprehensive validation on all inputs
- **SQL Injection Prevention**: SQLAlchemy ORM parameterized queries

## 🌍 Localization

All user-facing text is in German:
- Interface labels and buttons
- Email notifications
- Error messages
- Success messages
- Date formatting (DD.MM.YYYY)

## 📧 Email Notifications

The system sends German-language email notifications for:
- Booking creation
- Booking modification
- Booking cancellation
- Admin overrides
- Block-related cancellations

## 🎨 User Interface

### Dashboard Features
- **Responsive Design**: Works seamlessly on desktop, tablet, and mobile devices
- **Color-Coded Grid**: 
  - 🟢 Green: Available slots (click to book)
  - 🔴 Red: Reserved slots (click your own to cancel)
  - ⚫ Grey: Blocked slots (maintenance/weather)
- **Interactive Booking**: Click any available slot to open booking modal
- **One-Click Cancellation**: Click your own reservations to cancel them instantly
- **Smart Authorization**: Only your reservations are clickable for cancellation
- **Real-Time Updates**: AJAX-based updates without page reload
- **Touch-Friendly**: Optimized for mobile touch interactions

### Booking Workflow
1. **Select Date**: Choose date from date picker
2. **View Availability**: See color-coded grid for all 6 courts
3. **Book Court**: Click green slot → Select who to book for → Confirm
4. **Cancel Booking**: Click your red slot → Confirm cancellation
5. **Instant Feedback**: Grid updates immediately with success message

### Favourites Management
- **Dedicated Page**: "Meine Favoriten" in navigation
- **Quick Access**: Add/remove favourite members
- **Fast Booking**: Book courts for favourites without searching
- **Visual List**: See all your favourites with email addresses

## 🚀 Deployment

### PythonAnywhere

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for complete deployment instructions.

Quick deployment:
```bash
# On PythonAnywhere bash console
cd ~/tcz
./scripts/deploy/pythonanywhere.sh
```

The script handles:
- Git pull
- Dependency updates
- Database migrations
- Configuration checks

### Other Platforms

The application can be deployed to any platform supporting WSGI:
- Heroku
- AWS Elastic Beanstalk
- Google Cloud Platform
- DigitalOcean App Platform
- Your own server with Gunicorn/uWSGI

## 🤝 Contributing

This is a complete, production-ready system. For modifications:

1. Review the design document in `.kiro/specs/tennis-club-reservation/`
2. Follow the existing code structure
3. Add tests for new features
4. Ensure all tests pass before committing
5. Update documentation as needed

## 📝 License

[Add your license here]

## 👥 Authors

[Add author information here]

## 🙏 Acknowledgments

- Built with Flask and SQLAlchemy
- UI styled with Tailwind CSS
- Testing powered by Pytest and Hypothesis
- Deployed on PythonAnywhere

## 📞 Support

For issues or questions:
- Check the documentation in the `.kiro/specs/` directory
- Review error logs in the application
- Consult the deployment guide for platform-specific issues

## 🔄 Version History

See [CHANGELOG.md](CHANGELOG.md) for the complete version history.

**Current Version: v3.6.0** (2026-01-14)

Recent highlights:
- Mobile API with JWT authentication
- Email notification preferences per member
- Member profile editing
- Teamster (Team Leader) role
- CSRF protection for all forms
- Performance optimizations
- Enhanced admin dashboard with audit logging

- **v1.0.0** - Initial release
  - Complete booking system
  - Member and admin management
  - Email notifications
  - Property-based testing
  - German localization
  - Responsive design
  - PythonAnywhere deployment ready
