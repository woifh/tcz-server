"""Query service for retrieving reservation data."""
import logging
from datetime import date as date_class

from app import db
from app.models import Reservation
from app.services.validation_service import ValidationService
from app.services.reservation.helpers import ReservationHelpers
from app.utils.timezone_utils import ensure_berlin_timezone, log_timezone_operation
from app.utils.error_handling import (
    log_error_with_context,
    monitor_performance
)
from app.utils.query_helpers import build_active_reservation_time_filter

# Configure logging
logger = logging.getLogger(__name__)


class ReservationQueryService:
    """Service for querying and retrieving reservation data."""

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
                Reservation.booked_for_id == member_id,
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
                today = date_class.today()

                query = Reservation.query.filter(
                    Reservation.booked_for_id == member_id,
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
        return ReservationQueryService._get_member_active_reservations_base(
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
            sessions = ReservationQueryService.get_member_active_booking_sessions(member_id)

            # Get all active booking sessions including short notice
            all_sessions = ReservationQueryService.get_member_active_booking_sessions(
                member_id, include_short_notice=True
            )

            # Get active booking sessions at a specific time (for testing)
            test_time = datetime(2024, 1, 15, 14, 30)
            sessions = ReservationQueryService.get_member_active_booking_sessions(
                member_id, current_time=test_time
            )
        """
        return ReservationQueryService._get_member_active_reservations_base(
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
            short_notice = ReservationQueryService.get_member_active_short_notice_bookings(member_id)

            # Get active short notice bookings at a specific time (for testing)
            test_time = datetime(2024, 1, 15, 14, 30)
            short_notice = ReservationQueryService.get_member_active_short_notice_bookings(
                member_id, current_time=test_time
            )
        """
        return ReservationQueryService._get_member_active_reservations_base(
            member_id=member_id,
            short_notice_only=True,
            current_time=current_time,
            operation_name="get_member_active_short_notice_bookings"
        )

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
        today = date_class.today()

        return Reservation.query.filter(
            Reservation.booked_for_id == member_id,
            Reservation.status == 'active',
            Reservation.date >= today,
            Reservation.is_short_notice == False
        ).order_by(Reservation.date, Reservation.start_time).all()

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
            is_still_active = ReservationHelpers.is_reservation_currently_active(
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
