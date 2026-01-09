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

    # Member errors
    MEMBER_NOT_FOUND = "Mitglied nicht gefunden"
    MEMBER_EMAIL_ALREADY_EXISTS = "E-Mail-Adresse wird bereits verwendet"
    MEMBER_INVALID_EMAIL = "Ungültige E-Mail-Adresse"
    MEMBER_PASSWORD_TOO_SHORT = "Passwort muss mindestens 8 Zeichen lang sein"
    MEMBER_PASSWORD_REQUIRED = "Passwort ist erforderlich"
    MEMBER_FIRSTNAME_REQUIRED = "Vorname ist erforderlich"
    MEMBER_LASTNAME_REQUIRED = "Nachname ist erforderlich"
    MEMBER_EMAIL_REQUIRED = "E-Mail ist erforderlich"
    MEMBER_INVALID_ROLE = "Ungültige Rolle"
    MEMBER_CANNOT_DELETE_SELF = "Sie können sich nicht selbst löschen"
    MEMBER_CANNOT_DEACTIVATE_SELF = "Sie können sich nicht selbst deaktivieren"
    MEMBER_ALREADY_DEACTIVATED = "Mitglied ist bereits deaktiviert"
    MEMBER_NOT_DEACTIVATED = "Mitglied ist nicht deaktiviert"
    MEMBER_HAS_ACTIVE_RESERVATIONS = "Mitglied hat aktive Buchungen und kann nicht gelöscht werden"

    # Membership type errors
    SUSTAINING_MEMBER_NO_ACCESS = "Fördermitglieder haben keinen Zugang zum Buchungssystem"
    MEMBER_INVALID_MEMBERSHIP_TYPE = "Ungültiger Mitgliedschaftstyp"

    # CSV Import errors
    CSV_NO_FILE = "Keine Datei ausgewählt"
    CSV_EMPTY_FILE = "Die CSV-Datei ist leer"
    CSV_INVALID_FORMAT = "Ungültiges CSV-Format. Erwartetes Format: Vorname;Nachname;Email;PLZ;Stadt;Adresse;Telefon"
    CSV_IMPORT_FAILED = "CSV-Import fehlgeschlagen"

    # Payment errors
    MEMBER_FEE_UNPAID_BOOKING_WARNING = "Hinweis: Ihr Mitgliedsbeitrag ist noch nicht bezahlt."

    # Payment deadline errors
    PAYMENT_DEADLINE_PASSED = "Die Zahlungsfrist ist abgelaufen. Bitte bezahlen Sie Ihren Mitgliedsbeitrag, um wieder buchen zu können."
    PAYMENT_DEADLINE_INVALID_DATE = "Ungültiges Datum für Zahlungsfrist"

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

    # Member success
    MEMBER_CREATED = "Mitglied erfolgreich erstellt"
    MEMBER_UPDATED = "Mitglied erfolgreich aktualisiert"
    MEMBER_DELETED = "Mitglied erfolgreich gelöscht"
    MEMBER_DEACTIVATED = "Mitglied erfolgreich deaktiviert"
    MEMBER_REACTIVATED = "Mitglied erfolgreich reaktiviert"
    MEMBER_ROLE_CHANGED = "Mitgliederrolle erfolgreich geändert"

    # Membership and payment success
    MEMBER_MEMBERSHIP_TYPE_CHANGED = "Mitgliedschaftstyp erfolgreich geändert"
    MEMBER_FEE_MARKED_PAID = "Beitragszahlung erfolgreich vermerkt"
    MEMBER_FEE_MARKED_UNPAID = "Beitragszahlung entfernt"

    # CSV Import success
    CSV_IMPORT_SUCCESS = "CSV-Import erfolgreich abgeschlossen"

    # Payment deadline success
    PAYMENT_DEADLINE_SET = "Zahlungsfrist erfolgreich gesetzt"
    PAYMENT_DEADLINE_CLEARED = "Zahlungsfrist wurde entfernt"


class InfoMessages:
    """Informational messages used throughout the application."""

    # Availability info
    AVAILABILITY_INFO = "Verfügbare Buchungsplätze: {available_slots} von 2 (basierend auf aktueller Zeit)"
