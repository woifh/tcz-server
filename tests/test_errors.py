"""Tests for error message utilities."""
import pytest
from app.errors import get_error_message, get_success_message


class TestGetErrorMessage:
    """Test get_error_message function."""
    
    def test_invalid_credentials(self):
        """Test invalid credentials error."""
        msg = get_error_message('INVALID_CREDENTIALS')
        assert 'E-Mail' in msg or 'Passwort' in msg
    
    def test_unauthorized(self):
        """Test unauthorized error."""
        msg = get_error_message('UNAUTHORIZED')
        assert 'Berechtigung' in msg
    
    def test_not_found(self):
        """Test not found error."""
        msg = get_error_message('NOT_FOUND')
        assert 'nicht gefunden' in msg
    
    def test_booking_conflict(self):
        """Test booking conflict error."""
        msg = get_error_message('BOOKING_CONFLICT')
        assert 'bereits' in msg and 'gebucht' in msg
    
    def test_invalid_email(self):
        """Test invalid email error."""
        msg = get_error_message('INVALID_EMAIL')
        assert 'Ungültige' in msg and 'E-Mail' in msg
    
    def test_unknown_error_code(self):
        """Test unknown error code returns generic message."""
        msg = get_error_message('unknown_code_xyz')
        assert 'Fehler' in msg
    
    def test_with_kwargs(self):
        """Test error message with kwargs."""
        msg = get_error_message('NOT_FOUND', resource='Buchung')
        assert isinstance(msg, str)


class TestGetSuccessMessage:
    """Test get_success_message function."""
    
    def test_booking_created(self):
        """Test booking created success message."""
        msg = get_success_message('BOOKING_CREATED')
        assert 'erfolgreich' in msg and 'erstellt' in msg
    
    def test_booking_updated(self):
        """Test booking updated success message."""
        msg = get_success_message('BOOKING_UPDATED')
        assert 'erfolgreich' in msg and 'aktualisiert' in msg
    
    def test_booking_cancelled(self):
        """Test booking cancelled success message."""
        msg = get_success_message('BOOKING_CANCELLED')
        assert 'erfolgreich' in msg and 'storniert' in msg
    
    def test_member_created(self):
        """Test member created success message."""
        msg = get_success_message('MEMBER_CREATED')
        assert 'erfolgreich' in msg and 'erstellt' in msg
    
    def test_unknown_message_code(self):
        """Test unknown message code returns generic message."""
        msg = get_success_message('unknown_code_xyz')
        assert 'erfolgreich' in msg
    
    def test_with_kwargs(self):
        """Test success message with kwargs."""
        msg = get_success_message('BOOKING_CREATED', resource='Buchung')
        assert isinstance(msg, str)
