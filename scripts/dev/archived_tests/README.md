# Archived Test Files

This directory contains ad-hoc test scripts that were created during development. These are **not part of the official test suite**.

## About These Files

These test files were created to troubleshoot specific issues or test particular features during development. They are:

- **Not maintained** - May not work with current codebase
- **Not run by CI/CD** - Not part of `pytest tests/`
- **Historical artifacts** - Kept for reference only
- **Ad-hoc tests** - Created for one-time debugging

## Official Test Suite

The **official test suite** is located in [`tests/`](../../../tests/) at the project root:

```
tcz/
├── tests/                    ← Official test suite (use this!)
│   ├── test_models.py
│   ├── test_routes.py
│   ├── test_services.py
│   └── ...
└── scripts/dev/archived_tests/  ← Archived ad-hoc tests (this directory)
```

## Running Tests

### Run Official Test Suite
```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_models.py -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html
```

### These Archived Tests
```bash
# Generally don't run these - they may not work
# If you need to reference them, look at the code as examples
```

## Why Keep These?

These files are archived rather than deleted because they:

1. **Document debugging approaches** - Show how specific issues were investigated
2. **Preserve test scenarios** - May contain edge cases not in official tests
3. **Historical reference** - Show evolution of features during development
4. **Reusable patterns** - Code snippets might be useful for future debugging

## File Categories

Based on filenames, these tests cover:

### Batch Operations
- Tests for batch reservation editing and deletion
- Workflow testing for batch operations
- Batch ID handling and authentication

### Court Blocking
- Various iterations of court blocking functionality
- Debugging scripts for blocking issues
- Fix verification tests

### Authentication & Routes
- Authenticated request testing
- Route-specific debugging
- Edit mode troubleshooting

### Database & Connections
- Database connection testing
- Query debugging
- Data integrity checks

### Forms & UI
- Form rendering tests
- Browser HTML debugging
- Template testing

## Cleanup Policy

These files may be deleted in the future if:

1. Similar functionality is covered by official tests in `tests/`
2. The code is so outdated it's no longer useful as reference
3. The issues they were testing are long resolved

For now, they're preserved as part of the project's development history.

## Contributing New Tests

**Don't add tests here!**

If you're writing new tests, add them to the official test suite:

1. Create test file in `tests/` directory
2. Follow existing test patterns
3. Use pytest fixtures and conventions
4. Ensure tests pass with `pytest tests/`

See [`tests/README.md`](../../../tests/README.md) for testing guidelines (if it exists).
