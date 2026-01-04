"""Integration tests for active booking session logic with existing workflows."""
import pytest
from datetime import date, time, datetime, timedelta
from app import create_app, db
from app.models import Member, Court, Reservation
from app.services.reservation_service import ReservationService
from app.services.validation_service import ValidationService
from app.services.email_service import EmailService
from unittest.mock import patch, MagicMock


class TestActiveBookingSessionIntegration:
    """Integration tests for active booking session logic with existing workflows."""
    
    @pytest.fixture
    def app(self):
        """Create test app."""
        app = create_app('testing')
        with app.app_context():
            db.create_all()
            
            # Create courts
            for i in range(1, 7):
                court = Court(number=i)
                db.session.add(court)
            db.session.commit()
            
            yield app
            
            db.session.remove()
            db.drop_all()
    
    @pytest.fixture
    def test_court(self, app):
        """Get test court."""
        with app.app_context():
            return Court.query.filter_by(number=1).first()
    
    def create_test_member(self, email="test@example.com"):
        """Create a test member in the current app context."""
        member = Member(
            firstname="Test",
            lastname="Member",
            email=email,
            role="member"
        )
        member.set_password("password123")
        db.session.add(member)
        db.session.commit()
        return member
    
    def test_reservation_creation_with_time_based_validation(self, app, test_court):
        """Test that reservation creation works correctly with time-based validation."""
        with app.app_context():
            test_member = self.create_test_member("test1@example.com")
            
            # Test creating a reservation for tomorrow
            tomorrow = date.today() + timedelta(days=1)
            start_time = time(10, 0)
            current_time = datetime.now()
            
            # Create reservation
            reservation, error = ReservationService.create_reservation(
                court_id=test_court.id,
                date=tomorrow,
                start_time=start_time,
                booked_for_id=test_member.id,
                booked_by_id=test_member.id,
                current_time=current_time
            )
            
            # Verify reservation was created successfully
            assert reservation is not None, f"Reservation creation failed: {error}"
            assert error is None
            assert reservation.status == 'active'
            assert reservation.date == tomorrow
            assert reservation.start_time == start_time
            assert reservation.end_time == time(11, 0)
            
            # Verify the reservation is considered active using time-based logic
            is_active = ReservationService.is_reservation_currently_active(reservation, current_time)
            assert is_active is True, "Future reservation should be considered active"
            
            # Verify it appears in active booking sessions
            active_sessions = ReservationService.get_member_active_booking_sessions(
                test_member.id, current_time=current_time
            )
            assert len(active_sessions) == 1
            assert active_sessions[0].id == reservation.id
    
    def test_reservation_creation_short_notice_classification(self, app, test_court):
        """Test that short notice reservations are correctly classified and handled."""
        with app.app_context():
            test_member = self.create_test_member("test2@example.com")
            
            # Create a reservation for tomorrow at 10:00 AM, but set current time to be 10 minutes before
            tomorrow = date.today() + timedelta(days=1)
            start_time = time(10, 0)
            
            # Set current time to be 10 minutes before the booking (short notice)
            test_current_time = datetime.combine(tomorrow, time(9, 50))
            
            # Create reservation
            reservation, error = ReservationService.create_reservation(
                court_id=test_court.id,
                date=tomorrow,
                start_time=start_time,
                booked_for_id=test_member.id,
                booked_by_id=test_member.id,
                current_time=test_current_time
            )
            
            # Verify reservation was created successfully
            assert reservation is not None, f"Short notice reservation creation failed: {error}"
            assert error is None
            assert reservation.is_short_notice is True, "Reservation should be marked as short notice"
            
            # Verify it doesn't count toward regular reservation limit
            regular_sessions = ReservationService.get_member_active_booking_sessions(
                test_member.id, include_short_notice=False, current_time=test_current_time
            )
            assert len(regular_sessions) == 0, "Short notice booking should not count toward regular limit"
            
            # Verify it appears in short notice bookings
            short_notice_bookings = ReservationService.get_member_active_short_notice_bookings(
                test_member.id, current_time=test_current_time
            )
            assert len(short_notice_bookings) == 1
            assert short_notice_bookings[0].id == reservation.id
    
    def test_reservation_limit_enforcement_with_time_based_logic(self, app, test_court):
        """Test that reservation limits are enforced correctly with time-based logic."""
        with app.app_context():
            test_member = self.create_test_member("test3@example.com")
            current_time = datetime.now()
            
            # Create 2 active reservations (at the limit)
            for i in range(2):
                future_date = date.today() + timedelta(days=i+1)
                reservation = Reservation(
                    court_id=test_court.id,
                    date=future_date,
                    start_time=time(10, 0),
                    end_time=time(11, 0),
                    booked_for_id=test_member.id,
                    booked_by_id=test_member.id,
                    status='active',
                    is_short_notice=False
                )
                db.session.add(reservation)
            db.session.commit()
            
            # Verify member is at the limit
            can_book = ValidationService.validate_member_reservation_limit(
                test_member.id, is_short_notice=False, current_time=current_time
            )
            assert can_book is False, "Member should be at reservation limit"
            
            # Try to create another regular reservation (should fail)
            future_date = date.today() + timedelta(days=5)
            reservation, error = ReservationService.create_reservation(
                court_id=test_court.id,
                date=future_date,
                start_time=time(12, 0),
                booked_for_id=test_member.id,
                booked_by_id=test_member.id,
                current_time=current_time
            )
            
            assert reservation is None, "Reservation creation should fail when at limit"
            assert error is not None
            assert "bereits 2 aktive Buchungen" in error or "reservation limit" in error.lower()
            
            # But short notice booking should still be allowed
            can_book_short_notice = ValidationService.validate_member_reservation_limit(
                test_member.id, is_short_notice=True, current_time=current_time
            )
            assert can_book_short_notice is True, "Short notice bookings should be allowed even at regular limit"
    
    def test_cancellation_logic_with_time_based_validation(self, app, test_court):
        """Test that cancellation logic works correctly with time-based validation."""
        with app.app_context():
            test_member = self.create_test_member("test4@example.com")
            
            # Create a reservation for a future time that allows proper testing
            # Use tomorrow at 10:00 AM for predictable testing
            tomorrow = date.today() + timedelta(days=1)
            start_time = time(10, 0)
            
            reservation = Reservation(
                court_id=test_court.id,
                date=tomorrow,
                start_time=start_time,
                end_time=time(11, 0),
                booked_for_id=test_member.id,
                booked_by_id=test_member.id,
                status='active',
                is_short_notice=False
            )
            db.session.add(reservation)
            db.session.commit()
            
            # Test cancellation 30 minutes before start (should be allowed)
            # Set current time to 30 minutes before the reservation starts
            test_time_30_min_before = datetime.combine(tomorrow, time(9, 30))
            is_allowed, error_msg = ValidationService.validate_cancellation_allowed(
                reservation.id, current_time=test_time_30_min_before
            )
            assert is_allowed is True, f"Cancellation should be allowed 30 minutes before start, but got: {error_msg}"
            
            # Test cancellation 10 minutes before start (should be blocked)
            test_time_10_min_before = datetime.combine(tomorrow, time(9, 50))
            is_allowed, error_msg = ValidationService.validate_cancellation_allowed(
                reservation.id, current_time=test_time_10_min_before
            )
            assert is_allowed is False, "Cancellation should be blocked within 15 minutes of start"
            assert "weniger als 15 Minuten" in error_msg or "15 minutes" in error_msg.lower()
            
            # Test cancellation after start (should be blocked)
            test_time_after_start = datetime.combine(tomorrow, time(10, 5))
            is_allowed, error_msg = ValidationService.validate_cancellation_allowed(
                reservation.id, current_time=test_time_after_start
            )
            assert is_allowed is False, "Cancellation should be blocked after start"
    
    def test_short_notice_booking_cannot_be_cancelled(self, app, test_court):
        """Test that short notice bookings cannot be cancelled regardless of timing."""
        with app.app_context():
            test_member = self.create_test_member("test5@example.com")
            
            # Create a short notice reservation for tomorrow (plenty of time)
            tomorrow = date.today() + timedelta(days=1)
            current_time = datetime.now()
            
            reservation = Reservation(
                court_id=test_court.id,
                date=tomorrow,
                start_time=time(10, 0),
                end_time=time(11, 0),
                booked_for_id=test_member.id,
                booked_by_id=test_member.id,
                status='active',
                is_short_notice=True
            )
            db.session.add(reservation)
            db.session.commit()
            
            # Test cancellation (should be blocked even with plenty of time)
            is_allowed, error_msg = ValidationService.validate_cancellation_allowed(
                reservation.id, current_time=current_time
            )
            assert is_allowed is False, "Short notice bookings should never be cancellable"
            assert "Kurzfristige Buchungen können nicht storniert werden" in error_msg or \
                   "short notice" in error_msg.lower()
    
    @patch.object(EmailService, 'send_booking_created')
    def test_email_notifications_include_correct_status_information(self, mock_email, app, test_court):
        """Test that email notifications include correct status information."""
        with app.app_context():
            test_member = self.create_test_member("test6@example.com")
            
            # Create a regular reservation
            tomorrow = date.today() + timedelta(days=1)
            current_time = datetime.now()
            
            reservation, error = ReservationService.create_reservation(
                court_id=test_court.id,
                date=tomorrow,
                start_time=time(10, 0),
                booked_for_id=test_member.id,
                booked_by_id=test_member.id,
                current_time=current_time
            )
            
            # Verify reservation was created and email was called
            assert reservation is not None
            assert mock_email.called
            
            # Verify the reservation object passed to email has correct status
            called_reservation = mock_email.call_args[0][0]
            assert called_reservation.status == 'active'
            assert called_reservation.is_short_notice is False
            
            # Verify the reservation is considered active
            is_active = ReservationService.is_reservation_currently_active(
                called_reservation, current_time
            )
            assert is_active is True
    
    def test_time_based_logic_handles_edge_cases(self, app, test_court):
        """Test that time-based logic handles edge cases correctly."""
        with app.app_context():
            test_member = self.create_test_member("test7@example.com")
            
            # Test exact time boundaries
            today = date.today()
            
            # Create a reservation that ends at exactly the current time
            current_time = datetime.combine(today, time(11, 0))  # 11:00 AM
            reservation = Reservation(
                court_id=test_court.id,
                date=today,
                start_time=time(10, 0),
                end_time=time(11, 0),  # Ends exactly at current time
                booked_for_id=test_member.id,
                booked_by_id=test_member.id,
                status='active',
                is_short_notice=False
            )
            db.session.add(reservation)
            db.session.commit()
            
            # Test that reservation ending exactly at current time is NOT active
            is_active = ReservationService.is_reservation_currently_active(
                reservation, current_time
            )
            assert is_active is False, "Reservation ending exactly at current time should not be active"
            
            # Test that it doesn't appear in active booking sessions
            active_sessions = ReservationService.get_member_active_booking_sessions(
                test_member.id, current_time=current_time
            )
            assert len(active_sessions) == 0, "Ended reservation should not appear in active sessions"
            
            # Test reservation that ends 1 minute after current time (should be active)
            current_time_minus_1 = datetime.combine(today, time(10, 59))  # 10:59 AM
            is_active = ReservationService.is_reservation_currently_active(
                reservation, current_time_minus_1
            )
            assert is_active is True, "Reservation ending after current time should be active"
    
    def test_midnight_spanning_reservations(self, app, test_court):
        """Test that reservations spanning midnight are handled correctly."""
        with app.app_context():
            test_member = self.create_test_member("test8@example.com")
            
            # Create a reservation for the last slot (21:00-22:00)
            today = date.today()
            current_time = datetime.combine(today, time(20, 30))  # 8:30 PM
            
            reservation = Reservation(
                court_id=test_court.id,
                date=today,
                start_time=time(21, 0),  # 9:00 PM
                end_time=time(22, 0),    # 10:00 PM
                booked_for_id=test_member.id,
                booked_by_id=test_member.id,
                status='active',
                is_short_notice=False
            )
            db.session.add(reservation)
            db.session.commit()
            
            # Test that the reservation is active before it starts
            is_active = ReservationService.is_reservation_currently_active(
                reservation, current_time
            )
            assert is_active is True, "Future reservation should be active"
            
            # Test that the reservation is active during the slot
            during_time = datetime.combine(today, time(21, 30))  # 9:30 PM
            is_active = ReservationService.is_reservation_currently_active(
                reservation, during_time
            )
            assert is_active is True, "Current reservation should be active"
            
            # Test that the reservation is not active after it ends
            after_time = datetime.combine(today, time(22, 1))  # 10:01 PM
            is_active = ReservationService.is_reservation_currently_active(
                reservation, after_time
            )
            assert is_active is False, "Past reservation should not be active"
    
    def test_timezone_consistency_across_operations(self, app, test_court):
        """Test that timezone handling is consistent across all operations."""
        with app.app_context():
            test_member = self.create_test_member("test9@example.com")
            
            # Use a specific time for consistency
            current_time = datetime(2024, 1, 15, 14, 30)  # 2:30 PM
            tomorrow = date(2024, 1, 16)
            
            # Create reservation
            reservation, error = ReservationService.create_reservation(
                court_id=test_court.id,
                date=tomorrow,
                start_time=time(10, 0),
                booked_for_id=test_member.id,
                booked_by_id=test_member.id,
                current_time=current_time
            )
            
            assert reservation is not None
            
            # Test that all time-based operations use consistent timezone
            is_active_service = ReservationService.is_reservation_currently_active(
                reservation, current_time
            )
            
            is_active_direct = ReservationService.is_reservation_active_by_time(
                reservation.date, reservation.end_time, current_time
            )
            
            active_sessions = ReservationService.get_member_active_booking_sessions(
                test_member.id, current_time=current_time
            )
            
            # All should give consistent results
            assert is_active_service is True
            assert is_active_direct is True
            assert len(active_sessions) == 1
            assert active_sessions[0].id == reservation.id
    
    def test_performance_with_multiple_reservations(self, app, test_court):
        """Test that time-based queries perform well with multiple reservations."""
        with app.app_context():
            test_member = self.create_test_member("test10@example.com")
            current_time = datetime.now()
            
            # Create multiple reservations (mix of past, current, and future)
            reservations = []
            for i in range(10):
                reservation_date = date.today() + timedelta(days=i-5)  # Some past, some future
                reservation = Reservation(
                    court_id=test_court.id,
                    date=reservation_date,
                    start_time=time(10, 0),
                    end_time=time(11, 0),
                    booked_for_id=test_member.id,
                    booked_by_id=test_member.id,
                    status='active',
                    is_short_notice=(i % 3 == 0)  # Some short notice
                )
                db.session.add(reservation)
                reservations.append(reservation)
            db.session.commit()
            
            # Test that queries complete quickly and return correct results
            import time as time_module
            start_time = time_module.time()
            
            active_sessions = ReservationService.get_member_active_booking_sessions(
                test_member.id, current_time=current_time
            )
            
            end_time = time_module.time()
            query_time = end_time - start_time
            
            # Query should complete quickly (less than 1 second)
            assert query_time < 1.0, f"Query took too long: {query_time} seconds"
            
            # Should only return future/current reservations
            for session in active_sessions:
                is_active = ReservationService.is_reservation_currently_active(
                    session, current_time
                )
                assert is_active is True, "All returned sessions should be active"