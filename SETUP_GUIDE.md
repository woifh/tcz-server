# Tennis Club Reservation System - Setup Guide

## Overview

This guide will help you set up the Tennis Club Court Reservation System on your local machine or PythonAnywhere.

## Prerequisites

- Python 3.10+ (Python 3.9+ will work but 3.10+ is recommended)
- MySQL 8.0+ (or SQLite for development)
- Node.js and npm (for Tailwind CSS)
- Git

## Local Development Setup

### 1. Clone or Navigate to Project

```bash
cd tennis-club-reservation
```

### 2. Automated Setup (Recommended)

Run the setup script:

```bash
./setup.sh
```

This will:
- Create a virtual environment
- Install Python dependencies
- Install Node.js dependencies
- Build Tailwind CSS
- Create .env file from template

### 3. Manual Setup (Alternative)

If you prefer manual setup:

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Install Node.js dependencies
npm install

# Build Tailwind CSS
npm run build:css

# Copy environment template
cp .env.example .env
```

### 4. Configure Environment Variables

Edit `.env` file with your settings:

```bash
# Development settings
FLASK_ENV=development
SECRET_KEY=your-secret-key-here

# Database (use SQLite for development)
DATABASE_URL=sqlite:///tennis_club.db

# Or MySQL for production-like setup
# DATABASE_URL=mysql+pymysql://username:password@localhost/tennis_club

# Email settings (optional for development)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
```

### 5. Initialize Database

```bash
# Initialize Flask-Migrate
flask db init

# Create initial migration
flask db migrate -m "Initial database schema"

# Apply migration
flask db upgrade

# Initialize courts (after models are implemented)
flask init-courts

# Create admin user (after models are implemented)
flask create-admin
```

### 6. Run Development Server

```bash
flask run
```

Visit `http://localhost:5000` in your browser.

### 7. Watch Tailwind CSS (Optional)

In a separate terminal, watch for CSS changes:

```bash
npm run watch:css
```

## PythonAnywhere Deployment

### 1. Upload Files

Upload your project files to PythonAnywhere via:
- Git clone
- File upload
- rsync

### 2. Create Virtual Environment

```bash
mkvirtualenv --python=/usr/bin/python3.10 tennis-club
pip install -r requirements.txt
```

### 3. Configure MySQL Database

1. Go to PythonAnywhere Databases tab
2. Create a new MySQL database
3. Note the connection details

### 4. Set Environment Variables

Create a `.env` file or set in WSGI file:

```python
os.environ['DATABASE_URL'] = 'mysql+pymysql://username:password@username.mysql.pythonanywhere-services.com/dbname'
os.environ['SECRET_KEY'] = 'your-production-secret-key'
os.environ['MAIL_SERVER'] = 'smtp.gmail.com'
os.environ['MAIL_PORT'] = '587'
os.environ['MAIL_USERNAME'] = 'your-email@gmail.com'
os.environ['MAIL_PASSWORD'] = 'your-app-password'
```

### 5. Configure WSGI File

Edit `/var/www/username_pythonanywhere_com_wsgi.py`:

```python
import sys
import os

# Add project directory to path
path = '/home/username/tennis-club-reservation'
if path not in sys.path:
    sys.path.append(path)

# Set environment variables
os.environ['FLASK_ENV'] = 'production'
os.environ['DATABASE_URL'] = 'mysql+pymysql://...'
os.environ['SECRET_KEY'] = '...'

# Import application
from wsgi import application
```

### 6. Configure Static Files

In PythonAnywhere Web tab:
- URL: `/static/`
- Directory: `/home/username/tennis-club-reservation/app/static/`

### 7. Initialize Database

```bash
cd ~/tennis-club-reservation
workon tennis-club
flask db upgrade
flask init-courts
flask create-admin
```

### 8. Reload Web App

Click "Reload" button in PythonAnywhere Web tab.

## Project Structure

```
tennis-club-reservation/
├── app/
│   ├── __init__.py              # Flask app factory
│   ├── models.py                # Database models
│   ├── cli.py                   # CLI commands
│   ├── routes/                  # Route blueprints
│   │   ├── auth.py              # Authentication
│   │   ├── reservations.py      # Reservations
│   │   ├── members.py           # Member management
│   │   ├── courts.py            # Court availability
│   │   ├── admin.py             # Admin functions
│   │   └── dashboard.py         # Dashboard
│   ├── services/                # Business logic
│   │   ├── reservation_service.py
│   │   ├── validation_service.py
│   │   ├── email_service.py
│   │   └── block_service.py
│   ├── templates/               # HTML templates
│   └── static/                  # CSS, JS, images
│       ├── css/
│       └── js/
├── migrations/                   # Database migrations
├── tests/                        # Test files
├── config.py                     # Configuration
├── wsgi.py                       # WSGI entry point
├── requirements.txt              # Python dependencies
├── package.json                  # Node.js dependencies
├── tailwind.config.js            # Tailwind CSS config
└── .env                          # Environment variables (not in git)
```

## Available Flask Commands

```bash
# Database
flask db init              # Initialize migrations
flask db migrate           # Create migration
flask db upgrade           # Apply migrations

# Application
flask init-courts          # Create 6 courts
flask create-admin         # Create admin user
flask test-email           # Test email configuration

# Development
flask run                  # Run development server
flask shell                # Open Python shell with app context
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_app.py

# Run property-based tests
pytest tests/ -k property
```

## Troubleshooting

### Database Connection Issues

- Check DATABASE_URL in .env
- Ensure MySQL is running
- Verify credentials

### Email Not Sending

- Check MAIL_* settings in .env
- For Gmail, use App Password (not regular password)
- Enable "Less secure app access" or use OAuth2

### Import Errors

- Ensure virtual environment is activated
- Run `pip install -r requirements.txt`

### Tailwind CSS Not Working

- Run `npm install`
- Run `npm run build:css`
- Check that output.css is generated

## Next Steps

After setup is complete:

1. Implement database models (Task 2)
2. Implement validation service (Task 3)
3. Implement email service (Task 4)
4. Continue with remaining tasks

## Support

For issues or questions, refer to:
- Requirements: `.kiro/specs/tennis-club-reservation/requirements.md`
- Design: `.kiro/specs/tennis-club-reservation/design.md`
- Tasks: `.kiro/specs/tennis-club-reservation/tasks.md`
