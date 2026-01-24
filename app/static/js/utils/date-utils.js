/**
 * Date utility functions
 * Handles date formatting and calculations
 *
 * IMPORTANT: All date functions use Europe/Berlin timezone to ensure
 * consistency with the backend and correct behavior around midnight.
 */

const BERLIN_TIMEZONE = 'Europe/Berlin';

/**
 * Get current date/time in Berlin timezone as a Date-like object with ISO string
 * @returns {string} ISO date string (YYYY-MM-DD) in Berlin timezone
 */
export function getBerlinDateString() {
    return new Date().toLocaleDateString('sv-SE', { timeZone: BERLIN_TIMEZONE });
}

/**
 * Convert a Date object to ISO date string (YYYY-MM-DD) in Berlin timezone
 * @param {Date} date - Date object
 * @returns {string} ISO date string (YYYY-MM-DD)
 */
export function toBerlinDateString(date) {
    return date.toLocaleDateString('sv-SE', { timeZone: BERLIN_TIMEZONE });
}

/**
 * Format ISO date to German format (DD.MM.YYYY)
 * @param {string} isoDate - ISO date string (YYYY-MM-DD)
 * @returns {string} German formatted date
 */
export function formatDate(isoDate) {
    if (!isoDate) return '';

    const [year, month, day] = isoDate.split('-');
    return `${day}.${month}.${year}`;
}

/**
 * Format time string (HH:MM)
 * @param {string} time - Time string
 * @returns {string} Formatted time
 */
export function formatTime(time) {
    if (!time) return '';
    return time;
}

/**
 * Get end time from start time (adds 1 hour)
 * @param {string} startTime - Start time (HH:MM)
 * @returns {string} End time (HH:MM)
 */
export function getEndTime(startTime) {
    if (!startTime) return '';

    const [hour, minute] = startTime.split(':').map(Number);
    const endHour = hour + 1;
    return `${endHour.toString().padStart(2, '0')}:${minute.toString().padStart(2, '0')}`;
}

/**
 * Get time range string
 * @param {string} startTime - Start time (HH:MM)
 * @returns {string} Time range (HH:MM - HH:MM)
 */
export function getTimeRange(startTime) {
    if (!startTime) return '';
    return `${startTime} - ${getEndTime(startTime)}`;
}

/**
 * Add days to a date
 * @param {string} isoDate - ISO date string (YYYY-MM-DD)
 * @param {number} days - Number of days to add
 * @returns {string} New ISO date string
 */
export function addDays(isoDate, days) {
    const date = new Date(isoDate + 'T12:00:00'); // Use noon to avoid DST edge cases
    date.setDate(date.getDate() + days);
    return toBerlinDateString(date);
}

/**
 * Get today's date in ISO format (Berlin timezone)
 * @returns {string} Today's date (YYYY-MM-DD)
 */
export function getToday() {
    return getBerlinDateString();
}

/**
 * Check if date is in the past
 * @param {string} isoDate - ISO date string (YYYY-MM-DD)
 * @returns {boolean} True if date is in the past
 */
export function isPast(isoDate) {
    const date = new Date(isoDate);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    return date < today;
}

/**
 * Check if date is today
 * @param {string} isoDate - ISO date string (YYYY-MM-DD)
 * @returns {boolean} True if date is today
 */
export function isToday(isoDate) {
    return isoDate === getToday();
}

// German abbreviations for date strip
const GERMAN_MONTHS = [
    'JAN',
    'FEB',
    'MÄR',
    'APR',
    'MAI',
    'JUN',
    'JUL',
    'AUG',
    'SEP',
    'OKT',
    'NOV',
    'DEZ',
];
const GERMAN_WEEKDAYS = ['SO', 'MO', 'DI', 'MI', 'DO', 'FR', 'SA'];
const GERMAN_WEEKDAYS_LONG = ['So', 'Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa'];

/**
 * Get German month abbreviation (uppercase)
 * @param {Date} date - Date object
 * @returns {string} German month abbreviation (e.g., "JAN", "MÄR")
 */
export function getGermanMonthAbbr(date) {
    return GERMAN_MONTHS[date.getMonth()];
}

/**
 * Get German weekday abbreviation (uppercase)
 * @param {Date} date - Date object
 * @returns {string} German weekday abbreviation (e.g., "MO", "DI")
 */
export function getGermanWeekdayAbbr(date) {
    return GERMAN_WEEKDAYS[date.getDay()];
}

/**
 * Format ISO date to German header format (e.g., "Fr. 23.01.2026")
 * @param {string} isoDate - ISO date string (YYYY-MM-DD)
 * @returns {string} Formatted date header
 */
export function formatDateHeaderGerman(isoDate) {
    if (!isoDate) return '';
    const date = new Date(isoDate + 'T12:00:00');
    const weekday = GERMAN_WEEKDAYS_LONG[date.getDay()];
    const day = date.getDate().toString().padStart(2, '0');
    const month = (date.getMonth() + 1).toString().padStart(2, '0');
    const year = date.getFullYear();
    return `${weekday}. ${day}.${month}.${year}`;
}

/**
 * Generate array of date objects for date strip
 * @param {number} daysBefore - Number of days before today (default 30)
 * @param {number} daysAfter - Number of days after today (default 90)
 * @returns {Array} Array of date objects with isoDate, dayNumber, monthAbbr, weekdayAbbr, isToday
 */
export function generateDateRange(daysBefore = 30, daysAfter = 90) {
    const dates = [];
    const today = getToday();

    for (let offset = -daysBefore; offset <= daysAfter; offset++) {
        const isoDate = addDays(today, offset);
        const date = new Date(isoDate + 'T12:00:00');
        dates.push({
            isoDate,
            dayNumber: date.getDate(),
            monthAbbr: getGermanMonthAbbr(date),
            weekdayAbbr: getGermanWeekdayAbbr(date),
            isToday: offset === 0,
        });
    }

    return dates;
}
