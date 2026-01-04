"""Validation service for business rules."""
import logging
from datetime import time
from flask import current_app
from app.models import Reservation, Block
from app import db
from app.utils.timezone_utils import ensure_berlin_timezone, log_timezone_operation

# Configure logging
logger = logging.getLogger(__name__)


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
    def validate_member_reservation_limit(member_id, is_short_notice=False, current_time=None):
        """
        Validate member has not exceeded the 2-reservation limit using time-based logic.
        Only counts active booking sessions (future or currently in progress).
        Short notice bookings are excluded from the limit.
        
        Args:
            member_id: ID of the member
            is_short_notice: Whether this is a short notice booking (default False)
            current_time: Current datetime for testing (defaults to Europe/Berlin now)
            
        Returns:
            bool: True if member can make another reservation, False otherwise
        """
        try:
            # Short notice bookings are always allowed regardless of limit
            if is_short_notice:
                return True
            
            # Ensure consistent Europe/Berlin timezone handling
            berlin_time = ensure_berlin_timezone(current_time)
            log_timezone_operation("validate_member_reservation_limit", current_time, berlin_time)
            
            from app.services.reservation_service import ReservationService
            from app.utils.error_handling import handle_time_calculation_error, get_fallback_active_reservations_date_based
            
            max_reservations = current_app.config.get('MAX_ACTIVE_RESERVATIONS', 2)
            
            # Use the enhanced ReservationService to get active booking sessions
            # This uses time-based logic instead of date-only comparison
            active_booking_sessions = ReservationService.get_member_active_booking_sessions(
                member_id, 
                include_short_notice=False,  # Exclude short notice bookings from count
                current_time=berlin_time
            )
            
            active_count = len(active_booking_sessions)
            
            return active_count < max_reservations
            
        except Exception as e:
            # Use enhanced error handling with fallback
            context = {
                'member_id': member_id,
                'is_short_notice': is_short_notice,
                'current_time': current_time
            }
            
            try:
                # Attempt fallback to date-based logic
                logger.warning("validate_member_reservation_limit: Falling back to date-based logic")
                fallback_reservations = get_fallback_active_reservations_date_based(member_id, include_short_notice=False)
                fallback_count = len(fallback_reservations)
                max_reservations = current_app.config.get('MAX_ACTIVE_RESERVATIONS', 2)
                
                logger.info(f"Fallback validation successful: {fallback_count} active reservations")
                return fallback_count < max_reservations
                
            except Exception as fallback_error:
                # Log both errors
                logger.error(f"Primary validation error: {e}")
                logger.error(f"Fallback validation error: {fallback_error}")
                logger.error(f"Context: {context}")
                
                # Ultimate fallback: allow the reservation to be safe (better to allow than block)
                logger.warning("Ultimate fallback: allowing reservation due to validation errors")
                return True
    
    @staticmethod
    def validate_member_short_notice_limit(member_id, current_time=None):
        """
        Validate member has not exceeded the 1 short notice booking limit using time-based logic.
        Only counts active short notice bookings (future or currently in progress).
        
        Args:
            member_id: ID of the member
            current_time: Current datetime for testing (defaults to Europe/Berlin now)
            
        Returns:
            bool: True if member can make another short notice booking, False otherwise
        """
        try:
            # Ensure consistent Europe/Berlin timezone handling
            berlin_time = ensure_berlin_timezone(current_time)
            log_timezone_operation("validate_member_short_notice_limit", current_time, berlin_time)
            
            from app.services.reservation_service import ReservationService
            from app.utils.error_handling import get_fallback_active_reservations_date_based
            
            # Use the enhanced ReservationService to get active short notice bookings
            # This uses time-based logic instead of date-only comparison
            active_short_notice_bookings = ReservationService.get_member_active_short_notice_bookings(
                member_id,
                current_time=berlin_time
            )
            
            active_short_notice_count = len(active_short_notice_bookings)
            
            return active_short_notice_count < 1
            
        except Exception as e:
            # Use enhanced error handling with fallback
            context = {
                'member_id': member_id,
                'current_time': current_time
            }
            
            try:
                # Attempt fallback to date-based logic for short notice bookings
                logger.warning("validate_member_short_notice_limit: Falling back to date-based logic")
                
                from datetime import date as date_class
                from app.models import Reservation
                
                today = date_class.today()
                fallback_short_notice = Reservation.query.filter(
                    (Reservation.booked_for_id == member_id) | (Reservation.booked_by_id == member_id),
                    Reservation.status == 'active',
                    Reservation.is_short_notice == True,
                    Reservation.date >= today
                ).all()
                
                fallback_count = len(fallback_short_notice)
                logger.info(f"Fallback short notice validation successful: {fallback_count} active short notice bookings")
                return fallback_count < 1
                
            except Exception as fallback_error:
                # Log both errors
                logger.error(f"Primary short notice validation error: {e}")
                logger.error(f"Fallback short notice validation error: {fallback_error}")
                logger.error(f"Context: {context}")
                
                # Ultimate fallback: allow the booking to be safe
                logger.warning("Ultimate fallback: allowing short notice booking due to validation errors")
                return True
    
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
    def validate_no_conflict_with_time_logic(court_id, date, start_time, current_time=None):
        """
        Validate no conflicting active reservations exist using time-based logic.
        
        Args:
            court_id: ID of the court
            date: date object
            start_time: time object
            current_time: Current datetime (defaults to now)
            
        Returns:
            bool: True if no conflict, False if conflict exists
        """
        if current_time is None:
            from app.utils.timezone_utils import get_current_berlin_time
            current_time = get_current_berlin_time()
        
        conflict = Reservation.query.filter_by(
            court_id=court_id,
            date=date,
            start_time=start_time,
            status='active'
        ).first()
        
        if conflict:
            # Use time-based logic to determine if the conflicting reservation is still active
            from app.services.reservation_service import ReservationService
            return not ReservationService.is_reservation_currently_active(conflict, current_time)
        
        return True  # No conflicting reservation found
    
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
    def validate_all_booking_constraints(court_id, date, start_time, member_id, is_short_notice=False, current_time=None):
        """
        Validate all booking constraints.
        
        Args:
            court_id: ID of the court
            date: date object
            start_time: time object
            member_id: ID of the member making the booking
            is_short_notice: Whether this is a short notice booking (default False)
            current_time: Current datetime for testing (defaults to Europe/Berlin now)
            
        Returns:
            tuple: (bool, str) - (is_valid, error_message)
        """
        try:
            from datetime import datetime, timedelta
            from app.utils.error_handling import get_time_based_error_messages, log_error_with_context
            
            # Get updated error messages
            error_messages = get_time_based_error_messages()
            
            # Ensure consistent Europe/Berlin timezone handling
            berlin_time = ensure_berlin_timezone(current_time)
            log_timezone_operation("validate_all_booking_constraints", current_time, berlin_time)
            
            # Validate not in the past (with special handling for short notice bookings)
            booking_datetime = datetime.combine(date, start_time)
            
            # Validate not in the past (with special handling for short notice bookings)
            if is_short_notice:
                # For short notice bookings, allow as long as the slot hasn't ended yet
                # (booking end time = start time + 1 hour)
                booking_end_datetime = datetime.combine(date, time(start_time.hour + 1, start_time.minute))
                if berlin_time >= booking_end_datetime:
                    return False, error_messages['BOOKING_PAST_ENDED']
            else:
                # For regular bookings, don't allow past bookings
                if booking_datetime < berlin_time:
                    return False, error_messages['BOOKING_PAST_REGULAR']
            
            # Validate booking time
            if not ValidationService.validate_booking_time(start_time):
                return False, "Buchungen sind nur zu vollen Stunden zwischen 08:00 und 22:00 Uhr möglich"
            
            # Validate member reservation limit (short notice bookings are exempt)
            # Pass berlin_time for time-based validation
            if not ValidationService.validate_member_reservation_limit(member_id, is_short_notice, berlin_time):
                return False, error_messages['RESERVATION_LIMIT_REGULAR']
            
            # Validate short notice booking limit (only for short notice bookings)
            # Pass berlin_time for time-based validation
            if is_short_notice and not ValidationService.validate_member_short_notice_limit(member_id, berlin_time):
                return False, error_messages['RESERVATION_LIMIT_SHORT_NOTICE']
            
            # Validate no conflict using time-based logic
            if not ValidationService.validate_no_conflict_with_time_logic(court_id, date, start_time, berlin_time):
                return False, "Dieser Platz ist bereits für diese Zeit gebucht"
            
            # Validate not blocked
            if not ValidationService.validate_not_blocked(court_id, date, start_time):
                return False, "Dieser Platz ist für diese Zeit gesperrt"
            
            return True, ""
            
        except Exception as e:
            # Enhanced error handling with comprehensive logging
            context = {
                'court_id': court_id,
                'date': date,
                'start_time': start_time,
                'member_id': member_id,
                'is_short_notice': is_short_notice,
                'current_time': current_time
            }
            log_error_with_context(e, context, "validate_all_booking_constraints")
            
            # Try to provide a more specific error message
            error_messages = get_time_based_error_messages()
            return False, error_messages['TIME_CALCULATION_ERROR']
    
    @staticmethod
    def validate_cancellation_allowed(reservation_id, current_time=None):
        """
        Validate if a reservation can be cancelled.
        Reservations cannot be cancelled within 15 minutes of start time or once started.
        Short notice bookings can never be cancelled.
        
        Args:
            reservation_id: ID of the reservation
            current_time: Current datetime (defaults to Europe/Berlin now)
            
        Returns:
            tuple: (bool, str) - (is_allowed, error_message)
        """
        try:
            from datetime import datetime, timedelta
            from app.utils.error_handling import get_time_based_error_messages, log_error_with_context
            
            # Get updated error messages
            error_messages = get_time_based_error_messages()
            
            # Ensure consistent Europe/Berlin timezone handling
            berlin_time = ensure_berlin_timezone(current_time)
            log_timezone_operation("validate_cancellation_allowed", current_time, berlin_time)
            
            reservation = Reservation.query.get(reservation_id)
            if not reservation:
                return False, "Buchung nicht gefunden"
            
            # Short notice bookings can never be cancelled
            if reservation.is_short_notice:
                return False, error_messages['SHORT_NOTICE_NO_CANCEL']
            
            reservation_datetime = datetime.combine(reservation.date, reservation.start_time)
            time_until_start = reservation_datetime - berlin_time
            
            # If reservation has already started
            if time_until_start <= timedelta(0):
                return False, error_messages['CANCELLATION_STARTED']
            
            # If reservation starts in less than 15 minutes
            if time_until_start < timedelta(minutes=15):
                return False, error_messages['CANCELLATION_TOO_LATE']
            
            return True, ""
            
        except Exception as e:
            # Enhanced error handling with comprehensive logging
            context = {
                'reservation_id': reservation_id,
                'current_time': current_time
            }
            log_error_with_context(e, context, "validate_cancellation_allowed")
            
            # Try to provide a more specific error message
            error_messages = get_time_based_error_messages()
            return False, error_messages['TIME_CALCULATION_ERROR']
