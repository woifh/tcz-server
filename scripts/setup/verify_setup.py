"""Verify project setup is complete."""
import os
import sys

def check_file(path, description):
    """Check if a file exists."""
    exists = os.path.exists(path)
    status = "✓" if exists else "✗"
    print(f"{status} {description}: {path}")
    return exists

def check_directory(path, description):
    """Check if a directory exists."""
    exists = os.path.isdir(path)
    status = "✓" if exists else "✗"
    print(f"{status} {description}: {path}")
    return exists

def main():
    """Run verification checks."""
    print("Verifying Tennis Club Reservation System Setup\n")
    print("=" * 60)
    
    checks = []
    
    # Configuration files
    print("\nConfiguration Files:")
    checks.append(check_file("config.py", "Configuration module"))
    checks.append(check_file("wsgi.py", "WSGI entry point"))
    checks.append(check_file("requirements.txt", "Python dependencies"))
    checks.append(check_file(".env.example", "Environment variables example"))
    checks.append(check_file("tailwind.config.js", "Tailwind CSS config"))
    checks.append(check_file("package.json", "Node.js package config"))
    
    # Application structure
    print("\nApplication Structure:")
    checks.append(check_file("app/__init__.py", "Flask app factory"))
    checks.append(check_file("app/models.py", "Database models"))
    checks.append(check_directory("app/routes", "Routes directory"))
    checks.append(check_directory("app/services", "Services directory"))
    checks.append(check_directory("app/templates", "Templates directory"))
    checks.append(check_directory("app/static", "Static files directory"))
    
    # Routes
    print("\nRoute Blueprints:")
    checks.append(check_file("app/routes/auth.py", "Authentication routes"))
    checks.append(check_file("app/routes/reservations.py", "Reservation routes"))
    checks.append(check_file("app/routes/members.py", "Member routes"))
    checks.append(check_file("app/routes/courts.py", "Court routes"))
    checks.append(check_file("app/routes/admin.py", "Admin routes"))
    checks.append(check_file("app/routes/dashboard.py", "Dashboard routes"))
    
    # Services
    print("\nService Modules:")
    checks.append(check_file("app/services/reservation_service.py", "Reservation service"))
    checks.append(check_file("app/services/validation_service.py", "Validation service"))
    checks.append(check_file("app/services/email_service.py", "Email service"))
    checks.append(check_file("app/services/block_service.py", "Block service"))
    
    # Static files
    print("\nStatic Files:")
    checks.append(check_file("app/static/css/styles.css", "CSS styles"))
    checks.append(check_file("app/static/js/app.js", "JavaScript"))
    
    # Tests
    print("\nTest Structure:")
    checks.append(check_directory("tests", "Tests directory"))
    checks.append(check_file("tests/conftest.py", "Pytest configuration"))
    checks.append(check_file("tests/test_app.py", "App tests"))
    
    # Summary
    print("\n" + "=" * 60)
    passed = sum(checks)
    total = len(checks)
    print(f"\nSetup Verification: {passed}/{total} checks passed")
    
    if passed == total:
        print("✓ Project structure is complete!")
        return 0
    else:
        print("✗ Some files or directories are missing.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
