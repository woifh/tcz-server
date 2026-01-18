"""Service for cancelling reservations."""
import logging

from app import db
from app.models import Reservation
from app.services.validation_service import ValidationService
from app.services.email_service import EmailService

# Configure logging
logger = logging.getLogger(__name__)


class ReservationCancellationService:
    """Service for cancelling reservations."""

    @staticmethod
    def cancel_reservation(reservation_id, reason=None, cancelled_by_id=None):
        """
        Cancel a reservation.
        Uses enhanced validation that prevents cancellation within 15 minutes of start time,
        once the slot has started, or for short notice bookings.

        Args:
            reservation_id: ID of the reservation
            reason: Optional cancellation reason
            cancelled_by_id: ID of member cancelling the reservation (for audit trail)

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

            # Log audit trail
            from app.services.reservation import ReservationService
            cancelled_for_someone_else = bool(cancelled_by_id and cancelled_by_id != reservation.booked_for_id)
            ReservationService.log_reservation_operation(
                operation='cancel',
                reservation_id=reservation.id,
                operation_data={
                    'court_id': reservation.court_id,
                    'date': str(reservation.date),
                    'start_time': str(reservation.start_time),
                    'reason': reason,
                    'booked_for_id': reservation.booked_for_id,
                    'cancelled_by_id': cancelled_by_id or reservation.booked_for_id,
                    'cancelled_by_admin': cancelled_for_someone_else,
                    'is_admin_action': cancelled_for_someone_else
                },
                performed_by_id=cancelled_by_id or reservation.booked_for_id
            )

            return True, None
        except Exception as e:
            db.session.rollback()
            return False, f"Fehler beim Stornieren der Buchung: {str(e)}"
