#!/usr/bin/env python3
"""
Create an admin user for the Tennis Club Reservation System

This script provides multiple ways to create admin users:
1. Interactive mode (default): Prompts for user details
2. Command-line arguments: Quick admin creation
3. Test mode: Creates a test admin with known credentials

Usage:
    # Interactive mode (prompts for details)
    python scripts/setup/create_admin.py

    # Command-line arguments
    python scripts/setup/create_admin.py John Doe john@example.com mypassword

    # Test admin (admin@test.com / admin123)
    python scripts/setup/create_admin.py --test
"""
import os
import sys
from pathlib import Path
from getpass import getpass

# Load environment variables
from dotenv import load_dotenv

# Determine which environment file to load
config_name = os.environ.get('FLASK_CONFIG') or os.environ.get('FLASK_ENV', 'development')
if config_name == 'production':
    env_file = Path(__file__).parent.parent.parent / '.env.production'
    if env_file.exists():
        print(f"Loading production environment from: {env_file}")
        load_dotenv(env_file)
    else:
        load_dotenv()
else:
    load_dotenv()

from app import create_app, db
from app.models import Member


def validate_email(email):
    """Basic email validation"""
    return '@' in email and '.' in email.split('@')[1]


def create_admin_user(firstname, lastname, email, password, config='development'):
    """Create an admin user with the given details"""
    app = create_app(config)

    with app.app_context():
        # Check if user already exists
        existing_user = Member.query.filter_by(email=email).first()
        if existing_user:
            print(f"❌ User with email {email} already exists")
            if existing_user.role == 'administrator':
                print(f"   (User is already an administrator)")
            else:
                print(f"   Current role: {existing_user.role}")
            return False

        # Create admin user
        admin = Member(
            firstname=firstname,
            lastname=lastname,
            email=email,
            role='administrator'
        )
        admin.set_password(password)

        db.session.add(admin)
        db.session.commit()

        print()
        print("=" * 60)
        print("✅ Admin user created successfully!")
        print("=" * 60)
        print()
        print(f"Name:  {firstname} {lastname}")
        print(f"Email: {email}")
        print(f"Role:  Administrator")
        print()
        print("You can now log in with these credentials.")
        print()

        return True


def interactive_mode(config='development'):
    """Interactive mode - prompts user for details"""
    print("=" * 60)
    print("Create New Admin User (Interactive Mode)")
    print("=" * 60)
    print()

    # Get user input
    print("Enter admin details:")
    firstname = input("First name: ").strip()
    if not firstname:
        print("❌ First name cannot be empty")
        return False

    lastname = input("Last name: ").strip()
    if not lastname:
        print("❌ Last name cannot be empty")
        return False

    email = input("Email: ").strip().lower()
    if not validate_email(email):
        print("❌ Invalid email format")
        return False

    # Get password with confirmation
    password = getpass("Password: ")
    if not password:
        print("❌ Password cannot be empty")
        return False

    password_confirm = getpass("Confirm password: ")
    if password != password_confirm:
        print("❌ Passwords do not match")
        return False

    print()
    print("Creating admin user...")

    return create_admin_user(firstname, lastname, email, password, config)


def test_mode(config='development'):
    """Test mode - creates admin@test.com / admin123"""
    print("=" * 60)
    print("Create Test Admin User")
    print("=" * 60)
    print()
    print("This will create a test admin with known credentials:")
    print("  Email: admin@test.com")
    print("  Password: admin123")
    print()
    print("⚠️  WARNING: Only use this in development environments!")
    print()

    if config == 'production':
        print("❌ Test admin creation is not allowed in production!")
        print("   Use interactive mode or command-line arguments instead.")
        return False

    response = input("Continue? (yes/no): ").strip().lower()
    if response != 'yes':
        print("Aborted.")
        return False

    print()
    return create_admin_user("Test", "Admin", "admin@test.com", "admin123", config)


def main():
    """Main entry point"""
    # Determine environment
    config = os.environ.get('FLASK_CONFIG') or os.environ.get('FLASK_ENV', 'development')

    # Parse command-line arguments
    if len(sys.argv) == 1:
        # No arguments - interactive mode
        return interactive_mode(config)

    elif len(sys.argv) == 2 and sys.argv[1] in ['--test', '-t']:
        # Test mode
        return test_mode(config)

    elif len(sys.argv) == 5:
        # Command-line arguments mode
        firstname, lastname, email, password = sys.argv[1:5]

        # Validate
        if not validate_email(email):
            print("❌ Invalid email format")
            return False

        print(f"Creating admin user: {firstname} {lastname} ({email})")
        return create_admin_user(firstname, lastname, email, password, config)

    else:
        # Invalid usage
        print("Usage:")
        print("  Interactive mode:")
        print("    python scripts/setup/create_admin.py")
        print()
        print("  Command-line mode:")
        print("    python scripts/setup/create_admin.py <firstname> <lastname> <email> <password>")
        print("    Example: python scripts/setup/create_admin.py John Doe john@example.com mypassword")
        print()
        print("  Test mode (development only):")
        print("    python scripts/setup/create_admin.py --test")
        print()
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
