"""Pytest configuration and fixtures."""
import pytest
from app import create_app, db
from app.models import Member, Court, BlockReason
from flask_mail import Mail


@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app('testing')
    
    with app.app_context():
        db.create_all()
        
        # Create courts
        for i in range(1, 7):
            court = Court(number=i)
            db.session.add(court)
        
        # Create a default admin for block reasons
        admin = Member(
            firstname='System',
            lastname='Admin',
            email='system@example.com',
            role='administrator'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        
        # Create default block reasons
        default_reasons = ['Maintenance', 'Weather', 'Tournament', 'Championship', 'Tennis Course']
        for reason_name in default_reasons:
            reason = BlockReason(
                name=reason_name,
                is_active=True,
                created_by_id=admin.id
            )
            db.session.add(reason)
        
        db.session.commit()
        
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create test CLI runner."""
    return app.test_cli_runner()


@pytest.fixture
def test_member(app):
    """Create a test member."""
    with app.app_context():
        member = Member(
            firstname='Test',
            lastname='Member',
            email='test@example.com',
            role='member'
        )
        member.set_password('password123')
        db.session.add(member)
        db.session.commit()
        
        # Refresh to get the ID
        db.session.refresh(member)
        member_id = member.id
        member_email = member.email
    
    # Return a fresh instance
    with app.app_context():
        return Member.query.filter_by(email=member_email).first()


@pytest.fixture
def test_admin(app):
    """Create a test admin."""
    with app.app_context():
        admin = Member(
            firstname='Test',
            lastname='Admin',
            email='admin@example.com',
            role='administrator'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        
        # Refresh to get the ID
        db.session.refresh(admin)
        admin_email = admin.email
    
    # Return a fresh instance
    with app.app_context():
        return Member.query.filter_by(email=admin_email).first()


@pytest.fixture
def mail(app):
    """Create mail instance for testing."""
    from flask_mail import Mail
    mail = Mail(app)
    return mail
