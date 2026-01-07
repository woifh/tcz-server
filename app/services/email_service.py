"""Email service for sending notifications."""
from flask import current_app
from flask_mail import Message
from app import mail
import logging

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending email notifications in German."""
    
    # German email templates
    TEMPLATES = {
        'booking_created': {
            'subject': 'Buchungsbestätigung - Tennisplatz {court_number}',
            'body': '''Guten Tag {recipient_name},

Ihre Buchung wurde erfolgreich erstellt:

Platz: {court_number}
Datum: {date}
Uhrzeit: {start_time} - {end_time}
Gebucht für: {booked_for_name}
Gebucht von: {booked_by_name}

Mit freundlichen Grüßen
Ihr Tennisclub-Team'''
        },
        'booking_modified': {
            'subject': 'Buchungsänderung - Tennisplatz {court_number}',
            'body': '''Guten Tag {recipient_name},

Ihre Buchung wurde geändert:

Platz: {court_number}
Datum: {date}
Uhrzeit: {start_time} - {end_time}
Gebucht für: {booked_for_name}
Gebucht von: {booked_by_name}

Mit freundlichen Grüßen
Ihr Tennisclub-Team'''
        },
        'booking_cancelled': {
            'subject': 'Buchungsstornierung - Tennisplatz {court_number}',
            'body': '''Guten Tag {recipient_name},

Ihre Buchung wurde storniert:

Platz: {court_number}
Datum: {date}
Uhrzeit: {start_time} - {end_time}
{reason_text}

Mit freundlichen Grüßen
Ihr Tennisclub-Team'''
        },
        'admin_override': {
            'subject': 'Buchungsstornierung durch Administrator',
            'body': '''Guten Tag {recipient_name},

Ihre Buchung wurde durch einen Administrator storniert:

Platz: {court_number}
Datum: {date}
Uhrzeit: {start_time} - {end_time}
Grund: {reason}

Mit freundlichen Grüßen
Ihr Tennisclub-Team'''
        }
    }
    
    @staticmethod
    def _send_email(recipient_email, subject, body):
        """
        Send an email with error handling.

        In development mode, all emails are redirected to DEV_EMAIL_RECIPIENT
        with a header showing the original recipient.

        Args:
            recipient_email: Email address of recipient
            subject: Email subject
            body: Email body text

        Returns:
            bool: True if sent successfully, False otherwise
        """
        # Skip email if disabled (check for disabled placeholder)
        mail_username = current_app.config.get('MAIL_USERNAME')
        if not mail_username or mail_username == 'disabled@example.com':
            logger.info(f"Email sending disabled, skipping email to {recipient_email}")
            return False

        # In development mode, redirect all emails to a single address
        dev_recipient = current_app.config.get('DEV_EMAIL_RECIPIENT')
        actual_recipient = recipient_email

        if dev_recipient and current_app.debug:
            logger.info(f"DEV MODE: Redirecting email from {recipient_email} to {dev_recipient}")
            actual_recipient = dev_recipient
            # Add header to body showing original recipient
            body = f"[DEV MODE - Original recipient: {recipient_email}]\n\n" + body

        try:
            msg = Message(
                subject=subject,
                recipients=[actual_recipient],
                body=body,
                sender=current_app.config.get('MAIL_DEFAULT_SENDER')
            )
            mail.send(msg)
            logger.info(f"Email sent successfully to {actual_recipient}")
            return True
        except Exception as e:
            # Log error but don't fail the operation
            logger.error(f"Failed to send email to {actual_recipient}: {str(e)}")
            return False
    
    @staticmethod
    def _send_reservation_email(reservation, template_key, extra_context=None):
        """
        Generic method to send reservation emails to both parties.
        
        Args:
            reservation: Reservation object
            template_key: Key for template in TEMPLATES dict
            extra_context: Optional dict with additional context variables
            
        Returns:
            bool: True if both emails sent successfully
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
        
        # Send to booked_for member
        success1 = EmailService._send_email(
            reservation.booked_for.email,
            template['subject'].format(**context),
            template['body'].format(recipient_name=reservation.booked_for.name, **context)
        )
        
        # Send to booked_by member (if different)
        success2 = True
        if reservation.booked_for_id != reservation.booked_by_id:
            success2 = EmailService._send_email(
                reservation.booked_by.email,
                template['subject'].format(**context),
                template['body'].format(recipient_name=reservation.booked_by.name, **context)
            )
        
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
