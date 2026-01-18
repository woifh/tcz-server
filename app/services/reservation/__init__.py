"""
Reservation service package.

This package splits the original ReservationService into focused sub-services:
- helpers: Classification and time-based logic helpers
- query_service: All retrieval and query operations
- creation_service: Creating and updating reservations
- cancellation_service: Cancelling reservations

For backward compatibility, we export a unified ReservationService class that
delegates to the appropriate sub-service.
"""

from app.services.reservation.helpers import ReservationHelpers
from app.services.reservation.query_service import ReservationQueryService
from app.services.reservation.creation_service import ReservationCreationService
from app.services.reservation.cancellation_service import ReservationCancellationService

import logging

logger = logging.getLogger(__name__)


class ReservationService:
    """
    Unified reservation service for backward compatibility.

    This class delegates to the specialized sub-services while maintaining
    the same API as the original monolithic ReservationService.
    """

    # ============================================================================
    # Helper Methods (delegates to ReservationHelpers)
    # ============================================================================

    @staticmethod
    def is_reservation_active_by_time(reservation_date, reservation_end_time, current_time=None):
        """Determine if a reservation is active based on current time."""
        return ReservationHelpers.is_reservation_active_by_time(
            reservation_date, reservation_end_time, current_time
        )

    @staticmethod
    def is_reservation_currently_active(reservation, current_time=None):
        """Check if a reservation object is currently active based on time."""
        return ReservationHelpers.is_reservation_currently_active(reservation, current_time)

    @staticmethod
    def is_short_notice_booking(date, start_time, current_time=None):
        """Check if a booking would be classified as short notice."""
        return ReservationHelpers.is_short_notice_booking(date, start_time, current_time)

    @staticmethod
    def classify_booking_type(date, start_time, current_time=None):
        """Classify a booking as regular or short notice."""
        return ReservationHelpers.classify_booking_type(date, start_time, current_time)

    # ============================================================================
    # Query Methods (delegates to ReservationQueryService)
    # ============================================================================

    @staticmethod
    def get_member_active_reservations(member_id, include_short_notice=True, current_time=None):
        """Get active reservations for a member using time-based logic."""
        return ReservationQueryService.get_member_active_reservations(
            member_id, include_short_notice, current_time
        )

    @staticmethod
    def get_member_active_booking_sessions(member_id, include_short_notice=False, current_time=None,
                                           include_bookings_for_others=False):
        """Get active booking sessions for a member (for limit enforcement or display)."""
        return ReservationQueryService.get_member_active_booking_sessions(
            member_id, include_short_notice, current_time, include_bookings_for_others
        )

    @staticmethod
    def get_member_active_short_notice_bookings(member_id, current_time=None):
        """Get active short notice bookings for a member."""
        return ReservationQueryService.get_member_active_short_notice_bookings(
            member_id, current_time
        )

    @staticmethod
    def get_member_regular_reservations(member_id):
        """Get active regular reservations for a member (excludes short notice)."""
        return ReservationQueryService.get_member_regular_reservations(member_id)

    @staticmethod
    def check_availability(court_id, date, start_time, current_time=None):
        """Check if a court is available at a specific time."""
        return ReservationQueryService.check_availability(
            court_id, date, start_time, current_time
        )

    @staticmethod
    def get_reservations_by_date(date):
        """Get all reservations for a specific date."""
        return ReservationQueryService.get_reservations_by_date(date)

    # ============================================================================
    # Creation/Update Methods (delegates to ReservationCreationService)
    # ============================================================================

    @staticmethod
    def create_reservation(court_id, date, start_time, booked_for_id, booked_by_id, current_time=None, booked_for_member=None):
        """Create a new reservation."""
        return ReservationCreationService.create_reservation(
            court_id, date, start_time, booked_for_id, booked_by_id, current_time, booked_for_member
        )

    @staticmethod
    def update_reservation(reservation_id, **updates):
        """Update an existing reservation."""
        return ReservationCreationService.update_reservation(reservation_id, **updates)

    # ============================================================================
    # Cancellation Methods (delegates to ReservationCancellationService)
    # ============================================================================

    @staticmethod
    def cancel_reservation(reservation_id, reason=None, cancelled_by_id=None):
        """Cancel a reservation."""
        return ReservationCancellationService.cancel_reservation(reservation_id, reason, cancelled_by_id)

    # ============================================================================
    # Audit Logging
    # ============================================================================

    @staticmethod
    def log_reservation_operation(operation, reservation_id, operation_data, performed_by_id=None):
        """
        Log a reservation operation for audit purposes.

        Args:
            operation: Type of operation ('create', 'cancel')
            reservation_id: ID of the reservation being operated on
            operation_data: Dictionary containing operation details
            performed_by_id: ID of user performing the operation
        """
        from app import db
        from app.models import ReservationAuditLog, Member
        from app.utils.serializers import serialize_for_json

        try:
            if operation_data is None:
                operation_data = {}

            if performed_by_id:
                performer = Member.query.get(performed_by_id)
                if performer:
                    operation_data['performer_role'] = performer.role
                    # Only mark as admin action if performer has elevated role
                    if 'is_admin_action' in operation_data:
                        is_elevated_user = performer.role in ['administrator', 'teamster']
                        operation_data['is_admin_action'] = operation_data['is_admin_action'] and is_elevated_user

            safe_data = serialize_for_json(operation_data) if operation_data else None

            audit_log = ReservationAuditLog(
                reservation_id=str(reservation_id) if reservation_id else None,
                operation=operation,
                operation_data=safe_data,
                performed_by_id=performed_by_id
            )

            db.session.add(audit_log)
            db.session.commit()

            logger.info(f"Reservation operation logged: {operation} on reservation {reservation_id} by {performed_by_id or 'system'}")

        except Exception as e:
            logger.error(f"Failed to log reservation operation: {str(e)}")
            # Don't fail the main operation if logging fails


# Export all services for direct use
__all__ = [
    'ReservationService',  # Unified interface (backward compatible)
    'ReservationHelpers',
    'ReservationQueryService',
    'ReservationCreationService',
    'ReservationCancellationService'
]
