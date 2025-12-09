/**
 * Date utility functions
 * Handles date formatting and calculations
 */

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
    const date = new Date(isoDate);
    date.setDate(date.getDate() + days);
    return date.toISOString().split('T')[0];
}

/**
 * Get today's date in ISO format
 * @returns {string} Today's date (YYYY-MM-DD)
 */
export function getToday() {
    return new Date().toISOString().split('T')[0];
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
