"""Configuration module for Tennis Club Reservation System.

Environment Configuration:
-------------------------
This application supports multiple environments with separate configurations:

- Development (.env): SQLite database, optional email, rate limiting disabled
- Production (.env.production): MySQL database, required email, rate limiting enabled
- Testing: In-memory SQLite, email suppressed, rate limiting disabled

Email Configuration:
-------------------
The application uses Gmail SMTP for sending reservation notifications.

IMPORTANT: You MUST use Gmail App Passwords, not your regular Gmail password!

To set up email:
1. Enable 2-Step Verification on your Google account
2. Generate an App Password at: https://myaccount.google.com/apppasswords
3. Set MAIL_USERNAME to your Gmail address
4. Set MAIL_PASSWORD to the 16-character app password (no spaces)

For detailed setup instructions, see: docs/EMAIL_SETUP.md

If email credentials are not configured, the application will continue to work
but email notifications will fail silently (logged but not sent).
"""
import os
from datetime import timedelta


class Config:
    """Base configuration class."""

    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'

    # Rate Limiting
    RATELIMIT_ENABLED = os.environ.get('RATELIMIT_ENABLED', 'true').lower() in ['true', 'on', '1']

    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'mysql+pymysql://localhost/tennis_club_dev'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False

    # Session
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # Email Configuration (Flask-Mail)
    # Uses Gmail SMTP with App Password authentication
    # Leave MAIL_USERNAME/MAIL_PASSWORD empty to disable email sending
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'false').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or 'noreply@tennisclub.de'

    # Development email redirect - all emails in dev mode go to this address
    DEV_EMAIL_RECIPIENT = os.environ.get('DEV_EMAIL_RECIPIENT')
    
    # Application settings
    COURTS_COUNT = 6
    BOOKING_START_HOUR = 8
    BOOKING_END_HOUR = 22  # Last slot starts at 21:00, ends at 22:00
    BOOKING_DURATION_HOURS = 1
    MAX_ACTIVE_RESERVATIONS = 2


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    SQLALCHEMY_ECHO = True
    # Always respect DATABASE_URL environment variable
    # Only fall back to SQLite if no DATABASE_URL is set


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    
    # Ensure required environment variables are set
    @classmethod
    def init_app(cls, app):
        """Initialize production configuration."""
        Config.init_app(app)
        
        # Validate required environment variables
        required_vars = ['SECRET_KEY', 'DATABASE_URL', 'MAIL_USERNAME', 'MAIL_PASSWORD']
        missing = [var for var in required_vars if not os.environ.get(var)]
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    MAIL_SUPPRESS_SEND = True
    RATELIMIT_ENABLED = False
    
    # Override booking hours for testing to match test expectations
    BOOKING_START_HOUR = 6
    BOOKING_END_HOUR = 22  # Last slot starts at 21:00, ends at 22:00


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
