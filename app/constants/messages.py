"""Centralized error and success messages for the application."""


class ErrorMessages:
    """Error messages used throughout the application."""

    # Reservation errors
    RESERVATION_LIMIT_REGULAR = (
        "Sie haben bereits 2 aktive Buchungen (zukünftige oder laufende Reservierungen). "
        "Aktive Buchungen sind solche, die noch nicht beendet sind."
    )
    RESERVATION_LIMIT_SHORT_NOTICE = (
        "Sie haben bereits eine aktive kurzfristige Buchung (zukünftige oder laufende Reservierung). "
        "Nur eine kurzfristige Buchung pro Mitglied ist erlaubt."
    )
    RESERVATION_NOT_FOUND = "Buchung nicht gefunden"
    RESERVATION_ALREADY_BOOKED = "Dieser Platz ist bereits für diese Zeit gebucht"

    # Cancellation errors
    CANCELLATION_STARTED = "Diese Buchung kann nicht mehr storniert werden (Spielzeit bereits begonnen)"
    CANCELLATION_TOO_LATE = "Diese Buchung kann nicht mehr storniert werden (weniger als 15 Minuten bis Spielbeginn)"
    SHORT_NOTICE_NO_CANCEL = "Kurzfristige Buchungen können nicht storniert werden"

    # Booking time errors
    BOOKING_PAST_ENDED = "Kurzfristige Buchungen sind nur möglich, solange die Spielzeit noch nicht beendet ist"
    BOOKING_PAST_REGULAR = "Buchungen in der Vergangenheit sind nicht möglich"

    # System errors
    TIME_CALCULATION_ERROR = "Fehler bei der Zeitberechnung. Bitte versuchen Sie es erneut."
    TIMEZONE_ERROR = "Zeitzonenfehler aufgetreten. Bitte versuchen Sie es erneut."
    VALIDATION_ERROR = "Validierungsfehler aufgetreten. Bitte überprüfen Sie Ihre Eingaben."
    UNEXPECTED_ERROR = "Ein unerwarteter Fehler ist aufgetreten. Bitte versuchen Sie es erneut."
    SYSTEM_ERROR = "Ein Systemfehler ist aufgetreten."
    FALLBACK_ACTIVE = "System verwendet vereinfachte Zeitlogik aufgrund technischer Probleme"

    # Block errors
    BLOCK_NO_COURTS_SPECIFIED = "At least one court must be specified"

    # Block reason errors
    BLOCK_REASON_NAME_EMPTY = "Sperrungsgrund-Name darf nicht leer sein"
    BLOCK_REASON_NOT_FOUND = "Sperrungsgrund nicht gefunden"

class SuccessMessages:
    """Success messages used throughout the application."""

    # Reservation success
    RESERVATION_CREATED = "Buchung erfolgreich erstellt"
    RESERVATION_UPDATED = "Buchung erfolgreich aktualisiert"
    RESERVATION_CANCELLED = "Buchung erfolgreich storniert"

    # Block success
    BLOCK_CREATED = "Sperre erfolgreich erstellt"
    BLOCK_UPDATED = "Sperre erfolgreich aktualisiert"
    BLOCK_DELETED = "Sperre erfolgreich gelöscht"

    # Block reason success
    BLOCK_REASON_CREATED = "Sperrungsgrund erfolgreich erstellt"
    BLOCK_REASON_UPDATED = "Sperrungsgrund erfolgreich aktualisiert"
    BLOCK_REASON_DELETED = "Sperrungsgrund erfolgreich gelöscht"


class InfoMessages:
    """Informational messages used throughout the application."""

    # Availability info
    AVAILABILITY_INFO = "Verfügbare Buchungsplätze: {available_slots} von 2 (basierend auf aktueller Zeit)"
