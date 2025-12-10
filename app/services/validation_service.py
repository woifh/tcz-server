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
        Validate booking time is within allowed hours (06:00-20:00) and on full hours.
        
        Args:
            start_time: time object representing the start time
            
        Returns:
            bool: True if valid, False otherwise
        """
        booking_start = current_app.config.get('BOOKING_START_HOUR', 6)
        booking_end = current_app.config.get('BOOKING_END_HOUR', 21)
        
        # Start time must be on full hours (minutes must be 00)
        if start_time.minute != 0 or start_time.second != 0:
            return False
        
        # Start time must be between 06:00 and 20:00 (last slot starts at 20:00)
        min_time = time(booking_start, 0)
        max_time = time(booking_end - 1, 0)
        
        return min_time <= start_time <= max_time
    
    @staticmethod
    def validate_member_reservation_limit(member_id, is_short_notice=False):
        """
        Validate member has not exceeded the 2-reservation limit.
        Only counts future regular reservations (today or later).
        Short notice bookings are excluded from the limit.
        
        Args:
            member_id: ID of the member
            is_short_notice: Whether this is a short notice booking (default False)
            
        Returns:
            bool: True if member can make another reservation, False otherwise
        """
        # Short notice bookings are always allowed regardless of limit
        if is_short_notice:
            return True
        
        from datetime import date as date_class
        
        max_reservations = current_app.config.get('MAX_ACTIVE_RESERVATIONS', 2)
        today = date_class.today()
        
        # Count active regular reservations where member is booked_for and date is today or in the future
        # Exclude short notice bookings from the count
        active_count = Reservation.query.filter(
            Reservation.booked_for_id == member_id,
            Reservation.status == 'active',
            Reservation.date >= today,
            Reservation.is_short_notice == False
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
    def validate_all_booking_constraints(court_id, date, start_time, member_id, is_short_notice=False):
        """
        Validate all booking constraints.
        
        Args:
            court_id: ID of the court
            date: date object
            start_time: time object
            member_id: ID of the member making the booking
            is_short_notice: Whether this is a short notice booking (default False)
            
        Returns:
            tuple: (bool, str) - (is_valid, error_message)
        """
        from datetime import datetime, timedelta
        
        # Validate not in the past (with special handling for short notice bookings)
        booking_datetime = datetime.combine(date, start_time)
        now = datetime.now()
        
        # Validate not in the past (with special handling for short notice bookings)
        if is_short_notice:
            # For short notice bookings, allow as long as the slot hasn't ended yet
            # (booking end time = start time + 1 hour)
            booking_end_datetime = datetime.combine(date, time(start_time.hour + 1, start_time.minute))
            if now >= booking_end_datetime:
                return False, "Kurzfristige Buchungen sind nur möglich, solange die Spielzeit noch nicht beendet ist"
        else:
            # For regular bookings, don't allow past bookings
            if booking_datetime < now:
                return False, "Buchungen in der Vergangenheit sind nicht möglich"
        
        # Validate booking time
        if not ValidationService.validate_booking_time(start_time):
            return False, "Buchungen sind nur zu vollen Stunden zwischen 06:00 und 21:00 Uhr möglich"
        
        # Validate member reservation limit (short notice bookings are exempt)
        if not ValidationService.validate_member_reservation_limit(member_id, is_short_notice):
            return False, "Sie haben bereits 2 aktive reguläre Buchungen"
        
        # Validate no conflict
        if not ValidationService.validate_no_conflict(court_id, date, start_time):
            return False, "Dieser Platz ist bereits für diese Zeit gebucht"
        
        # Validate not blocked
        if not ValidationService.validate_not_blocked(court_id, date, start_time):
            return False, "Dieser Platz ist für diese Zeit gesperrt"
        
        return True, ""
    
    @staticmethod
    def validate_cancellation_allowed(reservation_id, current_time=None):
        """
        Validate if a reservation can be cancelled.
        Reservations cannot be cancelled within 15 minutes of start time or once started.
        Short notice bookings can never be cancelled.
        
        Args:
            reservation_id: ID of the reservation
            current_time: Current datetime (defaults to now)
            
        Returns:
            tuple: (bool, str) - (is_allowed, error_message)
        """
        from datetime import datetime, timedelta
        
        if current_time is None:
            current_time = datetime.now()
        
        reservation = Reservation.query.get(reservation_id)
        if not reservation:
            return False, "Buchung nicht gefunden"
        
        # Short notice bookings can never be cancelled
        if reservation.is_short_notice:
            return False, "Kurzfristige Buchungen können nicht storniert werden"
        
        reservation_datetime = datetime.combine(reservation.date, reservation.start_time)
        time_until_start = reservation_datetime - current_time
        
        # If reservation has already started
        if time_until_start <= timedelta(0):
            return False, "Diese Buchung kann nicht mehr storniert werden (Spielzeit bereits begonnen)"
        
        # If reservation starts in less than 15 minutes
        if time_until_start < timedelta(minutes=15):
            return False, "Diese Buchung kann nicht mehr storniert werden (weniger als 15 Minuten bis Spielbeginn)"
        
        return True, ""
