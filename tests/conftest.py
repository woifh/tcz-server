"""Pytest configuration and fixtures."""
import pytest
from app import create_app, db
from app.models import Member, Court, BlockReason
from flask_mailman import Mail


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


class MemberData:
    """Simple data holder for member info that doesn't require session."""
    def __init__(self, id, email, firstname, lastname, role):
        self.id = id
        self.email = email
        self.firstname = firstname
        self.lastname = lastname
        self.role = role

    @property
    def name(self):
        """Return full name like the Member model does."""
        return f"{self.firstname} {self.lastname}"


@pytest.fixture
def test_member(app):
    """Create a test member and return its data."""
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

        # Return a simple data object with member info
        return MemberData(
            id=member.id,
            email=member.email,
            firstname=member.firstname,
            lastname=member.lastname,
            role=member.role
        )


@pytest.fixture
def test_admin(app):
    """Create a test admin and return its data."""
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

        # Return a simple data object with admin info
        return MemberData(
            id=admin.id,
            email=admin.email,
            firstname=admin.firstname,
            lastname=admin.lastname,
            role=admin.role
        )


@pytest.fixture
def mail(app):
    """Create mail instance for testing."""
    from flask_mailman import Mail
    mail = Mail(app)
    return mail


@pytest.fixture
def database(app):
    """Provide database access within app context."""
    return db
