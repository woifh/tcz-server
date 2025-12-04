"""Reservation service for business logic."""
from datetime import time, timedelta
from app import db
from app.models import Reservation
from app.services.validation_service import ValidationService
from app.services.email_service import EmailService


class ReservationService:
    """Service for managing reservations."""
    
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
        # Validate all constraints
        is_valid, error_msg = ValidationService.validate_all_booking_constraints(
            court_id, date, start_time, booked_for_id
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
            status='active'
        )
        
        try:
            db.session.add(reservation)
            db.session.commit()
            
            # Send email notifications (don't fail if email fails)
            EmailService.send_booking_created(reservation)
            
            return reservation, None
        except Exception as e:
            db.session.rollback()
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
        
        Args:
            reservation_id: ID of the reservation
            reason: Optional cancellation reason
            
        Returns:
            tuple: (success boolean, error message or None)
        """
        reservation = Reservation.query.get(reservation_id)
        if not reservation:
            return False, "Buchung nicht gefunden"
        
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
    def get_member_active_reservations(member_id):
        """
        Get active reservations for a member.
        
        Args:
            member_id: ID of the member
            
        Returns:
            list: List of active Reservation objects
        """
        return Reservation.query.filter(
            (Reservation.booked_for_id == member_id) | (Reservation.booked_by_id == member_id),
            Reservation.status == 'active'
        ).order_by(Reservation.date, Reservation.start_time).all()
    
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
