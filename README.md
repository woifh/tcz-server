# Tennis Club Court Reservation System

A Flask-based web application for managing tennis court reservations with German localization.

## Features

- Court reservation management
- Member authentication and management
- Admin controls for blocking courts
- Email notifications in German
- Responsive design with Tailwind CSS
- MySQL database backend

## Setup Instructions

### 1. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Copy `.env.example` to `.env` and update with your settings:

```bash
cp .env.example .env
```

Edit `.env` with your database and email credentials.

### 4. Initialize Database

```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

### 5. Run Development Server

```bash
flask run
```

The application will be available at `http://localhost:5000`

## Project Structure

```
tennis-club-reservation/
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── models.py            # Database models
│   ├── routes/              # Route blueprints
│   ├── services/            # Business logic
│   ├── templates/           # HTML templates
│   └── static/              # CSS, JS, images
├── migrations/              # Database migrations
├── tests/                   # Test files
├── config.py                # Configuration
├── wsgi.py                  # WSGI entry point
└── requirements.txt         # Python dependencies
```

## Requirements

- Python 3.10+
- MySQL 8.0+
- Flask 3.0+

## License

Proprietary - Tennis Club Internal Use
