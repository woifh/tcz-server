"""Email service for sending notifications."""


class EmailService:
    """Service for sending email notifications."""
    
    @staticmethod
    def send_booking_created(reservation):
        """Send booking created notification - to be implemented."""
        pass
    
    @staticmethod
    def send_booking_modified(reservation):
        """Send booking modified notification - to be implemented."""
        pass
    
    @staticmethod
    def send_booking_cancelled(reservation, reason):
        """Send booking cancelled notification - to be implemented."""
        pass
    
    @staticmethod
    def send_admin_override(affected_members, reason):
        """Send admin override notification - to be implemented."""
        pass
    
    @staticmethod
    def format_german_email(template, **kwargs):
        """Format email in German - to be implemented."""
        pass
