"""Email service for sending notifications."""
import threading
from flask import current_app, copy_current_request_context
from flask_mail import Message
from app import mail
import logging

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending email notifications in German."""
    
    # German email templates (informal "du" style for club members)
    TEMPLATES = {
        'booking_created': {
            'subject': 'Buchungsbestätigung - Tennisplatz {court_number}',
            'body': '''Hallo {recipient_name},

deine Buchung wurde erstellt:

Platz: {court_number}
Datum: {date}
Uhrzeit: {start_time} - {end_time}
Gebucht für: {booked_for_name}
Gebucht von: {booked_by_name}

Viele Grüße
Dein TCZ-Team'''
        },
        'booking_modified': {
            'subject': 'Buchungsänderung - Tennisplatz {court_number}',
            'body': '''Hallo {recipient_name},

deine Buchung wurde geändert:

Platz: {court_number}
Datum: {date}
Uhrzeit: {start_time} - {end_time}
Gebucht für: {booked_for_name}
Gebucht von: {booked_by_name}

Viele Grüße
Dein TCZ-Team'''
        },
        'booking_cancelled': {
            'subject': 'Buchungsstornierung - Tennisplatz {court_number}',
            'body': '''Hallo {recipient_name},

deine Buchung wurde storniert:

Platz: {court_number}
Datum: {date}
Uhrzeit: {start_time} - {end_time}
{reason_text}

Viele Grüße
Dein TCZ-Team'''
        },
        'admin_override': {
            'subject': 'Buchungsstornierung durch Administrator',
            'body': '''Hallo {recipient_name},

deine Buchung wurde durch einen Administrator storniert:

Platz: {court_number}
Datum: {date}
Uhrzeit: {start_time} - {end_time}
Grund: {reason}

Viele Grüße
Dein TCZ-Team'''
        },
        'email_verification': {
            'subject': 'Bitte bestätige deine E-Mail-Adresse - TC Zellerndorf',
            'body': '''Hallo {recipient_name},

willkommen beim Tennisclub Zellerndorf!

Bitte bestätige deine E-Mail-Adresse, indem du auf den folgenden Link klickst:

{verification_url}

Der Link ist 48 Stunden gültig.

Wichtig: Solange deine E-Mail-Adresse nicht bestätigt ist, erhältst du keine Benachrichtigungen zu deinen Buchungen.

Falls du diese E-Mail nicht erwartet hast, kannst du sie ignorieren.

Viele Grüße
Dein TCZ-Team'''
        }
    }
    
    @staticmethod
    def _send_email_sync(recipient_email, subject, body, app):
        """
        Synchronously send an email (used by background thread).

        Args:
            recipient_email: Email address of recipient
            subject: Email subject
            body: Email body text
            app: Flask application instance for context

        Returns:
            bool: True if sent successfully, False otherwise
        """
        with app.app_context():
            # Skip email if disabled (check for disabled placeholder)
            mail_username = app.config.get('MAIL_USERNAME')
            if not mail_username or mail_username == 'disabled@example.com':
                logger.info(f"Email sending disabled, skipping email to {recipient_email}")
                return False

            # In development mode, redirect all emails to a single address
            dev_recipient = app.config.get('DEV_EMAIL_RECIPIENT')
            actual_recipient = recipient_email

            if dev_recipient and app.debug:
                logger.info(f"DEV MODE: Redirecting email from {recipient_email} to {dev_recipient}")
                actual_recipient = dev_recipient
                # Add header to body showing original recipient
                body = f"[DEV MODE - Original recipient: {recipient_email}]\n\n" + body

            try:
                msg = Message(
                    subject=subject,
                    recipients=[actual_recipient],
                    body=body,
                    sender=app.config.get('MAIL_DEFAULT_SENDER')
                )
                mail.send(msg)
                logger.info(f"Email sent successfully to {actual_recipient}")
                return True
            except Exception as e:
                # Log error but don't fail the operation
                logger.error(f"Failed to send email to {actual_recipient}: {str(e)}")
                return False

    @staticmethod
    def _send_email(recipient_email, subject, body, async_send=True):
        """
        Send an email with error handling.

        In development mode, all emails are redirected to DEV_EMAIL_RECIPIENT
        with a header showing the original recipient.

        Args:
            recipient_email: Email address of recipient
            subject: Email subject
            body: Email body text
            async_send: If True, send in background thread (default True)

        Returns:
            bool: True if queued/sent successfully, False otherwise
        """
        app = current_app._get_current_object()

        if async_send:
            # Send in background thread to avoid blocking the request
            thread = threading.Thread(
                target=EmailService._send_email_sync,
                args=(recipient_email, subject, body, app)
            )
            thread.daemon = True
            thread.start()
            logger.info(f"Email queued for async delivery to {recipient_email}")
            return True
        else:
            return EmailService._send_email_sync(recipient_email, subject, body, app)
    
    @staticmethod
    def _should_notify_member(member, is_own_booking):
        """
        Check if member should receive notification based on their preferences
        and email verification status.

        Args:
            member: Member object
            is_own_booking: True if this member initiated the booking

        Returns:
            bool: True if member should receive notification
        """
        # Skip if email is not verified
        if not member.email_verified:
            logger.info(f"Skipping notification to {member.email} (email not verified)")
            return False
        if not member.notifications_enabled:
            return False
        if is_own_booking:
            return member.notify_own_bookings
        return member.notify_other_bookings

    @staticmethod
    def _send_reservation_email(reservation, template_key, extra_context=None):
        """
        Generic method to send reservation emails to both parties.
        Respects member notification preferences.

        Args:
            reservation: Reservation object
            template_key: Key for template in TEMPLATES dict
            extra_context: Optional dict with additional context variables

        Returns:
            bool: True if all intended emails sent successfully
        """
        template = EmailService.TEMPLATES[template_key]

        # Build base context
        context = {
            'court_number': reservation.court.number,
            'date': reservation.date.strftime('%d.%m.%Y'),
            'start_time': reservation.start_time.strftime('%H:%M'),
            'end_time': reservation.end_time.strftime('%H:%M'),
            'booked_for_name': reservation.booked_for.name,
            'booked_by_name': reservation.booked_by.name
        }

        # Add extra context if provided
        if extra_context:
            context.update(extra_context)

        is_own_booking = reservation.booked_for_id == reservation.booked_by_id

        # Send to booked_for member (check preferences)
        success1 = True
        if EmailService._should_notify_member(reservation.booked_for, is_own_booking):
            success1 = EmailService._send_email(
                reservation.booked_for.email,
                template['subject'].format(**context),
                template['body'].format(recipient_name=reservation.booked_for.name, **context)
            )
        else:
            logger.info(f"Skipping notification to {reservation.booked_for.email} (preferences)")

        # Send to booked_by member (if different) - always "own booking" for them
        success2 = True
        if reservation.booked_for_id != reservation.booked_by_id:
            if EmailService._should_notify_member(reservation.booked_by, is_own_booking=True):
                success2 = EmailService._send_email(
                    reservation.booked_by.email,
                    template['subject'].format(**context),
                    template['body'].format(recipient_name=reservation.booked_by.name, **context)
                )
            else:
                logger.info(f"Skipping notification to {reservation.booked_by.email} (preferences)")

        return success1 and success2
    
    @staticmethod
    def send_booking_created(reservation):
        """
        Send booking created notification to both parties.
        
        Args:
            reservation: Reservation object
            
        Returns:
            bool: True if both emails sent successfully
        """
        return EmailService._send_reservation_email(reservation, 'booking_created')
    
    @staticmethod
    def send_booking_modified(reservation):
        """
        Send booking modified notification to both parties.
        
        Args:
            reservation: Reservation object
            
        Returns:
            bool: True if both emails sent successfully
        """
        return EmailService._send_reservation_email(reservation, 'booking_modified')
    
    @staticmethod
    def send_booking_cancelled(reservation, reason=None):
        """
        Send booking cancelled notification to both parties.
        
        Args:
            reservation: Reservation object
            reason: Optional cancellation reason
            
        Returns:
            bool: True if both emails sent successfully
        """
        reason_text = f"Grund: {reason}" if reason else ""
        return EmailService._send_reservation_email(
            reservation, 
            'booking_cancelled',
            {'reason_text': reason_text}
        )
    
    @staticmethod
    def send_admin_override(reservation, reason):
        """
        Send admin override notification to both parties.

        Args:
            reservation: Reservation object
            reason: Override reason

        Returns:
            bool: True if both emails sent successfully
        """
        return EmailService._send_reservation_email(
            reservation,
            'admin_override',
            {'reason': reason}
        )

    @staticmethod
    def send_verification_email(member, verification_url):
        """
        Send email verification link to a member.

        Note: This email is sent regardless of email_verified status,
        as it's the mechanism to verify the email address.

        Args:
            member: Member object
            verification_url: Full verification URL

        Returns:
            bool: True if email was sent successfully
        """
        template = EmailService.TEMPLATES['email_verification']

        return EmailService._send_email(
            member.email,
            template['subject'],
            template['body'].format(
                recipient_name=member.firstname,
                verification_url=verification_url
            )
        )
