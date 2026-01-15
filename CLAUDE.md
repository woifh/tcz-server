# CLAUDE.md

This file provides guidance to Claude Code when working in this repository.

## Build & Development Commands

```bash
# Start development server
flask run --debug

# Run all tests
pytest

# Run tests with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_reservations.py -v

# Run property-based tests
pytest tests/property/ -v

# Lint and format
npm run lint          # ESLint for JavaScript
npm run format        # Prettier formatting

# Build CSS (Tailwind)
npm run build:css
npm run watch:css     # Watch mode

# Run Python/Flask commands locally
python3 -m flask run --debug
python3 -m pytest
python3 script.py
```

## Project Architecture

This is a Flask web application for tennis court reservation management (TCZ - Tennis Club Zorneding).

### Backend Structure

- **Factory pattern**: App created via `create_app()` in `app/__init__.py`
- **Blueprints**: Routes organized by domain in `app/routes/`
  - `auth.py` - Authentication (login, logout, password reset)
  - `courts.py` - Court availability views
  - `reservations.py` - Booking management
  - `members.py` - Member management
  - `admin.py` - Admin dashboard
  - `api/` - REST API endpoints (mobile app support)
- **Service layer**: Business logic in `app/services/`
  - `reservation_service.py` - Booking rules, validation
  - `member_service.py` - Member CRUD operations
  - `block_service.py` - Court blocking logic
  - `notification_service.py` - Email notifications
- **Models**: SQLAlchemy models in `app/models/`

### Frontend Structure

- **Alpine.js**: Client-side reactivity (no build step for JS)
- **Tailwind CSS**: Utility-first styling
- **Components**: `app/static/js/components/`
  - `dashboard.js` - Main reservation grid
  - `admin/` - Admin panel modules

### API Pattern

All API endpoints use `/api/` prefix. Frontend fetches use this convention:
```javascript
fetch('/api/reservations/...', { ... })
fetch('/api/members/...', { ... })
fetch('/api/courts/availability', { ... })
```

### Authentication

- Session-based auth for web (Flask-Login)
- JWT Bearer tokens for mobile app API access
- Decorator `@jwt_or_session_required` supports both

## Key Files

- `config.py` - Environment-based configuration
- `app/constants/` - Business rules (booking limits, time windows)
- `app/decorators/auth.py` - Authorization decorators
- `app/utils/timezone_utils.py` - Berlin timezone handling

## Database

- SQLite for development (`instance/app.db`)
- MySQL for production (PythonAnywhere)
- Migrations via Flask-Migrate: `flask db migrate`, `flask db upgrade`

## Testing

- Unit tests in `tests/unit/`
- Integration tests in `tests/integration/`
- Property-based tests using Hypothesis in `tests/property/`
- Fixtures in `tests/conftest.py`

## Deployment

Hosted on PythonAnywhere. Reload after changes:
- Web app reload via PythonAnywhere dashboard
- Or use MCP tool: `mcp__pythonanywhere__reload_webapp`

## Important Rules

- **NEVER push to GitHub without explicit user request** - always wait for the user to ask before pushing commits
- **When pushing to GitHub**:
  - Ask the user whether to increase major or minor version
  - Add a short, non-technical changelog entry to CHANGELOG.md (keep version in sync with git tags, major.minor format)
  - Create a meaningful commit message
  - Push to GitHub

## German Language

UI text is in German. Common terms:
- Platz = Court
- Sperrung = Block (court blocking)
- Buchung = Booking/Reservation
- Mitglied = Member
