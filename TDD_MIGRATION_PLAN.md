# TDD-Driven Alpine.js Migration Plan

## Overview
Implementing Test-Driven Development approach for completing the Alpine.js migration of the Tennis Club Reservation System.

## Current Status

### ✅ Completed
1. **Deployment Infrastructure**
   - PythonAnywhere MCP server configured and working
   - Deployment script created (`deploy_update.sh`)
   - App successfully deployed to https://woifh.pythonanywhere.com
   - Fixed booking modal null reference error

2. **Existing Test Coverage**
   - 24/24 E2E tests passing for existing features
   - Tests for: Authentication, Dashboard, Reservations, Favourites
   - Playwright configured and working

3. **Alpine.js Migration (75% Complete)**
   - ✅ Favourites page (Alpine.js)
   - ✅ Reservations list (Alpine.js)
   - ✅ Member search component (Alpine.js)
   - ⏳ Booking modal (Vanilla JS - stable)
   - ⏳ Court grid (Vanilla JS - needs migration)

### 📝 New Test Suite Created
- **booking-modal.spec.js** - 25 comprehensive tests covering:
  - Modal opening/closing (5 tests)
  - Modal content validation (9 tests)
  - Booking creation (5 tests)
  - Error handling (2 tests)
  - State management (3 tests)
  - Accessibility (3 tests)

### ⚠️ Current Issue
- Tests require Flask server running
- Need to update test configuration for proper server management

## TDD Migration Strategy

### Phase 1: Establish Test Baseline ⏳
**Goal**: Get all booking modal tests passing with current vanilla JS implementation

**Tasks**:
1. ✅ Create comprehensive E2E tests for booking modal
2. ⏳ Configure Playwright to start Flask server automatically
3. ⏳ Run tests and fix any failures
4. ⏳ Document baseline test results

**Success Criteria**: All 25 booking modal tests passing

### Phase 2: Migrate Booking Modal to Alpine.js
**Goal**: Convert booking modal to Alpine.js while keeping tests green

**Approach**:
1. Create Alpine.js component for booking modal
2. Run tests after each change
3. Keep tests passing throughout migration
4. Add Alpine.js specific tests

**Test-Driven Steps**:
```
1. Write test → Run (should fail) → Implement → Run (should pass)
2. Refactor → Run tests → Ensure still passing
3. Repeat for each feature
```

**Features to Migrate**:
- Modal state management (open/close)
- Form data binding
- Favourites loading
- Booking submission
- Error handling

### Phase 3: Migrate Court Grid to Alpine.js
**Goal**: Complete the migration to 100% Alpine.js

**Tasks**:
1. Write E2E tests for court grid interactions
2. Create Alpine.js component for grid
3. Migrate grid rendering logic
4. Migrate date navigation
5. Migrate slot clicking
6. Keep all tests passing

### Phase 4: Add Unit Tests
**Goal**: Add JavaScript unit tests for business logic

**Setup**:
- Install Vitest or Jest
- Configure for ES modules
- Create test utilities

**Test Coverage**:
- Utility functions (getEndTime, formatDateGerman, etc.)
- Data transformation functions
- Validation logic
- API interaction functions

### Phase 5: Production Optimization
**Goal**: Optimize for production deployment

**Tasks**:
1. Remove cache-busting headers in production
2. Minify JavaScript
3. Add proper error logging
4. Configure email notifications
5. Add monitoring

## Test Configuration Needed

### Playwright Config Update
```javascript
// playwright.config.js
webServer: {
  command: 'source venv/bin/activate && python -m flask run',
  port: 5000,
  reuseExistingServer: !process.env.CI,
  env: {
    FLASK_ENV: 'testing',
    RATELIMIT_ENABLED: 'false'
  }
}
```

### Test Environment Variables
```bash
# .env.test
DATABASE_URL=sqlite:///instance/tennis_club.db
FLASK_ENV=testing
RATELIMIT_ENABLED=false
SECRET_KEY=test-secret-key
```

## Benefits of TDD Approach

### 1. **Confidence**
- Tests catch regressions immediately
- Safe to refactor
- Clear success criteria

### 2. **Documentation**
- Tests document expected behavior
- Examples of how features should work
- Living specification

### 3. **Quality**
- Forces thinking about edge cases
- Catches bugs early
- Ensures features work as intended

### 4. **Speed**
- Faster debugging (tests pinpoint issues)
- Less manual testing needed
- Automated regression testing

## Next Steps (In Order)

1. **Fix Playwright Configuration**
   - Add webServer config to auto-start Flask
   - Update test environment setup
   - Run booking modal tests

2. **Establish Baseline**
   - Get all 25 booking modal tests passing
   - Document any issues found
   - Fix vanilla JS bugs if needed

3. **Deploy Current Fix**
   - Pull latest code on PythonAnywhere
   - Reload webapp
   - Verify production works

4. **Begin Alpine.js Migration**
   - Start with booking modal
   - Keep tests green
   - Commit after each passing test

5. **Complete Migration**
   - Migrate court grid
   - Add unit tests
   - Update documentation

## Success Metrics

- ✅ 100% test pass rate maintained throughout
- ✅ No regressions introduced
- ✅ All features working in production
- ✅ Code coverage > 80%
- ✅ Migration complete (100% Alpine.js)

## Timeline Estimate

- **Phase 1** (Test Baseline): 1-2 hours
- **Phase 2** (Booking Modal Migration): 2-3 hours
- **Phase 3** (Court Grid Migration): 3-4 hours
- **Phase 4** (Unit Tests): 2-3 hours
- **Phase 5** (Production Optimization): 1-2 hours

**Total**: 9-14 hours of focused work

## Resources

- **Test Files**: `tests/e2e/booking-modal.spec.js`
- **Deployment Script**: `deploy_update.sh`
- **Documentation**: `ALPINE_MIGRATION_FINAL_STATUS.md`
- **Playwright Docs**: https://playwright.dev/
- **Alpine.js Docs**: https://alpinejs.dev/

## Notes

- Flask server must be running for E2E tests
- Tests use SQLite database (same as development)
- Rate limiting disabled for tests
- Admin credentials: wolfgang.hacker@gmail.com / admin123

---

**Created**: December 8, 2025, 22:45 CET
**Status**: Phase 1 in progress
**Next Action**: Configure Playwright webServer
