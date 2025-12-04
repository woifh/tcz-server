"""Test Flask application factory."""
import pytest
from app import create_app


def test_app_creation():
    """Test that the app can be created."""
    app = create_app('testing')
    assert app is not None
    assert app.config['TESTING'] is True


def test_app_config_development():
    """Test development configuration."""
    app = create_app('development')
    assert app.config['DEBUG'] is True


def test_app_config_production():
    """Test production configuration."""
    app = create_app('production')
    assert app.config['DEBUG'] is False
