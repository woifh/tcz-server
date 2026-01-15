# CLAUDE.md

This file provides guidance to Claude Code when working in this repository.

## Build & Development Commands

**IMPORTANT**: All Python commands must be run using the virtual environment at `.venv/`:

```bash
# Run all tests (ALWAYS use this exact command)
source .venv/bin/activate && pytest

# Run tests with coverage
source .venv/bin/activate && pytest --cov=app --cov-report=html

# Run specific test file
source .venv/bin/activate && pytest tests/test_reservations.py -v

# Run property-based tests
source .venv/bin/activate && pytest tests/property/ -v

# Start development server
source .venv/bin/activate && flask run --debug

# Run Flask CLI commands
source .venv/bin/activate && flask <command>

# Lint and format (JavaScript)
npm run lint          # ESLint for JavaScript
npm run format        # Prettier formatting

# Build CSS (Tailwind)
npm run build:css
npm run watch:css     # Watch mode
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
  - Add a short, non-technical changelog entry to CHANGELOG.md (version format: major.minor)
  - Create a meaningful commit message
  - Push to GitHub
  - Create and push a git tag matching the changelog version (format: vX.Y.0, e.g., v3.9.0 for changelog version 3.9)

## German Language

UI text is in German. Common terms:
- Platz = Court
- Sperrung = Block (court blocking)
- Buchung = Booking/Reservation
- Mitglied = Member

## Vibe Coding Principles

This codebase prioritizes flow, clarity, and fast iteration.

### General Guidelines
- Prefer simple, readable code over clever abstractions
- Optimize for local reasoning: a reader should understand code in under a minute
- Keep changes small, reversible, and easy to delete
- Avoid premature abstraction; duplicate a little before extracting
- Make failures loud and obvious—no silent magic

### Naming & Structure
- Use clear, descriptive names; naming is more important than comments
- Keep related logic close together
- Avoid deep inheritance or excessive indirection

### Comments & Intent
- Comment *why* something exists, not *what the code does*
- Explain tradeoffs, constraints, or non-obvious decisions

### Testing Philosophy
- Write tests that increase confidence without slowing momentum
- Focus on behavior, not implementation details
- Prefer a few high-signal tests over exhaustive coverage

### Refactoring
- Refactor opportunistically when it improves clarity
- Do not refactor solely for architectural purity
- It should feel safe to rewrite or delete code

## Mandatory Rules

- **NEVER break existing functionality** - preserve working behavior at all costs
- **When in doubt, ask the user** - don't guess or assume; clarify before proceeding
- **Respect software development principles** - follow SOLID, DRY, KISS
- **Never mention Claude Code** - no references to Claude, AI, or this tool in changelogs, commits, or any project files