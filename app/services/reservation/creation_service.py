"""Service for creating and updating reservations."""
import logging
from datetime import time

from sqlalchemy.orm import joinedload
from app import db
from app.models import Reservation, Court, Member
from app.services.validation_service import ValidationService
from app.services.email_service import EmailService
from app.services.reservation.helpers import ReservationHelpers
from app.utils.timezone_utils import ensure_berlin_timezone, log_timezone_operation
from app.utils.error_handling import (
    log_error_with_context,
    monitor_performance,
    get_system_health_info,
    get_time_based_error_messages
)
from app.constants.messages import ErrorMessages

# Configure logging
logger = logging.getLogger(__name__)


class ReservationCreationService:
    """Service for creating and updating reservations."""

    @staticmethod
    @monitor_performance("create_reservation", threshold_ms=2000)
    def create_reservation(court_id, date, start_time, booked_for_id, booked_by_id, current_time=None, booked_for_member=None):
        """
        Create a new reservation.

        Args:
            court_id: ID of the court
            date: Reservation date
            start_time: Start time
            booked_for_id: ID of member the reservation is for
            booked_by_id: ID of member creating the reservation
            current_time: Current datetime for testing (defaults to now)
            booked_for_member: Optional pre-loaded Member object (booked_for) to avoid redundant query

        Returns:
            tuple: (Reservation object or None, error message or None)
        """
        try:
            # Use provided current_time or default to Berlin time
            berlin_time = ensure_berlin_timezone(current_time)
            log_timezone_operation("create_reservation", current_time, berlin_time)

            # Determine if this is a short notice booking
            is_short_notice = ReservationHelpers.is_short_notice_booking(date, start_time, berlin_time)

            # Log reservation creation
            logger.info(f"Creating reservation - date={date}, start_time={start_time}, is_short_notice={is_short_notice}")

            # Validate all constraints (pass short notice flag and current_time for proper validation)
            # Pass pre-loaded member to avoid redundant query
            is_valid, error_msg = ValidationService.validate_all_booking_constraints(
                court_id, date, start_time, booked_for_id, is_short_notice, berlin_time, member=booked_for_member
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

                # Eager load relationships for email to avoid additional queries
                # Note: Must use filter_by().first() instead of .get() because
                # .get() bypasses query options like joinedload
                reservation = Reservation.query.options(
                    joinedload(Reservation.court),
                    joinedload(Reservation.booked_for),
                    joinedload(Reservation.booked_by)
                ).filter_by(id=reservation.id).first()

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

            # Eager load relationships for email to avoid additional queries
            # Note: Must use filter_by().first() instead of .get() because
            # .get() bypasses query options like joinedload
            reservation = Reservation.query.options(
                joinedload(Reservation.court),
                joinedload(Reservation.booked_for),
                joinedload(Reservation.booked_by)
            ).filter_by(id=reservation_id).first()

            # Send email notifications
            EmailService.send_booking_modified(reservation)

            return reservation, None
        except Exception as e:
            db.session.rollback()
            return None, f"Fehler beim Aktualisieren der Buchung: {str(e)}"
