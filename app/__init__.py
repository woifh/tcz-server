"""Flask application factory for Tennis Club Reservation System."""
import os
import logging
from dotenv import load_dotenv
from flask import Flask, render_template

# Load .env file for local development (VS Code debugger doesn't auto-load it)
load_dotenv()
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect

from config import config

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()
migrate = Migrate()
csrf = CSRFProtect()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["2000 per day", "500 per hour"],
    storage_uri="memory://"
)


def create_app(config_name=None):
    """
    Create and configure the Flask application.
    
    Args:
        config_name: Configuration name ('development', 'production', 'testing', 'default')
                    If None, auto-detect from environment variables
        
    Returns:
        Configured Flask application instance
    """
    app = Flask(__name__)
    
    # Auto-detect configuration if not specified
    if config_name is None:
        # Check for explicit FLASK_CONFIG first
        config_name = os.environ.get('FLASK_CONFIG')
        
        if not config_name:
            # Auto-detect based on environment
            database_url = os.environ.get('DATABASE_URL', '')
            if database_url.startswith('mysql'):
                config_name = 'production'
            elif os.environ.get('FLASK_ENV') == 'production':
                config_name = 'production'
            elif os.environ.get('TESTING'):
                config_name = 'testing'
            else:
                config_name = 'development'
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Configure logging for anonymous access monitoring
    if not app.debug and not app.testing:
        # Set up anonymous access logger
        anonymous_logger = logging.getLogger('anonymous_access')
        anonymous_logger.setLevel(logging.INFO)
        
        # Create file handler for anonymous access logs
        log_dir = os.path.join(os.path.dirname(app.instance_path), 'logs')
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        file_handler = logging.FileHandler(os.path.join(log_dir, 'anonymous_access.log'))
        file_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        )
        file_handler.setFormatter(formatter)
        
        # Add handler to logger
        anonymous_logger.addHandler(file_handler)
    
    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    
    # Only enable rate limiting if not explicitly disabled
    if app.config.get('RATELIMIT_ENABLED', True):
        limiter.init_app(app)
    # If disabled, don't initialize limiter at all
    
    # Import models for Flask-Migrate
    from app import models
    
    # Configure Flask-Login
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Bitte melde dich an, um diese Seite zu sehen.'
    login_manager.login_message_category = 'info'
    
    # Import and register blueprints
    with app.app_context():
        from app.routes import auth, reservations, members, courts, admin
        from app.routes import api

        app.register_blueprint(auth.bp)
        app.register_blueprint(reservations.bp)
        app.register_blueprint(members.bp)
        app.register_blueprint(courts.bp)
        app.register_blueprint(admin.bp)
        app.register_blueprint(api.bp)

        # Register main dashboard route
        from app.routes import dashboard
        app.register_blueprint(dashboard.bp)
    
    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        from app.models import Member
        return Member.query.get(user_id)
    
    # Register error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html'), 403
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500
    
    # Disable caching in development
    @app.after_request
    def add_header(response):
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '-1'
        return response
    
    # Register CLI commands
    from app import cli
    cli.init_app(app)

    # Auto-reset payment status on January 1st
    with app.app_context():
        _check_annual_payment_reset(app)

    return app


def _check_annual_payment_reset(app):
    """Check if annual payment reset is needed on January 1st.

    This runs once per app startup and checks if today is January 1st.
    If so, and if payment statuses haven't been reset yet this year,
    it automatically resets all members' fee_paid status to False.
    """
    import logging
    from datetime import date
    from app.models import Member, SystemSetting

    logger = logging.getLogger(__name__)
    today = date.today()

    # Only run on January 1st
    if today.month != 1 or today.day != 1:
        return

    try:
        # Check if we already reset this year using a system setting
        current_year = today.year
        setting_key = f'payment_reset_year_{current_year}'

        # Try to get existing setting
        existing_setting = SystemSetting.query.filter_by(key=setting_key).first()

        if existing_setting:
            # Already reset this year
            logger.info(f'Payment reset already performed for {current_year}')
            return

        # Count members that need reset
        paid_count = Member.query.filter_by(fee_paid=True).count()

        if paid_count == 0:
            logger.info('No members need payment status reset')
            # Still mark as done so we don't check again
            new_setting = SystemSetting(key=setting_key, value='done')
            db.session.add(new_setting)
            db.session.commit()
            return

        # Perform the reset
        from app.services.member_service import MemberService
        reset_count, error = MemberService.reset_all_payment_status()

        if error:
            logger.error(f'Failed to auto-reset payment status: {error}')
            return

        # Mark as done for this year
        new_setting = SystemSetting(key=setting_key, value='done')
        db.session.add(new_setting)
        db.session.commit()

        logger.info(f'Auto-reset payment status for {reset_count} members on {today}')

    except Exception as e:
        logger.error(f'Error during annual payment reset check: {e}')
