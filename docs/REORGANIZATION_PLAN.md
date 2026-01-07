# Project Reorganization Plan

## Overview
This document outlines the reorganization of the Tennis Club Reservation System to improve maintainability, deployment reliability, and developer experience.

## Current Issues

1. **Root Directory Clutter**: 82 Python files scattered in root (52 tests, 13 debug scripts)
2. **Deployment Inconsistency**: 3 duplicate PythonAnywhere deployment scripts
3. **Test Fragmentation**: Ad-hoc test files in root vs. proper test suite in `tests/`
4. **Documentation Sprawl**: 9 refactoring/summary markdown files
5. **No Clear Deployment Guide**: Deployment knowledge scattered across scripts

## Target Structure

```
tcz/
├── app/                    # Production application (NO CHANGES)
├── tests/                  # Test suite (NO CHANGES)
├── migrations/             # Database migrations (NO CHANGES)
├── scripts/               # NEW: Organized utility scripts
│   ├── deploy/
│   │   ├── pythonanywhere.sh           # Consolidated deployment script
│   │   └── README.md                   # Deployment script documentation
│   ├── setup/
│   │   ├── init_environment.sh         # Environment setup
│   │   ├── init_database.py            # Database initialization
│   │   └── create_admin.py             # Admin user creation
│   ├── database/
│   │   ├── seed.py                     # Database seeding
│   │   ├── recreate.py                 # Full database recreation
│   │   ├── explore.py                  # Database exploration
│   │   └── README.md                   # Database tools documentation
│   └── dev/
│       ├── debug/                      # Archived debug scripts
│       └── archived_tests/             # Archived ad-hoc tests
├── docs/                   # NEW: Consolidated documentation
│   ├── DEPLOYMENT.md                   # Deployment guide
│   ├── ARCHITECTURE.md                 # System architecture
│   └── DEVELOPMENT.md                  # Developer setup guide
├── config.py              # Configuration
├── wsgi.py                # WSGI entry point
├── requirements.txt       # Dependencies
├── .env.example           # Environment template
├── .env.production.example # Production template
└── README.md              # Main documentation
```

## Migration Steps

### Phase 1: Create Structure & Documentation
- [x] Create `scripts/` subdirectories
- [ ] Create `docs/` directory
- [ ] Write DEPLOYMENT.md
- [ ] Write ARCHITECTURE.md
- [ ] Consolidate refactoring docs

### Phase 2: Consolidate Deployment Scripts
- [ ] Merge `deploy_pythonanywhere.sh`, `deploy_to_pythonanywhere.sh`, `pythonanywhere_deploy.sh`
- [ ] Move to `scripts/deploy/pythonanywhere.sh`
- [ ] Update to use new paths
- [ ] Test deployment script

### Phase 3: Organize Database Scripts
- [ ] Move `seed_database.py` → `scripts/database/seed.py`
- [ ] Move `recreate_database.py` → `scripts/database/recreate.py`
- [ ] Move `init_db.py` → `scripts/setup/init_database.py`
- [ ] Move `setup_mysql_db.py` → `scripts/setup/`
- [ ] Consolidate admin creation scripts
- [ ] Move database inspection scripts

### Phase 4: Clean Up Test Files
- [ ] Identify which root test files are still relevant
- [ ] Move relevant tests to `tests/` directory
- [ ] Archive remaining ad-hoc tests to `scripts/dev/archived_tests/`
- [ ] Update test documentation

### Phase 5: Archive Debug Files
- [ ] Move all `debug_*.py` files to `scripts/dev/debug/`
- [ ] Add README explaining these are archived

### Phase 6: Update Configuration
- [ ] Update `.gitignore` for new structure
- [ ] Update paths in remaining scripts
- [ ] Update README.md with new structure

### Phase 7: Validation
- [ ] Test setup workflow on clean environment
- [ ] Test deployment workflow
- [ ] Verify all production paths still work

## Files to Move

### Deployment Scripts (scripts/deploy/)
- deploy_pythonanywhere.sh → pythonanywhere.sh (consolidated)
- deploy_to_pythonanywhere.sh → (merge into above)
- pythonanywhere_deploy.sh → (merge into above)
- setup_pythonanywhere.sh → keep as setup/pythonanywhere.sh
- update_pythonanywhere.sh → (merge into deploy)
- update_app.sh → scripts/deploy/

### Setup Scripts (scripts/setup/)
- setup.sh
- setup_env.sh
- init_db.py → init_database.py
- setup_mysql_db.py
- verify_setup.py

### Database Scripts (scripts/database/)
- seed_database.py → seed.py
- recreate_database.py → recreate.py
- explore_database.py → explore.py
- fix_migration_version.py → fix_migration.py
- delete_all_reservations.py → delete_reservations.py
- check_db_structure.py → inspect_structure.py
- check_actual_database.py → inspect_data.py

### Admin Creation (consolidate to scripts/setup/create_admin.py)
- add_admin.py
- create_admin_user.py
- create_test_admin.py

### Archive to scripts/dev/debug/
- debug_actual_route.py
- debug_batch_query.py
- debug_blocks.py
- debug_booking.py
- debug_booking_issue.py
- debug_booking_simple.py
- debug_browser_html.py
- debug_form_initialization.py
- debug_form_simple.py
- manual_security_validation.py
- (+ all test debug files)

### Archive to scripts/dev/archived_tests/
- All 52 test_*.py files from root

### Documentation (docs/)
- Create DEPLOYMENT.md (new)
- Create ARCHITECTURE.md (consolidate refactoring docs)
- Create DEVELOPMENT.md (new)
- Archive old refactoring docs

## Safety Measures

1. **No Production Code Changes**: The `app/`, `tests/`, and `migrations/` directories remain untouched
2. **Git Tracking**: All moves use `git mv` to preserve history
3. **Validation**: Each phase includes validation steps
4. **Rollback Plan**: Keep original file list for potential rollback

## Success Criteria

- [ ] Root directory has <15 files (down from 95+)
- [ ] Clear separation: app code vs. scripts vs. docs
- [ ] Single source of truth for deployment
- [ ] Comprehensive deployment documentation
- [ ] All tests pass
- [ ] Deployment workflow tested and working

## Timeline

Estimated time: 2-3 hours
- Phase 1-2: 30 minutes
- Phase 3-4: 45 minutes
- Phase 5-6: 30 minutes
- Phase 7: 30 minutes (testing)
