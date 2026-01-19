"""Email verification service for token generation and validation."""
import logging
from datetime import datetime
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from flask import current_app, url_for

from app import db
from app.models import Member

logger = logging.getLogger(__name__)

# Default token expiration: 48 hours in seconds
DEFAULT_TOKEN_EXPIRATION = 48 * 60 * 60


class VerificationService:
    """Service for email verification token management."""

    @staticmethod
    def _get_serializer():
        """Get the URL-safe timed serializer for token generation."""
        return URLSafeTimedSerializer(
            current_app.config['SECRET_KEY'],
            salt='email-verification'
        )

    @staticmethod
    def generate_verification_token(member_id: str, email: str) -> str:
        """
        Generate a verification token for a member.

        Args:
            member_id: The member's UUID
            email: The email address being verified

        Returns:
            str: URL-safe verification token
        """
        serializer = VerificationService._get_serializer()
        return serializer.dumps({'member_id': member_id, 'email': email})

    @staticmethod
    def verify_token(token: str, max_age: int = None) -> tuple:
        """
        Verify a token and return the member data.

        Args:
            token: The verification token
            max_age: Maximum token age in seconds (default from config)

        Returns:
            tuple: (member_id, email, error_message)
        """
        if max_age is None:
            max_age = current_app.config.get(
                'EMAIL_VERIFICATION_EXPIRATION',
                DEFAULT_TOKEN_EXPIRATION
            )

        serializer = VerificationService._get_serializer()

        try:
            data = serializer.loads(token, max_age=max_age)
            return data.get('member_id'), data.get('email'), None
        except SignatureExpired:
            return None, None, 'Der Bestätigungslink ist abgelaufen. Bitte fordere einen neuen an.'
        except BadSignature:
            return None, None, 'Ungültiger Bestätigungslink.'

    @staticmethod
    def verify_member_email(token: str) -> tuple:
        """
        Verify a member's email address using a token.

        Args:
            token: The verification token

        Returns:
            tuple: (success: bool, message: str, member: Member or None)
        """
        from app.services.member_service import MemberService

        member_id, email, error = VerificationService.verify_token(token)

        if error:
            return False, error, None

        member = Member.query.get(member_id)

        if not member:
            return False, 'Mitglied nicht gefunden.', None

        # Check if email still matches (in case user changed it)
        if member.email.lower() != email.lower():
            return False, 'E-Mail-Adresse wurde geändert. Bitte fordere einen neuen Bestätigungslink an.', None

        if member.email_verified:
            return True, 'Deine E-Mail-Adresse wurde bereits bestätigt.', member

        # Mark as verified
        member.email_verified = True
        member.email_verified_at = datetime.utcnow()

        try:
            # Log the verification
            MemberService.log_member_operation(
                operation='email_verified',
                member_id=member_id,
                operation_data={
                    'member_name': member.name,
                    'email': member.email,
                    'method': 'link'
                },
                performed_by_id=member_id  # Self-verification
            )

            db.session.commit()
            logger.info(f"Email verified for member {member_id} ({member.email})")
            return True, 'Deine E-Mail-Adresse wurde erfolgreich bestätigt!', member
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to verify email for member {member_id}: {e}")
            return False, 'Ein Fehler ist aufgetreten. Bitte versuch es nochmal.', None

    @staticmethod
    def get_verification_url(member: Member) -> str:
        """
        Generate the full verification URL for a member.

        Args:
            member: The member object

        Returns:
            str: Full verification URL
        """
        token = VerificationService.generate_verification_token(
            member.id,
            member.email
        )
        return url_for('auth.verify_email', token=token, _external=True)

    @staticmethod
    def reset_email_verification(member: Member, admin_id: str = None) -> bool:
        """
        Reset verification status (called when email changes).

        Args:
            member: The member object
            admin_id: ID of admin making the change (or None if self-service)

        Returns:
            bool: True if reset was performed, False if already unverified
        """
        from app.services.member_service import MemberService

        if not member.email_verified:
            return False

        old_verified_at = member.email_verified_at

        member.email_verified = False
        member.email_verified_at = None

        # Log the reset
        MemberService.log_member_operation(
            operation='email_verification_reset',
            member_id=member.id,
            operation_data={
                'member_name': member.name,
                'email': member.email,
                'reason': 'email_changed',
                'previous_verified_at': old_verified_at.isoformat() if old_verified_at else None
            },
            performed_by_id=admin_id
        )

        logger.info(f"Email verification reset for member {member.id} ({member.email})")
        return True

    @staticmethod
    def send_verification_email(member: Member, triggered_by: str = 'resend', admin_id: str = None) -> bool:
        """
        Send verification email to a member.

        Args:
            member: The member to send verification email to
            triggered_by: What triggered this email ('member_creation', 'resend', 'email_change')
            admin_id: ID of admin triggering the send (for audit), or None if self-service

        Returns:
            bool: True if email was sent successfully
        """
        from app.services.email_service import EmailService
        from app.services.member_service import MemberService

        verification_url = VerificationService.get_verification_url(member)
        success = EmailService.send_verification_email(member, verification_url)

        if success:
            # Log the email send
            MemberService.log_member_operation(
                operation='email_verification_sent',
                member_id=member.id,
                operation_data={
                    'member_name': member.name,
                    'email': member.email,
                    'triggered_by': triggered_by
                },
                performed_by_id=admin_id
            )
            logger.info(f"Verification email sent to {member.email} (triggered_by: {triggered_by})")
        else:
            logger.error(f"Failed to send verification email to {member.email}")

        return success
