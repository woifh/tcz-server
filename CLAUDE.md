# CLAUDE.md — TCZ Web (Flask Backend + Web UI)

This file contains web-specific guidance.
Shared rules (git, production, vibe coding) are in `/Users/woifh/tcz/CLAUDE.md`.

---

## 🔗 Cross-Project Context

This project **defines the API** that iOS and Android apps consume.

### Related Codebases

| Project | Path | Relationship |
|---------|------|--------------|
| iOS App | `/Users/woifh/tcz/tcz-ios` | Consumes our API |
| Android App | `/Users/woifh/tcz/tcz-android` | Consumes our API |

### Before Modifying API Endpoints

Always check how mobile apps use the endpoint. See "Cross-Project Search" in the parent CLAUDE.md for grep commands.

### API Change Checklist

When modifying an API endpoint:
1. ☐ Search iOS and Android for usage
2. ☐ Maintain backward compatibility if possible
3. ☐ If breaking change: note which mobile app versions are affected
4. ☐ Update API documentation if it exists

---

## ✅ Testing

### Test Structure

- Python tests: `tests/test_*.py` (flat structure)
- JS unit tests: `tests/unit/`
- E2E tests: `tests/e2e/` (Playwright)
- Fixtures: `tests/conftest.py`

### When to Run Tests

- **After every meaningful code change** — Don't wait until the end
- **Before declaring a task complete** — Always verify
- **After fixing a bug** — Confirm it's actually fixed
- **When touching shared code** — Services, models, utilities

### Test Commands

```bash
# Run all tests (default choice)
source .venv/bin/activate && pytest

# Run specific test file
source .venv/bin/activate && pytest tests/test_reservations.py -v

# Run with coverage
source .venv/bin/activate && pytest --cov=app --cov-report=html
```

### If Tests Fail

1. Read the failure message carefully
2. Identify if it's a real bug or a test that needs updating
3. Fix the root cause, not the symptom
4. Run tests again to confirm
5. Tell me what was wrong and how you fixed it

### Local Development Login

- **User**: max@tcz.at
- **Password**: max@tcz.at

---

## 🏗️ Project Architecture

Flask web application for tennis court reservation management (TCZ - Tennis Club Zellerndorf).

### Backend Structure

- **Factory pattern**: App created via `create_app()` in `app/__init__.py`
- **Blueprints**: Routes organized by domain in `app/routes/`
  - `auth.py` - Authentication (login, logout, password reset)
  - `courts.py` - Court availability views
  - `dashboard.py` - Main dashboard view
  - `reservations.py` - Booking management
  - `members.py` - Member management
  - `admin/` - Admin panel (views.py, audit.py)
  - `api/` - REST API endpoints (consumed by mobile apps)
- **Service layer**: Business logic in `app/services/`
- **Models**: SQLAlchemy models in `app/models/`

### Where to Put Things

| Type | Location |
|------|----------|
| Business logic | `app/services/` |
| Route handlers | `app/routes/` (thin, delegate to services) |
| Database models | `app/models/` |
| Utilities | `app/utils/` |
| Constants | `app/constants/` |
| Frontend JS | `app/static/js/components/` |
| API endpoints | `app/routes/api/` |

### Code Patterns

```python
# ✅ GOOD: Thin route, logic in service
@bp.route('/reservations', methods=['POST'])
@login_required
def create_reservation():
    result = reservation_service.create(current_user, request.json)
    if result.error:
        return jsonify(error=result.error), 400
    return jsonify(result.data), 201

# ❌ BAD: Business logic in route handler
```

```python
# ✅ GOOD: Explicit error handling
def get_member(member_id):
    member = Member.query.get(member_id)
    if not member:
        raise MemberNotFoundError(f"Member {member_id} not found")
    return member

# ❌ BAD: Silent failure (returns None)
```

### Frontend

- **Alpine.js**: Client-side reactivity (no build step)
- **Tailwind CSS**: Utility-first styling
- **Components**: `app/static/js/components/`

### Authentication

- Session-based for web (Flask-Login)
- JWT Bearer tokens for mobile API
- Decorator `@jwt_or_session_required` supports both

---

## 🗄️ Database

- **Development**: SQLite (`instance/tennis_club.db`)
- **Production**: MySQL (PythonAnywhere)

### Migrations

```bash
# After changing models
source .venv/bin/activate && flask db migrate -m "Description"

# Review the generated migration, then apply
source .venv/bin/activate && flask db upgrade
```

⚠️ **Always review generated migrations** — they can be wrong.

---

## 🌐 Environment Configuration

### Config Loading Flow

```
1. Flask app starts
2. Reads .env file (python-dotenv)
3. Checks DATABASE_URL environment variable
4. Selects config class:
   - mysql:// → ProductionConfig
   - Otherwise → DevelopmentConfig
5. config.py reads remaining env vars
```

### Config Files

| File | Purpose | Used When |
|------|---------|-----------|
| `config.py` | Defines config classes | Always (code) |
| `.env` | Your local settings | Local development |
| `.env.example` | Template for new devs | Reference only |
| `.env.production` | Production settings | On PythonAnywhere |

