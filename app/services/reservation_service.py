"""Reservation service for business logic."""
import logging
from datetime import time, timedelta, datetime, timezone
from sqlalchemy import or_, and_
from app import db
from app.models import Reservation
from app.services.validation_service import ValidationService
from app.services.email_service import EmailService
from app.utils.timezone_utils import ensure_berlin_timezone, log_timezone_operation
from app.utils.error_handling import (
    safe_time_operation,
    log_error_with_context,
    get_fallback_active_reservations_date_based,
    monitor_performance,
    ActiveBookingSessionError
)
from app.utils.query_helpers import build_active_reservation_time_filter
from app.constants.messages import ErrorMessages

# Configure logging
logger = logging.getLogger(__name__)


class ReservationService:
    """Service for managing reservations."""
    
    @staticmethod
    @monitor_performance("is_reservation_active_by_time", threshold_ms=100)
    def is_reservation_active_by_time(reservation_date, reservation_end_time, current_time=None):
        """
        Determine if a reservation is active based on current time.
        
        A reservation is considered active if:
        - It's on a future date, OR
        - It's on the same date but hasn't ended yet (end_time > current_time)
        
        This implements the core time-based logic for active booking sessions,
        replacing the previous date-only approach.
        
        Args:
            reservation_date: Date of the reservation (date object)
            reservation_end_time: End time of the reservation (time object)
            current_time: Current datetime (defaults to Europe/Berlin timezone)
            
        Returns:
            bool: True if reservation is active (future or in progress)
        """
        try:
            # Ensure consistent Europe/Berlin timezone handling
            berlin_time = ensure_berlin_timezone(current_time)
            log_timezone_operation("is_reservation_active_by_time", current_time, berlin_time)
            
            current_date = berlin_time.date()
            current_time_only = berlin_time.time()
            
            # Future reservation (date > current_date): Always active
            if reservation_date > current_date:
                return True
            
            # Past reservation (date < current_date): Never active
            elif reservation_date < current_date:
                return False
            
            # Same day reservation: Active if end_time > current_time
            else:  # reservation_date == current_date
                # Handle edge case: if current time exactly matches end time, reservation is NOT active
                return reservation_end_time > current_time_only
                
        except Exception as e:
            context = {
                'reservation_date': reservation_date,
                'reservation_end_time': reservation_end_time,
                'current_time': current_time
            }
            log_error_with_context(e, context, "is_reservation_active_by_time")
            
            # Fallback to date-based logic if time calculations fail
            try:
                logger.warning("Falling back to date-based logic for is_reservation_active_by_time")
                fallback_time = ensure_berlin_timezone(None)  # Get current Berlin time
                return reservation_date >= fallback_time.date()
            except Exception as fallback_error:
                log_error_with_context(fallback_error, context, "is_reservation_active_by_time_fallback")
                # Ultimate fallback: assume reservation is active to be safe
                logger.error("Ultimate fallback: assuming reservation is active")
                return True
    
    @staticmethod
    def is_reservation_currently_active(reservation, current_time=None):
        """
        Check if a reservation object is currently active based on time.
        
        This is a convenience wrapper around is_reservation_active_by_time()
        that works directly with Reservation model objects.
        
        Args:
            reservation: Reservation object
            current_time: Current datetime (defaults to Europe/Berlin now)
            
        Returns:
            bool: True if reservation is active (future or in progress)
        """
        return ReservationService.is_reservation_active_by_time(
            reservation.date,
            reservation.end_time,
            current_time
        )
    
    @staticmethod
    def is_short_notice_booking(date, start_time, current_time=None):
        """
        Check if a booking would be classified as short notice.

        A booking is short notice if:
        - Current time is within the booking slot (ongoing), OR
        - Current time is within 15 minutes before the slot start

        Args:
            date: Reservation date (assumed to be in Europe/Berlin timezone)
            start_time: Reservation start time (assumed to be in Europe/Berlin timezone)
            current_time: Current datetime (defaults to Europe/Berlin now)

        Returns:
            bool: True if booking is short notice (ongoing or within 15 minutes of start)
        """
        try:
            # Ensure consistent Europe/Berlin timezone handling
            berlin_time = ensure_berlin_timezone(current_time)
            log_timezone_operation("is_short_notice_booking", current_time, berlin_time)

            # Ensure we're comparing like with like - both should be naive datetimes
            # representing the same timezone (Europe/Berlin)
            reservation_start = datetime.combine(date, start_time)

            # Calculate end time (slots are 1 hour long)
            end_hour = start_time.hour + 1
            end_time = time(end_hour if end_hour < 24 else 0, start_time.minute)
            reservation_end = datetime.combine(date, end_time)
            # Handle midnight crossing
            if end_hour >= 24:
                reservation_end = reservation_end + timedelta(days=1)

            time_until_start = reservation_start - berlin_time
            time_until_end = reservation_end - berlin_time

            # Debug logging
            logger.debug(f"Short Notice Check:")
            logger.debug(f"  Reservation start: {reservation_start}")
            logger.debug(f"  Reservation end: {reservation_end}")
            logger.debug(f"  Current time (Berlin): {berlin_time}")
            logger.debug(f"  Time until start: {time_until_start}")
            logger.debug(f"  Time until end: {time_until_end}")

            # If the slot has already ended, it's not short notice (it's invalid/past)
            if time_until_end < timedelta(0):
                logger.debug(f"  Slot has ended, not short notice")
                return False

            # If we're currently within the slot (ongoing), it's short notice
            if time_until_start < timedelta(0) and time_until_end > timedelta(0):
                logger.debug(f"  Currently within the slot (ongoing), IS short notice")
                return True

            # If slot starts within 15 minutes or less, it's short notice
            is_short_notice = time_until_start <= timedelta(minutes=15)
            logger.debug(f"  Within 15 minutes of start: {is_short_notice}")

            return is_short_notice

        except Exception as e:
            logger.error(f"Error in is_short_notice_booking: {e}")
            # Fallback: assume not short notice to be safe
            return False
    
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
    @monitor_performance("create_reservation", threshold_ms=2000)
    def create_reservation(court_id, date, start_time, booked_for_id, booked_by_id, current_time=None):
        """
        Create a new reservation.
        
        Args:
            court_id: ID of the court
            date: Reservation date
            start_time: Start time
            booked_for_id: ID of member the reservation is for
            booked_by_id: ID of member creating the reservation
            current_time: Current datetime for testing (defaults to now)
            
        Returns:
            tuple: (Reservation object or None, error message or None)
        """
        try:
            # Use provided current_time or default to Berlin time
            berlin_time = ensure_berlin_timezone(current_time)
            log_timezone_operation("create_reservation", current_time, berlin_time)
            
            # Determine if this is a short notice booking
            is_short_notice = ReservationService.is_short_notice_booking(date, start_time, berlin_time)
            
            # Log reservation creation
            logger.info(f"Creating reservation - date={date}, start_time={start_time}, is_short_notice={is_short_notice}")
            
            # Validate all constraints (pass short notice flag and current_time for proper validation)
            is_valid, error_msg = ValidationService.validate_all_booking_constraints(
                court_id, date, start_time, booked_for_id, is_short_notice, berlin_time
            )
            
            if not is_valid:
                logger.warning(f"Reservation validation failed: {error_msg}")
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
                
                logger.info(f"Reservation created successfully: ID={reservation.id}")
                
                # Send email notifications (don't fail if email fails)
                try:
                    EmailService.send_booking_created(reservation)
                except Exception as email_error:
                    logger.warning(f"Email notification failed: {email_error}")
                    # Don't fail the reservation creation if email fails
                
                return reservation, None
                
            except Exception as db_error:
                db.session.rollback()
                logger.error(f"Database error creating reservation: {db_error}")
                
                # Check if it's a duplicate booking error
                if 'Duplicate entry' in str(db_error) and 'unique_booking' in str(db_error):
                    return None, ErrorMessages.RESERVATION_ALREADY_BOOKED
                return None, f"Fehler beim Erstellen der Buchung: {str(db_error)}"
                
        except Exception as e:
            # Enhanced error handling with comprehensive logging
            context = {
                'court_id': court_id,
                'date': date,
                'start_time': start_time,
                'booked_for_id': booked_for_id,
                'booked_by_id': booked_by_id,
                'current_time': current_time
            }
            log_error_with_context(e, context, "create_reservation")
            
            # Get system health info for debugging
            from app.utils.error_handling import get_system_health_info, get_time_based_error_messages
            health_info = get_system_health_info()
            logger.error(f"System health during reservation creation error: {health_info}")
            
            # Return user-friendly error message
            error_messages = get_time_based_error_messages()
            return None, error_messages.get('TIME_CALCULATION_ERROR', "Ein unerwarteter Fehler ist beim Erstellen der Buchung aufgetreten. Bitte versuchen Sie es erneut.")
    
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
            return None, ErrorMessages.RESERVATION_NOT_FOUND
        
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
    def _get_member_active_reservations_base(member_id, include_short_notice=None,
                                             short_notice_only=False, current_time=None,
                                             operation_name="get_member_active_reservations"):
        """
        Internal base method to get active reservations with flexible filtering.

        This consolidates the logic used by multiple public methods to avoid duplication.

        Args:
            member_id: ID of the member
            include_short_notice: Include short notice bookings (True), exclude them (False),
                                 or don't filter by this (None)
            short_notice_only: Only return short notice bookings (default False)
            current_time: Current datetime for testing (defaults to Europe/Berlin now)
            operation_name: Name for logging purposes

        Returns:
            list: List of active Reservation objects
        """
        try:
            # Ensure consistent Europe/Berlin timezone handling
            berlin_time = ensure_berlin_timezone(current_time)
            log_timezone_operation(operation_name, current_time, berlin_time)

            current_date = berlin_time.date()
            current_time_only = berlin_time.time()

            # Build time-based filter using shared utility
            time_filter = build_active_reservation_time_filter(
                current_date, current_time_only, Reservation
            )

            query = Reservation.query.filter(
                (Reservation.booked_for_id == member_id) | (Reservation.booked_by_id == member_id),
                Reservation.status == 'active',
                time_filter
            )

            # Apply short notice filtering
            if short_notice_only:
                query = query.filter(Reservation.is_short_notice == True)
            elif include_short_notice is False:
                query = query.filter(Reservation.is_short_notice == False)
            # If include_short_notice is True or None, don't filter

            return query.order_by(Reservation.date, Reservation.start_time).all()

        except Exception as e:
            # Enhanced error handling with comprehensive logging
            context = {
                'member_id': member_id,
                'include_short_notice': include_short_notice,
                'short_notice_only': short_notice_only,
                'current_time': current_time
            }
            log_error_with_context(e, context, operation_name)

            # Fallback to date-based logic
            try:
                logger.warning(f"{operation_name}: Falling back to date-based logic")
                from datetime import date as date_class
                today = date_class.today()

                query = Reservation.query.filter(
                    (Reservation.booked_for_id == member_id) | (Reservation.booked_by_id == member_id),
                    Reservation.status == 'active',
                    Reservation.date >= today
                )

                # Apply short notice filtering
                if short_notice_only:
                    query = query.filter(Reservation.is_short_notice == True)
                elif include_short_notice is False:
                    query = query.filter(Reservation.is_short_notice == False)

                result = query.order_by(Reservation.date, Reservation.start_time).all()
                logger.info(f"Fallback successful: returned {len(result)} reservations")
                return result

            except Exception as fallback_error:
                log_error_with_context(fallback_error, context, f"{operation_name}_fallback")
                logger.error("All fallback methods failed, returning empty list")
                return []

    @staticmethod
    def get_member_active_reservations(member_id, include_short_notice=True, current_time=None):
        """
        Get active reservations for a member using time-based logic.
        Returns reservations that are either in the future or currently in progress.

        Args:
            member_id: ID of the member
            include_short_notice: Whether to include short notice bookings (default True)
            current_time: Current datetime for testing (defaults to Europe/Berlin now)

        Returns:
            list: List of active Reservation objects
        """
        return ReservationService._get_member_active_reservations_base(
            member_id=member_id,
            include_short_notice=include_short_notice,
            current_time=current_time,
            operation_name="get_member_active_reservations"
        )
    
    @staticmethod
    @monitor_performance("get_member_active_booking_sessions", threshold_ms=500)
    def get_member_active_booking_sessions(member_id, include_short_notice=False, current_time=None):
        """
        Get active booking sessions for a member using time-based logic.

        This method specifically implements the "active booking session" concept for
        reservation limit enforcement. By default, it excludes short notice bookings
        since they don't count toward the 2-reservation limit.

        An active booking session is a reservation that:
        - Has status='active' AND
        - Is either in the future or currently in progress (hasn't ended yet) AND
        - Optionally excludes short notice bookings (default behavior)

        Args:
            member_id: ID of the member
            include_short_notice: Whether to include short notice bookings (default False)
            current_time: Current datetime for testing (defaults to Europe/Berlin now)

        Returns:
            list: List of active booking session Reservation objects

        Examples:
            # Get regular active booking sessions (for 2-reservation limit)
            sessions = ReservationService.get_member_active_booking_sessions(member_id)

            # Get all active booking sessions including short notice
            all_sessions = ReservationService.get_member_active_booking_sessions(
                member_id, include_short_notice=True
            )

            # Get active booking sessions at a specific time (for testing)
            test_time = datetime(2024, 1, 15, 14, 30)
            sessions = ReservationService.get_member_active_booking_sessions(
                member_id, current_time=test_time
            )
        """
        return ReservationService._get_member_active_reservations_base(
            member_id=member_id,
            include_short_notice=include_short_notice,
            current_time=current_time,
            operation_name="get_member_active_booking_sessions"
        )
    
    @staticmethod
    def get_member_active_short_notice_bookings(member_id, current_time=None):
        """
        Get active short notice bookings for a member using time-based logic.

        This method specifically gets short notice bookings that are currently active
        (future or in progress) for the purpose of enforcing the 1 short notice booking limit.

        Uses the same time-based logic as regular reservations:
        - Future reservations (date > current_date): Active
        - Same-day reservations: Active if end_time > current_time
        - Past reservations: Not active

        Args:
            member_id: ID of the member
            current_time: Current datetime for testing (defaults to Europe/Berlin now)

        Returns:
            list: List of active short notice Reservation objects

        Examples:
            # Get active short notice bookings (for 1-booking limit enforcement)
            short_notice = ReservationService.get_member_active_short_notice_bookings(member_id)

            # Get active short notice bookings at a specific time (for testing)
            test_time = datetime(2024, 1, 15, 14, 30)
            short_notice = ReservationService.get_member_active_short_notice_bookings(
                member_id, current_time=test_time
            )
        """
        return ReservationService._get_member_active_reservations_base(
            member_id=member_id,
            short_notice_only=True,
            current_time=current_time,
            operation_name="get_member_active_short_notice_bookings"
        )
    
    @staticmethod
    def check_availability(court_id, date, start_time, current_time=None):
        """
        Check if a court is available using time-based active booking session logic.
        
        Args:
            court_id: ID of the court
            date: Date to check
            start_time: Time to check
            current_time: Current datetime (defaults to now)
            
        Returns:
            bool: True if available, False otherwise
        """
        if current_time is None:
            from app.utils.timezone_utils import get_current_berlin_time
            current_time = get_current_berlin_time()
        
        # Check if not blocked (this doesn't need time-based logic)
        if not ValidationService.validate_not_blocked(court_id, date, start_time):
            return False
        
        # Check for conflicting reservations using time-based logic
        conflicting_reservation = Reservation.query.filter_by(
            court_id=court_id,
            date=date,
            start_time=start_time,
            status='active'
        ).first()
        
        if conflicting_reservation:
            # Use time-based logic to determine if the conflicting reservation is still active
            is_still_active = ReservationService.is_reservation_currently_active(
                conflicting_reservation, current_time
            )
            return not is_still_active  # Available if the conflicting reservation is no longer active
        
        return True  # No conflicting reservation found
    
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
