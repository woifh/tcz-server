"""WSGI entry point for PythonAnywhere deployment."""
import os
from app import create_app

# Load environment variables from .env file if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Create application instance
config_name = os.environ.get('FLASK_ENV', 'production')
application = create_app(config_name)

if __name__ == '__main__':
    application.run()