### Required Environment Variables

**Local Development (minimum):**

```bash
# .env file
SECRET_KEY=any-random-string-for-local-dev
DATABASE_URL=sqlite:///instance/tennis_club.db
RATELIMIT_ENABLED=false
```

**Production (required):**

```bash
SECRET_KEY=<strong-random-key>
DATABASE_URL=mysql+pymysql://user:pass@host/db
MAIL_USERNAME=<gmail-address>
MAIL_PASSWORD=<gmail-app-password>
```

**Optional (both environments):**

```bash
JWT_SECRET_KEY=<for-mobile-api>
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
DEV_EMAIL_RECIPIENT=<redirect-all-test-emails-here>
```

### Key Differences

| Setting | Development | Production |
|---------|-------------|------------|
| Database | SQLite | MySQL |
| Rate Limiting | Disabled | Enabled |
| Debug Mode | True | False |
| Session Cookies | HTTP allowed | HTTPS only |
| Email | Optional | Required |

### Local Dev for Mobile Testing

```bash
# Run accessible on local network (mobile apps expect 10.0.0.147:5001)
source .venv/bin/activate && flask run --host=0.0.0.0 --port=5001
```

---

## 🚀 Deployment (PythonAnywhere)

| Setting | Value |
|---------|-------|
| Domain | woifh.pythonanywhere.com |
| Python | 3.10 |
| Virtualenv | `/home/woifh/.virtualenvs/tennisclub` |
| Project Path | `/home/woifh/tcz` |

### ⚠️ Important: Two Different Virtualenvs

| Environment | Virtualenv Path | Activation Command |
|-------------|-----------------|-------------------|
| **Local (Mac)** | `.venv/` in project dir | `source .venv/bin/activate` |
| **Production (PythonAnywhere)** | `~/.virtualenvs/tennisclub/` | `source ~/.virtualenvs/tennisclub/bin/activate` |

Don't confuse these — using the wrong virtualenv will cause missing dependencies.

### ⚠️ Important: Different Directory Structures

| Environment | Flask App Location | Note |
|-------------|-------------------|------|
| **Local (Mac)** | `/Users/woifh/tcz/tcz-web/` | In subdirectory of monorepo |
| **Production** | `/home/woifh/tcz/` | At root (only tcz-web is deployed) |

Local has the monorepo structure (`tcz-web/`, `tcz-ios/`, `tcz-android/`), but production only has the Flask app at the root.

### Production Commands

```bash
# Activate virtualenv (REQUIRED first)
source ~/.virtualenvs/tennisclub/bin/activate

# Full deployment
cd /home/woifh/tcz && git pull origin main && flask db upgrade
# Then reload webapp via MCP or dashboard
```

### MCP Tools

```
mcp__pythonanywhere__reload_webapp with domain="woifh.pythonanywhere.com"
mcp__pythonanywhere__read_file_or_directory with path="/home/woifh/tcz/..."
```

---

## 📋 Audit Log Checklist

When adding new audit log operations:

1. ☐ Add operation to `valid_operations` in `app/models.py`
2. ☐ Add German label in `app/templates/admin/audit_log.html` (actionMap)
3. ☐ Add field labels in `app/templates/admin/audit_log.html` (fieldLabels)
4. ☐ Add formatting in `formatDetails()` if needed

### Required Details

| Type | Required fields |
|------|-----------------|
| Reservations | member name, court, date, time |
| Blocks | court(s), date, time range, reason |
| Members | name, changed fields with old/new values |

**Never show raw IDs** — always resolve to human-readable names.

---

## 📦 Versioning

### Release Configuration (for woifh workflows)

| Setting | Value |
|---------|-------|
| CHANGELOG | `CHANGELOG.md` (project root) |
| Version file | None (calculated from git tags) |
| Test command | `source .venv/bin/activate && pytest` |

---

## ⚠️ Common Mistakes to Avoid

- Don't put business logic in route handlers — use services
- Don't forget to activate venv before running Python commands
- Don't create migrations without reviewing them first
- Don't modify API response formats without checking mobile apps
- Don't use `query.get()` without handling None returns

---

## 🔧 Build Commands Reference

```bash
# Python (always activate venv first)
source .venv/bin/activate && pytest              # Run tests
source .venv/bin/activate && flask run --debug   # Dev server
source .venv/bin/activate && flask db migrate    # Create migration
source .venv/bin/activate && flask db upgrade    # Apply migration

# JavaScript
npm run lint          # ESLint
npm run format        # Prettier

# CSS
npm run build:css     # Build Tailwind
npm run watch:css     # Watch mode
```

---

## 📚 Key Files

| File | Purpose |
|------|---------|
| `config.py` | Environment configuration |
| `app/__init__.py` | App factory (`create_app()`) |
| `app/routes/api/` | API endpoints for mobile apps |
| `app/services/` | Business logic |
| `app/constants/` | Business rules, limits |
| `tests/conftest.py` | Test fixtures |
