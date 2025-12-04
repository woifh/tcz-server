# E2E Tests - Playwright

These tests were converted from Cypress to Playwright due to Cypress download accessibility issues.

## Test Suites

1. **authentication.spec.js** - Login/logout functionality
2. **dashboard.spec.js** - Dashboard features, date navigation, court grid
3. **reservations.spec.js** - Booking modal, creating reservations
4. **favourites.spec.js** - Favourites management

## Running Tests

```bash
# Run all tests (headless)
npm run test:e2e

# Run tests with browser visible
npm run test:e2e:headed

# Run tests with UI mode (interactive)
npm run test:e2e:ui

# Run tests in debug mode
npm run test:e2e:debug

# Run specific test file
npx playwright test authentication.spec.js
```

## Configuration

Tests are configured in `playwright.config.js`:
- Base URL: http://127.0.0.1:5000
- Auto-starts Flask server before tests
- Takes screenshots on failure
- Generates HTML report

## Test Credentials

- Admin: wolfgang.hacker@gmail.com / admin123
- Tests use the local SQLite database

## Notes

- Playwright automatically starts the Flask server before running tests
- Tests run in parallel by default
- HTML report is generated after test run
- Screenshots and traces are saved on failure
