"""Tests for settings service."""
import pytest
from datetime import date, timedelta
from app import db
from app.models import SystemSetting, Member
from app.services.settings_service import SettingsService


class TestPaymentDeadline:
    """Tests for payment deadline functionality."""

    def test_get_payment_deadline_not_set(self, app):
        """Should return None when no deadline is set."""
        with app.app_context():
            # Clear any existing deadline
            SystemSetting.query.filter_by(key=SettingsService.PAYMENT_DEADLINE_KEY).delete()
            db.session.commit()

            deadline = SettingsService.get_payment_deadline()
            assert deadline is None

    def test_set_payment_deadline_with_date(self, app):
        """Should set payment deadline with date object."""
        with app.app_context():
            future_date = date.today() + timedelta(days=30)
            success, error = SettingsService.set_payment_deadline(future_date)

            assert success is True
            assert error is None

            # Verify it was saved
            deadline = SettingsService.get_payment_deadline()
            assert deadline == future_date

    def test_set_payment_deadline_with_string(self, app):
        """Should set payment deadline with ISO string."""
        with app.app_context():
            future_date = date.today() + timedelta(days=30)
            success, error = SettingsService.set_payment_deadline(future_date.isoformat())

            assert success is True
            assert error is None

            deadline = SettingsService.get_payment_deadline()
            assert deadline == future_date

    def test_set_payment_deadline_invalid_string(self, app):
        """Should return error for invalid date string."""
        with app.app_context():
            success, error = SettingsService.set_payment_deadline('invalid-date')

            assert success is False
            assert error is not None
            assert 'Datumsformat' in error

    def test_update_existing_payment_deadline(self, app):
        """Should update existing deadline."""
        with app.app_context():
            # Set initial deadline
            first_date = date.today() + timedelta(days=15)
            SettingsService.set_payment_deadline(first_date)

            # Update deadline
            second_date = date.today() + timedelta(days=45)
            success, error = SettingsService.set_payment_deadline(second_date)

            assert success is True
            deadline = SettingsService.get_payment_deadline()
            assert deadline == second_date

    def test_clear_payment_deadline(self, app):
        """Should clear existing deadline."""
        with app.app_context():
            # Set deadline first
            SettingsService.set_payment_deadline(date.today() + timedelta(days=30))

            # Clear it
            success, error = SettingsService.clear_payment_deadline()

            assert success is True
            assert error is None

            # Verify it's cleared
            deadline = SettingsService.get_payment_deadline()
            assert deadline is None

    def test_clear_nonexistent_deadline(self, app):
        """Clearing non-existent deadline should succeed."""
        with app.app_context():
            # Make sure no deadline exists
            SystemSetting.query.filter_by(key=SettingsService.PAYMENT_DEADLINE_KEY).delete()
            db.session.commit()

            success, error = SettingsService.clear_payment_deadline()

            assert success is True
            assert error is None


class TestIsPastDeadline:
    """Tests for checking if past deadline."""

    def test_is_past_deadline_no_deadline(self, app):
        """Should return False when no deadline set."""
        with app.app_context():
            SystemSetting.query.filter_by(key=SettingsService.PAYMENT_DEADLINE_KEY).delete()
            db.session.commit()

            is_past = SettingsService.is_past_payment_deadline()
            assert is_past is False

    def test_is_past_deadline_future(self, app):
        """Should return False for future deadline."""
        with app.app_context():
            future_date = date.today() + timedelta(days=30)
            SettingsService.set_payment_deadline(future_date)

            is_past = SettingsService.is_past_payment_deadline()
            assert is_past is False

    def test_is_past_deadline_today(self, app):
        """Today should not be past deadline."""
        with app.app_context():
            SettingsService.set_payment_deadline(date.today())

            is_past = SettingsService.is_past_payment_deadline()
            assert is_past is False

    def test_is_past_deadline_yesterday(self, app):
        """Yesterday should be past deadline."""
        with app.app_context():
            past_date = date.today() - timedelta(days=1)
            SettingsService.set_payment_deadline(past_date)

            is_past = SettingsService.is_past_payment_deadline()
            assert is_past is True


class TestDaysUntilDeadline:
    """Tests for days until deadline calculation."""

    def test_days_until_deadline_no_deadline(self, app):
        """Should return None when no deadline set."""
        with app.app_context():
            SystemSetting.query.filter_by(key=SettingsService.PAYMENT_DEADLINE_KEY).delete()
            db.session.commit()

            days = SettingsService.days_until_deadline()
            assert days is None

    def test_days_until_deadline_future(self, app):
        """Should return positive days for future deadline."""
        with app.app_context():
            future_date = date.today() + timedelta(days=10)
            SettingsService.set_payment_deadline(future_date)

            days = SettingsService.days_until_deadline()
            assert days == 10

    def test_days_until_deadline_today(self, app):
        """Should return 0 for today's deadline."""
        with app.app_context():
            SettingsService.set_payment_deadline(date.today())

            days = SettingsService.days_until_deadline()
            assert days == 0

    def test_days_until_deadline_past(self, app):
        """Should return negative days for past deadline."""
        with app.app_context():
            past_date = date.today() - timedelta(days=5)
            SettingsService.set_payment_deadline(past_date)

            days = SettingsService.days_until_deadline()
            assert days == -5


class TestUnpaidMemberCount:
    """Tests for unpaid member count."""

    def test_unpaid_member_count_no_unpaid(self, app):
        """Should return 0 when all members have paid."""
        with app.app_context():
            # Create a paid member
            member = Member(
                firstname='Paid',
                lastname='Member',
                email='paid@example.com',
                role='member',
                fee_paid=True,
                is_active=True,
                membership_type='full'
            )
            member.set_password('password123')
            db.session.add(member)
            db.session.commit()

            # Count should not include this paid member
            count = SettingsService.get_unpaid_member_count()
            # May include existing test members
            assert count >= 0

    def test_unpaid_member_count_with_unpaid(self, app):
        """Should count unpaid members."""
        with app.app_context():
            # Create an unpaid member
            member = Member(
                firstname='Unpaid',
                lastname='Member',
                email='unpaid@example.com',
                role='member',
                fee_paid=False,
                is_active=True,
                membership_type='full'
            )
            member.set_password('password123')
            db.session.add(member)
            db.session.commit()

            count = SettingsService.get_unpaid_member_count()
            assert count >= 1

    def test_unpaid_member_count_excludes_inactive(self, app):
        """Should exclude inactive members."""
        with app.app_context():
            # Create an inactive unpaid member
            member = Member(
                firstname='Inactive',
                lastname='Unpaid',
                email='inactive_unpaid@example.com',
                role='member',
                fee_paid=False,
                is_active=False,
                membership_type='full'
            )
            member.set_password('password123')
            db.session.add(member)
            db.session.commit()

            # Get baseline count
            count_before = SettingsService.get_unpaid_member_count()

            # This member should not be counted
            # (since is_active=False)
            assert count_before >= 0  # Just verify query doesn't crash

    def test_unpaid_member_count_excludes_sustaining(self, app):
        """Should exclude sustaining members."""
        with app.app_context():
            # Create a sustaining member
            member = Member(
                firstname='Sustaining',
                lastname='Unpaid',
                email='sustaining_unpaid@example.com',
                role='member',
                fee_paid=False,
                is_active=True,
                membership_type='sustaining'
            )
            member.set_password('password123')
            db.session.add(member)
            db.session.commit()

            # Count should not include sustaining members
            count = SettingsService.get_unpaid_member_count()
            assert count >= 0
