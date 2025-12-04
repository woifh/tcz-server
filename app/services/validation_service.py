"""Validation service for business rules."""
from datetime import time
from flask import current_app
from app.models import Reservation, Block
from app import db


class ValidationService:
    """Service for validating booking constraints."""
    
    @staticmethod
    def validate_booking_time(start_time):
        """
        Validate booking time is within allowed hours (06:00-20:00).
        
        Args:
            start_time: time object representing the start time
            
        Returns:
            bool: True if valid, False otherwise
        """
        booking_start = current_app.config.get('BOOKING_START_HOUR', 6)
        booking_end = current_app.config.get('BOOKING_END_HOUR', 21)
        
        # Start time must be between 06:00 and 20:00 (last slot starts at 20:00)
        min_time = time(booking_start, 0)
        max_time = time(booking_end - 1, 0)
        
        return min_time <= start_time <= max_time
    
    @staticmethod
    def validate_member_reservation_limit(member_id):
        """
        Validate member has not exceeded the 2-reservation limit.
        
        Args:
            member_id: ID of the member
            
        Returns:
            bool: True if member can make another reservation, False otherwise
        """
        max_reservations = current_app.config.get('MAX_ACTIVE_RESERVATIONS', 2)
        
        # Count active reservations where member is booked_for
        active_count = Reservation.query.filter_by(
            booked_for_id=member_id,
            status='active'
        ).count()
        
        return active_count < max_reservations
    
    @staticmethod
    def validate_no_conflict(court_id, date, start_time):
        """
        Validate no conflicting reservations exist.
        
        Args:
            court_id: ID of the court
            date: date object
            start_time: time object
            
        Returns:
            bool: True if no conflict, False if conflict exists
        """
        conflict = Reservation.query.filter_by(
            court_id=court_id,
            date=date,
            start_time=start_time,
            status='active'
        ).first()
        
        return conflict is None
    
    @staticmethod
    def validate_not_blocked(court_id, date, start_time):
        """
        Validate time slot is not blocked.
        
        Args:
            court_id: ID of the court
            date: date object
            start_time: time object
            
        Returns:
            bool: True if not blocked, False if blocked
        """
        # Check if there's a block covering this time slot
        block = Block.query.filter(
            Block.court_id == court_id,
            Block.date == date,
            Block.start_time <= start_time,
            Block.end_time > start_time
        ).first()
        
        return block is None
    
    @staticmethod
    def validate_all_booking_constraints(court_id, date, start_time, member_id):
        """
        Validate all booking constraints.
        
        Args:
            court_id: ID of the court
            date: date object
            start_time: time object
            member_id: ID of the member making the booking
            
        Returns:
            tuple: (bool, str) - (is_valid, error_message)
        """
        # Validate booking time
        if not ValidationService.validate_booking_time(start_time):
            return False, "Buchungen sind nur zwischen 06:00 und 21:00 Uhr möglich"
        
        # Validate member reservation limit
        if not ValidationService.validate_member_reservation_limit(member_id):
            return False, "Sie haben bereits 2 aktive Buchungen"
        
        # Validate no conflict
        if not ValidationService.validate_no_conflict(court_id, date, start_time):
            return False, "Dieser Platz ist bereits für diese Zeit gebucht"
        
        # Validate not blocked
        if not ValidationService.validate_not_blocked(court_id, date, start_time):
            return False, "Dieser Platz ist für diese Zeit gesperrt"
        
        return True, ""
