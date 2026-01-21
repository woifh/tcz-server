"""Push notification service for sending APNs notifications."""
import jwt
import time
import threading
import logging
from datetime import datetime
from flask import current_app

logger = logging.getLogger(__name__)


class PushNotificationService:
    """Service for sending push notifications via APNs."""

    # JWT token cache (class-level)
    _jwt_token = None
    _jwt_token_expiry = None
    _token_lock = threading.Lock()

    # German notification templates
    TEMPLATES = {
        'booking_created': {
            'title': 'Buchungsbestaetigung',
            'body': 'Platz {court_number} am {date}, {start_time} - {end_time}'
        },
        'booking_for_you': {
            'title': 'Neue Buchung fuer dich',
            'body': '{booked_by_name} hat Platz {court_number} fuer dich gebucht ({date}, {start_time})'
        },
        'booking_cancelled': {
            'title': 'Buchung storniert',
            'body': 'Platz {court_number} am {date}, {start_time} wurde storniert'
        },
        'booking_suspended': {
            'title': 'Buchung ausgesetzt',
            'body': 'Platz {court_number} am {date}, {start_time} - {reason}'
        },
        'booking_restored': {
            'title': 'Buchung wiederhergestellt',
            'body': 'Platz {court_number} am {date}, {start_time} ist wieder aktiv'
        }
    }

    @classmethod
    def _get_apns_token(cls, app):
        """Generate or return cached JWT token for APNs authentication."""
        current_time = time.time()

        with cls._token_lock:
            # Return cached token if still valid (50 minutes, APNs allows 60)
            if cls._jwt_token and cls._jwt_token_expiry and current_time < cls._jwt_token_expiry:
                return cls._jwt_token

            key_id = app.config.get('APNS_KEY_ID')
            team_id = app.config.get('APNS_TEAM_ID')
            key_path = app.config.get('APNS_KEY_PATH')

            if not all([key_id, team_id, key_path]):
                logger.warning("APNs credentials not configured")
                return None

            try:
                with open(key_path, 'r') as f:
                    private_key = f.read()

                headers = {
                    'alg': 'ES256',
                    'kid': key_id
                }
                payload = {
                    'iss': team_id,
                    'iat': int(current_time)
                }

                cls._jwt_token = jwt.encode(payload, private_key, algorithm='ES256', headers=headers)
                cls._jwt_token_expiry = current_time + (50 * 60)  # 50 minutes
                return cls._jwt_token
            except Exception as e:
                logger.error(f"Failed to generate APNs token: {e}")
                return None

    @staticmethod
    def _send_push_sync(device_token, payload, app):
        """
        Synchronously send a push notification (used by background thread).

        Args:
            device_token: APNs device token string
            payload: APNs payload dictionary
            app: Flask application instance for context
        """
        with app.app_context():
            try:
                import httpx

                jwt_token = PushNotificationService._get_apns_token(app)
                if not jwt_token:
                    logger.warning("No APNs token available, skipping push notification")
                    return False

                bundle_id = app.config.get('APNS_BUNDLE_ID', 'com.tcz.tennisapp')
                is_production = not app.debug

                if is_production:
                    host = "api.push.apple.com"
                else:
                    host = "api.sandbox.push.apple.com"

                url = f"https://{host}/3/device/{device_token}"

                headers = {
                    'authorization': f'bearer {jwt_token}',
                    'apns-topic': bundle_id,
                    'apns-push-type': 'alert',
                    'apns-priority': '10'
                }

                with httpx.Client(http2=True, timeout=30.0) as client:
                    response = client.post(url, json=payload, headers=headers)

                    if response.status_code == 200:
                        logger.info(f"Push sent successfully to {device_token[:20]}...")
                        return True
                    elif response.status_code == 410:
                        # Device token is no longer valid, mark as inactive
                        PushNotificationService._deactivate_token_sync(device_token, app)
                        logger.info(f"Deactivated invalid token: {device_token[:20]}...")
                        return False
                    else:
                        logger.error(f"APNs error {response.status_code}: {response.text}")
                        return False

            except Exception as e:
                logger.error(f"Failed to send push notification: {e}")
                return False

    @staticmethod
    def _deactivate_token_sync(token, app):
        """Mark a device token as inactive."""
        with app.app_context():
            from app import db
            from app.models import DeviceToken

            device_token = DeviceToken.query.filter_by(token=token).first()
            if device_token:
                device_token.is_active = False
                db.session.commit()

    @staticmethod
    def _send_push_async(device_token, payload, app):
        """Send push notification in background thread."""
        thread = threading.Thread(
            target=PushNotificationService._send_push_sync,
            args=(device_token, payload, app)
        )
        thread.daemon = True
        thread.start()

    @staticmethod
    def _should_notify_member_push(member, is_own_booking):
        """
        Check if member should receive push notification based on their preferences.

        Args:
            member: Member object
            is_own_booking: True if this member initiated the booking

        Returns:
            bool: True if member should receive push notification
        """
        # Skip if push notifications are disabled
        if not member.push_notifications_enabled:
            return False
        # Skip if email is not verified (same rule as email)
        if not member.email_verified:
            logger.info(f"Skipping push to {member.email} (email not verified)")
            return False
        # Use push-specific preferences
        if is_own_booking:
            return member.push_notify_own_bookings
        return member.push_notify_other_bookings

    @staticmethod
    def _get_member_tokens(member_id):
        """Get all active device tokens for a member."""
        from app.models import DeviceToken

        tokens = DeviceToken.query.filter_by(
            member_id=member_id,
            is_active=True
        ).all()
        return [t.token for t in tokens]

    @staticmethod
    def _build_payload(template_key, context, notification_type=None):
        """Build APNs payload from template."""
        template = PushNotificationService.TEMPLATES.get(template_key, {})

        title = template.get('title', 'TCZ Buchung')
        body = template.get('body', '').format(**context)

        payload = {
            'aps': {
                'alert': {
                    'title': title,
                    'body': body
                },
                'sound': 'default',
                'badge': 1
            }
        }

        # Add custom data for deep linking
        if notification_type:
            payload['type'] = notification_type

        return payload

    @staticmethod
    def send_booking_created_push(reservation):
        """Send push notification for booking creation."""
        app = current_app._get_current_object()

        context = {
            'court_number': reservation.court.number,
            'date': reservation.date.strftime('%d.%m.%Y'),
            'start_time': reservation.start_time.strftime('%H:%M'),
            'end_time': reservation.end_time.strftime('%H:%M'),
            'booked_for_name': reservation.booked_for.name,
            'booked_by_name': reservation.booked_by.name
        }

        is_own_booking = reservation.booked_for_id == reservation.booked_by_id

        # Notify booked_for member
        if PushNotificationService._should_notify_member_push(reservation.booked_for, is_own_booking):
            tokens = PushNotificationService._get_member_tokens(reservation.booked_for_id)

            if is_own_booking:
                template_key = 'booking_created'
            else:
                template_key = 'booking_for_you'

            payload = PushNotificationService._build_payload(template_key, context, 'booking_created')

            for token in tokens:
                PushNotificationService._send_push_async(token, payload, app)
        else:
            logger.info(f"Skipping push to booked_for {reservation.booked_for.email} (preferences)")

        # Notify booked_by member if different (they always get "own booking" notification)
        if not is_own_booking:
            if PushNotificationService._should_notify_member_push(reservation.booked_by, is_own_booking=True):
                tokens = PushNotificationService._get_member_tokens(reservation.booked_by_id)
                payload = PushNotificationService._build_payload('booking_created', context, 'booking_created')

                for token in tokens:
                    PushNotificationService._send_push_async(token, payload, app)
            else:
                logger.info(f"Skipping push to booked_by {reservation.booked_by.email} (preferences)")

    @staticmethod
    def send_booking_cancelled_push(reservation, reason=None):
        """Send push notification for booking cancellation."""
        app = current_app._get_current_object()

        context = {
            'court_number': reservation.court.number,
            'date': reservation.date.strftime('%d.%m.%Y'),
            'start_time': reservation.start_time.strftime('%H:%M'),
            'reason': reason or ''
        }

        payload = PushNotificationService._build_payload('booking_cancelled', context, 'booking_cancelled')

        # Notify booked_for
        if reservation.booked_for.push_notifications_enabled and reservation.booked_for.push_notify_court_blocked:
            if reservation.booked_for.email_verified:
                tokens = PushNotificationService._get_member_tokens(reservation.booked_for_id)
                for token in tokens:
                    PushNotificationService._send_push_async(token, payload, app)

        # Notify booked_by if different
        if reservation.booked_for_id != reservation.booked_by_id:
            if reservation.booked_by.push_notifications_enabled and reservation.booked_by.push_notify_court_blocked:
                if reservation.booked_by.email_verified:
                    tokens = PushNotificationService._get_member_tokens(reservation.booked_by_id)
                    for token in tokens:
                        PushNotificationService._send_push_async(token, payload, app)

    @staticmethod
    def send_booking_suspended_push(reservation, reason=None):
        """Send push notification for booking suspension."""
        app = current_app._get_current_object()

        context = {
            'court_number': reservation.court.number,
            'date': reservation.date.strftime('%d.%m.%Y'),
            'start_time': reservation.start_time.strftime('%H:%M'),
            'reason': reason or 'Voruebergehende Sperre'
        }

        payload = PushNotificationService._build_payload('booking_suspended', context, 'booking_suspended')

        # Notify booked_for
        if reservation.booked_for.push_notifications_enabled and reservation.booked_for.push_notify_court_blocked:
            if reservation.booked_for.email_verified:
                tokens = PushNotificationService._get_member_tokens(reservation.booked_for_id)
                for token in tokens:
                    PushNotificationService._send_push_async(token, payload, app)

        # Notify booked_by if different
        if reservation.booked_for_id != reservation.booked_by_id:
            if reservation.booked_by.push_notifications_enabled and reservation.booked_by.push_notify_court_blocked:
                if reservation.booked_by.email_verified:
                    tokens = PushNotificationService._get_member_tokens(reservation.booked_by_id)
                    for token in tokens:
                        PushNotificationService._send_push_async(token, payload, app)

    @staticmethod
    def send_booking_restored_push(reservation):
        """Send push notification for booking restoration."""
        app = current_app._get_current_object()

        context = {
            'court_number': reservation.court.number,
            'date': reservation.date.strftime('%d.%m.%Y'),
            'start_time': reservation.start_time.strftime('%H:%M')
        }

        payload = PushNotificationService._build_payload('booking_restored', context, 'booking_restored')

        # Notify booked_for
        if reservation.booked_for.push_notifications_enabled:
            if reservation.booked_for.email_verified:
                tokens = PushNotificationService._get_member_tokens(reservation.booked_for_id)
                for token in tokens:
                    PushNotificationService._send_push_async(token, payload, app)

        # Notify booked_by if different
        if reservation.booked_for_id != reservation.booked_by_id:
            if reservation.booked_by.push_notifications_enabled:
                if reservation.booked_by.email_verified:
                    tokens = PushNotificationService._get_member_tokens(reservation.booked_by_id)
                    for token in tokens:
                        PushNotificationService._send_push_async(token, payload, app)
