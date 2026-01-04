"""Reservation service for business logic."""
from datetime import time, timedelta, datetime
from app import db
from app.models import Reservation
from app.services.validation_service import ValidationService
from app.services.email_service import EmailService


class ReservationService:
    """Service for managing reservations."""
    
    @staticmethod
    def is_short_notice_booking(date, start_time, current_time=None):
        """
        Check if a booking would be classified as short notice.
        
        Args:
            date: Reservation date (assumed to be in CET/CEST timezone)
            start_time: Reservation start time (assumed to be in CET/CEST timezone)
            current_time: Current datetime (defaults to CET/CEST now)
            
        Returns:
            bool: True if booking is within 15 minutes of start time
        """
        if current_time is None:
            # Use CET/CEST timezone (UTC+1/UTC+2)
            import pytz
            try:
                cet = pytz.timezone('Europe/Vienna')  # Austria timezone (CET/CEST)
                current_time = datetime.now(cet).replace(tzinfo=None)  # Convert to naive local time
            except:
                # Fallback: assume UTC+1 (CET) for now
                from datetime import timedelta
                current_time = datetime.utcnow() + timedelta(hours=1)
        
        # Ensure we're comparing like with like - both should be naive datetimes
        # representing the same timezone (CET/CEST)
        reservation_datetime = datetime.combine(date, start_time)
        
        # If current_time is timezone-aware, convert to naive local time
        if hasattr(current_time, 'tzinfo') and current_time.tzinfo is not None:
            current_time = current_time.replace(tzinfo=None)
        
        time_until_start = reservation_datetime - current_time
        
        # Debug logging
        print(f"DEBUG Short Notice Check:")
        print(f"  Reservation datetime: {reservation_datetime}")
        print(f"  Current time (CET/CEST): {current_time}")
        print(f"  Time until start: {time_until_start}")
        print(f"  Is short notice: {time_until_start <= timedelta(minutes=15)}")
        
        # If reservation starts in 15 minutes or less, it's short notice
        return time_until_start <= timedelta(minutes=15)
    
    @staticmethod
    def classify_booking_type(date, start_time, current_time=None):
        """
        Classify a booking as regular or short notice.
        
        Args:
            date: Reservation date
            start_time: Reservation start time
            current_time: Current datetime (defaults to now)
            
        Returns:
            str: 'short_notice' or 'regular'
        """
        if ReservationService.is_short_notice_booking(date, start_time, current_time):
            return 'short_notice'
        return 'regular'
    
    @staticmethod
    def get_member_regular_reservations(member_id):
        """
        Get active regular reservations for a member (excludes short notice bookings).
        Only returns future reservations (today or later).
        
        Args:
            member_id: ID of the member
            
        Returns:
            list: List of active regular Reservation objects
        """
        from datetime import date as date_class
        today = date_class.today()
        
        return Reservation.query.filter(
            (Reservation.booked_for_id == member_id) | (Reservation.booked_by_id == member_id),
            Reservation.status == 'active',
            Reservation.date >= today,
            Reservation.is_short_notice == False
        ).order_by(Reservation.date, Reservation.start_time).all()
    
    @staticmethod
    def create_reservation(court_id, date, start_time, booked_for_id, booked_by_id):
        """
        Create a new reservation.
        
        Args:
            court_id: ID of the court
            date: Reservation date
            start_time: Start time
            booked_for_id: ID of member the reservation is for
            booked_by_id: ID of member creating the reservation
            
        Returns:
            tuple: (Reservation object or None, error message or None)
        """
        # Determine if this is a short notice booking
        is_short_notice = ReservationService.is_short_notice_booking(date, start_time)
        
        # Log reservation creation
        print(f"Creating reservation - date={date}, start_time={start_time}, is_short_notice={is_short_notice}")
        
        # Validate all constraints (pass short notice flag for proper validation)
        is_valid, error_msg = ValidationService.validate_all_booking_constraints(
            court_id, date, start_time, booked_for_id, is_short_notice
        )
        
        if not is_valid:
            return None, error_msg
        
        # Calculate end time (1 hour after start)
        end_time = time(start_time.hour + 1, start_time.minute)
        
        # Create reservation
        reservation = Reservation(
            court_id=court_id,
            date=date,
            start_time=start_time,
            end_time=end_time,
            booked_for_id=booked_for_id,
            booked_by_id=booked_by_id,
            status='active',
            is_short_notice=is_short_notice
        )
        
        try:
            db.session.add(reservation)
            db.session.commit()
            
            # Send email notifications (don't fail if email fails)
            EmailService.send_booking_created(reservation)
            
            return reservation, None
        except Exception as e:
            db.session.rollback()
            # Check if it's a duplicate booking error
            if 'Duplicate entry' in str(e) and 'unique_booking' in str(e):
                return None, "Dieser Platz ist bereits für diese Zeit gebucht"
            return None, f"Fehler beim Erstellen der Buchung: {str(e)}"
    
    @staticmethod
    def update_reservation(reservation_id, **updates):
        """
        Update an existing reservation.
        
        Args:
            reservation_id: ID of the reservation
            **updates: Fields to update
            
        Returns:
            tuple: (Reservation object or None, error message or None)
        """
        reservation = Reservation.query.get(reservation_id)
        if not reservation:
            return None, "Buchung nicht gefunden"
        
        # Update fields
        for key, value in updates.items():
            if hasattr(reservation, key):
                setattr(reservation, key, value)
        
        try:
            db.session.commit()
            
            # Send email notifications
            EmailService.send_booking_modified(reservation)
            
            return reservation, None
        except Exception as e:
            db.session.rollback()
            return None, f"Fehler beim Aktualisieren der Buchung: {str(e)}"
    
    @staticmethod
    def cancel_reservation(reservation_id, reason=None):
        """
        Cancel a reservation.
        Uses enhanced validation that prevents cancellation within 15 minutes of start time,
        once the slot has started, or for short notice bookings.
        
        Args:
            reservation_id: ID of the reservation
            reason: Optional cancellation reason
            
        Returns:
            tuple: (success boolean, error message or None)
        """
        # Use the enhanced validation service
        is_allowed, error_msg = ValidationService.validate_cancellation_allowed(reservation_id)
        
        if not is_allowed:
            return False, error_msg
        
        reservation = Reservation.query.get(reservation_id)
        reservation.status = 'cancelled'
        if reason:
            reservation.reason = reason
        
        try:
            db.session.commit()
            
            # Send email notifications
            EmailService.send_booking_cancelled(reservation, reason)
            
            return True, None
        except Exception as e:
            db.session.rollback()
            return False, f"Fehler beim Stornieren der Buchung: {str(e)}"
    
    @staticmethod
    def get_member_active_reservations(member_id, include_short_notice=True):
        """
        Get active reservations for a member.
        Only returns future reservations (today or later).
        
        Args:
            member_id: ID of the member
            include_short_notice: Whether to include short notice bookings (default True)
            
        Returns:
            list: List of active Reservation objects
        """
        from datetime import date as date_class
        today = date_class.today()
        
        query = Reservation.query.filter(
            (Reservation.booked_for_id == member_id) | (Reservation.booked_by_id == member_id),
            Reservation.status == 'active',
            Reservation.date >= today
        )
        
        if not include_short_notice:
            query = query.filter(Reservation.is_short_notice == False)
        
        return query.order_by(Reservation.date, Reservation.start_time).all()
    
    @staticmethod
    def check_availability(court_id, date, start_time):
        """
        Check if a court is available.
        
        Args:
            court_id: ID of the court
            date: Date to check
            start_time: Time to check
            
        Returns:
            bool: True if available, False otherwise
        """
        return ValidationService.validate_no_conflict(court_id, date, start_time) and \
               ValidationService.validate_not_blocked(court_id, date, start_time)
    
    @staticmethod
    def get_reservations_by_date(date):
        """
        Get all reservations for a date.
        
        Args:
            date: Date to query
            
        Returns:
            list: List of Reservation objects
        """
        return Reservation.query.filter_by(
            date=date,
            status='active'
        ).order_by(Reservation.start_time).all()
