# Tennis Club Court Reservation System

A comprehensive web-based court reservation system for tennis clubs, built with Flask, SQLAlchemy, and Tailwind CSS. Features include member management, court booking, administrative controls, and email notifications—all in German.

## 🎾 Features

### For Members
- **Court Reservations**: Book tennis courts with an intuitive visual grid interface
- **Availability View**: See real-time court availability (available/reserved/blocked)
- **Favourites System**: Maintain a list of preferred playing partners for quick booking
- **Email Notifications**: Receive German-language emails for all booking events
- **Responsive Design**: Access from desktop, tablet, or mobile devices
- **Flexible Booking**: Reserve courts for 1-hour slots between 06:00-21:00
- **Booking Management**: View, modify, and cancel your reservations

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
python3 init_db.py

# Option 2: Using Flask CLI commands
flask db upgrade
flask init-courts
flask create-admin
```

### 6. Run the Application

```bash
flask run
```

Visit `http://localhost:5000` in your browser.

## 📚 Documentation

- **[Setup Guide](SETUP_GUIDE.md)**: Detailed installation and configuration instructions
- **[Deployment Guide](DEPLOYMENT.md)**: Step-by-step PythonAnywhere deployment
- **[Requirements](/.kiro/specs/tennis-club-reservation/requirements.md)**: Complete system requirements
- **[Design Document](/.kiro/specs/tennis-club-reservation/design.md)**: Architecture and design decisions

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

## 🔧 Flask CLI Commands

```bash
# Create an administrator account
flask create-admin

# Initialize 6 tennis courts
flask init-courts

# Test email configuration
flask test-email --to your-email@example.com

# Database migrations
flask db upgrade    # Apply migrations
flask db migrate    # Create new migration
flask db downgrade  # Rollback migration
```

## 📁 Project Structure

```
tennis-club-reservation/
├── app/
│   ├── __init__.py           # Flask app factory
│   ├── models.py             # Database models
│   ├── decorators.py         # Authorization decorators
│   ├── errors.py             # German error messages
│   ├── cli.py                # CLI commands
│   ├── routes/               # Route blueprints
│   │   ├── auth.py           # Authentication
│   │   ├── reservations.py   # Booking management
│   │   ├── members.py        # Member management
│   │   ├── courts.py         # Court availability
│   │   ├── admin.py          # Admin functions
│   │   └── dashboard.py      # Main dashboard
│   ├── services/             # Business logic
│   │   ├── reservation_service.py
│   │   ├── validation_service.py
│   │   ├── email_service.py
│   │   └── block_service.py
│   ├── templates/            # HTML templates
│   │   ├── base.html
│   │   ├── dashboard.html
│   │   ├── login.html
│   │   ├── reservations.html
│   │   ├── members.html
│   │   ├── admin.html
│   │   └── errors/
│   └── static/               # Static files
│       ├── css/
│       └── js/
├── tests/                    # Test suite
├── migrations/               # Database migrations
├── config.py                 # Configuration
├── wsgi.py                   # WSGI entry point
├── init_db.py               # Database initialization
└── requirements.txt          # Python dependencies
```

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

- **Responsive Design**: Works on desktop, tablet, and mobile
- **Color-Coded Grid**: Green (available), Red (reserved), Grey (blocked)
- **Interactive Booking**: Click any available slot to book
- **Real-Time Updates**: AJAX-based updates without page reload
- **Touch-Friendly**: Optimized for mobile touch interactions

## 🚀 Deployment

### PythonAnywhere

See [DEPLOYMENT.md](DEPLOYMENT.md) for complete deployment instructions.

Quick steps:
1. Upload code to PythonAnywhere
2. Create virtual environment
3. Configure environment variables
4. Set up MySQL database
5. Run migrations
6. Configure WSGI
7. Set up static files

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

- **v1.0.0** - Initial release
  - Complete booking system
  - Member and admin management
  - Email notifications
  - Property-based testing
  - German localization
  - Responsive design
  - PythonAnywhere deployment ready
