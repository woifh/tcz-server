"""German error messages for the application."""

# Validation errors
VALIDATION_ERRORS = {
    'BOOKING_CONFLICT': 'Dieser Platz ist bereits für diese Zeit gebucht',
    'RESERVATION_LIMIT': 'Sie haben bereits 2 aktive Buchungen',
    'BLOCKED_SLOT': 'Dieser Platz ist für diese Zeit gesperrt',
    'INVALID_TIME': 'Buchungen sind nur zwischen 06:00 und 21:00 Uhr möglich',
    'INVALID_DURATION': 'Buchungen müssen genau eine Stunde dauern',
    'PAST_DATE': 'Buchungen können nicht in der Vergangenheit erstellt werden',
    'INVALID_COURT': 'Ungültige Platznummer (1-6)',
    'REQUIRED_FIELD': 'Dieses Feld ist erforderlich',
    'INVALID_EMAIL': 'Ungültige E-Mail-Adresse',
    'EMAIL_EXISTS': 'Diese E-Mail-Adresse wird bereits verwendet',
    'WEAK_PASSWORD': 'Das Passwort muss mindestens 8 Zeichen lang sein',
}

# Authentication errors
AUTH_ERRORS = {
    'INVALID_CREDENTIALS': 'E-Mail oder Passwort ist falsch',
    'UNAUTHORIZED': 'Sie haben keine Berechtigung für diese Aktion',
    'LOGIN_REQUIRED': 'Bitte melden Sie sich an, um auf diese Seite zuzugreifen',
    'SESSION_EXPIRED': 'Ihre Sitzung ist abgelaufen. Bitte melden Sie sich erneut an',
}

# Resource errors
RESOURCE_ERRORS = {
    'NOT_FOUND': 'Die angeforderte Ressource wurde nicht gefunden',
    'MEMBER_NOT_FOUND': 'Mitglied nicht gefunden',
    'RESERVATION_NOT_FOUND': 'Buchung nicht gefunden',
    'COURT_NOT_FOUND': 'Platz nicht gefunden',
    'BLOCK_NOT_FOUND': 'Sperrung nicht gefunden',
}

# Server errors
SERVER_ERRORS = {
    'INTERNAL_ERROR': 'Ein interner Fehler ist aufgetreten',
    'DATABASE_ERROR': 'Datenbankfehler',
    'EMAIL_FAILED': 'E-Mail konnte nicht gesendet werden',
}

# Success messages
SUCCESS_MESSAGES = {
    'BOOKING_CREATED': 'Buchung erfolgreich erstellt',
    'BOOKING_UPDATED': 'Buchung erfolgreich aktualisiert',
    'BOOKING_CANCELLED': 'Buchung erfolgreich storniert',
    'MEMBER_CREATED': 'Mitglied erfolgreich erstellt',
    'MEMBER_UPDATED': 'Mitglied erfolgreich aktualisiert',
    'MEMBER_DELETED': 'Mitglied erfolgreich gelöscht',
    'BLOCK_CREATED': 'Sperrung erfolgreich erstellt',
    'BLOCK_DELETED': 'Sperrung erfolgreich gelöscht',
    'FAVOURITE_ADDED': 'Favorit erfolgreich hinzugefügt',
    'FAVOURITE_REMOVED': 'Favorit erfolgreich entfernt',
    'LOGIN_SUCCESS': 'Erfolgreich angemeldet',
    'LOGOUT_SUCCESS': 'Erfolgreich abgemeldet',
}

# Info messages
INFO_MESSAGES = {
    'NO_RESERVATIONS': 'Sie haben derzeit keine aktiven Buchungen',
    'NO_MEMBERS': 'Keine Mitglieder gefunden',
    'NO_BLOCKS': 'Keine Sperrungen für dieses Datum',
}


def get_error_message(error_code, **kwargs):
    """
    Get a German error message by code.
    
    Args:
        error_code: The error code
        **kwargs: Optional parameters to format the message
        
    Returns:
        Formatted German error message
    """
    # Check all error dictionaries
    for error_dict in [VALIDATION_ERRORS, AUTH_ERRORS, RESOURCE_ERRORS, SERVER_ERRORS]:
        if error_code in error_dict:
            message = error_dict[error_code]
            return message.format(**kwargs) if kwargs else message
    
    # Default error message
    return 'Ein Fehler ist aufgetreten'


def get_success_message(message_code, **kwargs):
    """
    Get a German success message by code.
    
    Args:
        message_code: The message code
        **kwargs: Optional parameters to format the message
        
    Returns:
        Formatted German success message
    """
    if message_code in SUCCESS_MESSAGES:
        message = SUCCESS_MESSAGES[message_code]
        return message.format(**kwargs) if kwargs else message
    
    return 'Aktion erfolgreich'
