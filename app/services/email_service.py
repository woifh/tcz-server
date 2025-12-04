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
        
        Args:
            recipient_email: Email address of recipient
            subject: Email subject
            body: Email body text
            
        Returns:
            bool: True if sent successfully, False otherwise
        """
        try:
            msg = Message(
                subject=subject,
                recipients=[recipient_email],
                body=body,
                sender=current_app.config.get('MAIL_DEFAULT_SENDER')
            )
            mail.send(msg)
            return True
        except Exception as e:
            # Log error but don't fail the operation
            logger.error(f"Failed to send email to {recipient_email}: {str(e)}")
            return False
    
    @staticmethod
    def send_booking_created(reservation):
        """
        Send booking created notification to both parties.
        
        Args:
            reservation: Reservation object
            
        Returns:
            bool: True if both emails sent successfully
        """
        template = EmailService.TEMPLATES['booking_created']
        
        context = {
            'court_number': reservation.court.number,
            'date': reservation.date.strftime('%d.%m.%Y'),
            'start_time': reservation.start_time.strftime('%H:%M'),
            'end_time': reservation.end_time.strftime('%H:%M'),
            'booked_for_name': reservation.booked_for.name,
            'booked_by_name': reservation.booked_by.name
        }
        
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
    def send_booking_modified(reservation):
        """
        Send booking modified notification to both parties.
        
        Args:
            reservation: Reservation object
            
        Returns:
            bool: True if both emails sent successfully
        """
        template = EmailService.TEMPLATES['booking_modified']
        
        context = {
            'court_number': reservation.court.number,
            'date': reservation.date.strftime('%d.%m.%Y'),
            'start_time': reservation.start_time.strftime('%H:%M'),
            'end_time': reservation.end_time.strftime('%H:%M'),
            'booked_for_name': reservation.booked_for.name,
            'booked_by_name': reservation.booked_by.name
        }
        
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
    def send_booking_cancelled(reservation, reason=None):
        """
        Send booking cancelled notification to both parties.
        
        Args:
            reservation: Reservation object
            reason: Optional cancellation reason
            
        Returns:
            bool: True if both emails sent successfully
        """
        template = EmailService.TEMPLATES['booking_cancelled']
        
        reason_text = f"Grund: {reason}" if reason else ""
        
        context = {
            'court_number': reservation.court.number,
            'date': reservation.date.strftime('%d.%m.%Y'),
            'start_time': reservation.start_time.strftime('%H:%M'),
            'end_time': reservation.end_time.strftime('%H:%M'),
            'reason_text': reason_text
        }
        
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
    def send_admin_override(reservation, reason):
        """
        Send admin override notification to both parties.
        
        Args:
            reservation: Reservation object
            reason: Override reason
            
        Returns:
            bool: True if both emails sent successfully
        """
        template = EmailService.TEMPLATES['admin_override']
        
        context = {
            'court_number': reservation.court.number,
            'date': reservation.date.strftime('%d.%m.%Y'),
            'start_time': reservation.start_time.strftime('%H:%M'),
            'end_time': reservation.end_time.strftime('%H:%M'),
            'reason': reason
        }
        
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
