/**
 * Utility functions for Tennis Club Reservation System
 */

/**
 * Calculate end time (1 hour after start)
 */
export function getEndTime(startTime) {
    const [hours, minutes] = startTime.split(':').map(Number);
    const endHours = (hours + 1).toString().padStart(2, '0');
    return `${endHours}:${minutes.toString().padStart(2, '0')}`;
}

/**
 * Format date in German convention (DD.MM.YYYY)
 */
export function formatDateGerman(dateString) {
    const date = new Date(dateString);
    const day = date.getDate().toString().padStart(2, '0');
    const month = (date.getMonth() + 1).toString().padStart(2, '0');
    const year = date.getFullYear();
    return `${day}.${month}.${year}`;
}

/**
 * Show success message
 */
export function showSuccess(message) {
    const flashDiv = document.createElement('div');
    flashDiv.className =
        'fixed top-4 right-4 bg-green-100 text-green-700 px-6 py-4 rounded-lg shadow-lg z-50';
    flashDiv.textContent = message;
    document.body.appendChild(flashDiv);

    setTimeout(() => {
        flashDiv.remove();
    }, 3000);
}

/**
 * Show error message
 */
export function showError(message) {
    const flashDiv = document.createElement('div');
    flashDiv.className =
        'fixed top-4 right-4 bg-red-100 text-red-700 px-6 py-4 rounded-lg shadow-lg z-50';
    flashDiv.textContent = message;
    document.body.appendChild(flashDiv);

    setTimeout(() => {
        flashDiv.remove();
    }, 5000);
}

/**
 * Generate time slots from 08:00 to 21:00
 */
export function generateTimeSlots() {
    const timeSlots = [];
    for (let hour = 8; hour <= 21; hour++) {
        timeSlots.push(`${hour.toString().padStart(2, '0')}:00`);
    }
    return timeSlots;
}
