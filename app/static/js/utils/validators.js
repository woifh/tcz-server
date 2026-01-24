/**
 * Validation utility functions
 * Handles form validation and data validation
 */

/**
 * Validate booking data
 * @param {Object} bookingData - Booking data to validate
 * @returns {Object} Validation result { valid: boolean, errors: string[] }
 */
export function validateBooking(bookingData) {
    const errors = [];

    if (!bookingData.court_id) {
        errors.push('Platz ist erforderlich');
    }

    if (!bookingData.date) {
        errors.push('Datum ist erforderlich');
    } else if (!isValidDate(bookingData.date)) {
        errors.push('Ungültiges Datum');
    }

    if (!bookingData.start_time) {
        errors.push('Uhrzeit ist erforderlich');
    } else if (!isValidTime(bookingData.start_time)) {
        errors.push('Ungültige Uhrzeit');
    }

    if (!bookingData.booked_for_id) {
        errors.push('Gebucht für ist erforderlich');
    }

    return {
        valid: errors.length === 0,
        errors,
    };
}

/**
 * Validate date format (YYYY-MM-DD)
 * @param {string} date - Date string
 * @returns {boolean} True if valid
 */
export function isValidDate(date) {
    if (!date) return false;

    const regex = /^\d{4}-\d{2}-\d{2}$/;
    if (!regex.test(date)) return false;

    const dateObj = new Date(date);
    return dateObj instanceof Date && !isNaN(dateObj);
}

/**
 * Validate time format (HH:MM)
 * @param {string} time - Time string
 * @returns {boolean} True if valid
 */
export function isValidTime(time) {
    if (!time) return false;

    const regex = /^([01]\d|2[0-3]):([0-5]\d)$/;
    return regex.test(time);
}

/**
 * Validate email format
 * @param {string} email - Email string
 * @returns {boolean} True if valid
 */
export function isValidEmail(email) {
    if (!email) return false;

    const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return regex.test(email);
}

/**
 * Validate required field
 * @param {any} value - Value to validate
 * @returns {boolean} True if not empty
 */
export function isRequired(value) {
    if (value === null || value === undefined) return false;
    if (typeof value === 'string') return value.trim().length > 0;
    return true;
}
