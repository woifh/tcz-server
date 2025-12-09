/**
 * Utility functions for testing Alpine.js components
 */

/**
 * Create a mock Alpine component instance
 * @param {Function} componentFactory - The component factory function
 * @param {Object} initialData - Initial data to merge with component
 * @returns {Object} Component instance
 */
export function createComponent(componentFactory, initialData = {}) {
    const component = componentFactory();
    return { ...component, ...initialData };
}

/**
 * Mock successful API response
 * @param {*} data - Response data
 * @returns {Promise} Resolved promise with data
 */
export function mockApiSuccess(data) {
    global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => data,
        status: 200
    });
}

/**
 * Mock API error response
 * @param {number} status - HTTP status code
 * @param {string} message - Error message
 * @returns {Promise} Rejected promise with error
 */
export function mockApiError(status, message) {
    global.fetch.mockResolvedValueOnce({
        ok: false,
        json: async () => ({ message }),
        status
    });
}

/**
 * Mock network error
 * @param {string} message - Error message
 * @returns {Promise} Rejected promise
 */
export function mockNetworkError(message = 'Network error') {
    global.fetch.mockRejectedValueOnce(new Error(message));
}

/**
 * Wait for async operations to complete
 * @param {number} ms - Milliseconds to wait
 * @returns {Promise}
 */
export function wait(ms = 0) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Create a mock date in ISO format
 * @param {number} daysOffset - Days to offset from today
 * @returns {string} ISO date string (YYYY-MM-DD)
 */
export function createMockDate(daysOffset = 0) {
    const date = new Date();
    date.setDate(date.getDate() + daysOffset);
    return date.toISOString().split('T')[0];
}

/**
 * Create mock availability data
 * @param {string} date - Date string
 * @param {number} courts - Number of courts
 * @returns {Object} Mock availability data
 */
export function createMockAvailability(date, courts = 6) {
    const timeSlots = [];
    for (let hour = 6; hour < 22; hour++) {
        const time = `${hour.toString().padStart(2, '0')}:00`;
        for (let court = 1; court <= courts; court++) {
            timeSlots.push({
                court_id: court,
                court_name: `Platz ${court}`,
                time,
                status: 'available',
                reservation: null,
                block: null
            });
        }
    }
    return { date, slots: timeSlots };
}

/**
 * Create mock reservation data
 * @param {Object} overrides - Properties to override
 * @returns {Object} Mock reservation
 */
export function createMockReservation(overrides = {}) {
    return {
        id: 1,
        date: createMockDate(1),
        start_time: '10:00',
        end_time: '11:00',
        court_id: 1,
        court_name: 'Platz 1',
        member_id: 1,
        member_name: 'Test User',
        booked_for_id: 1,
        booked_for_name: 'Test User',
        is_short_notice: false,
        created_at: new Date().toISOString(),
        ...overrides
    };
}

/**
 * Create mock favourite data
 * @param {Object} overrides - Properties to override
 * @returns {Object} Mock favourite
 */
export function createMockFavourite(overrides = {}) {
    return {
        id: 1,
        member_id: 2,
        member_name: 'Favourite User',
        member_email: 'favourite@example.com',
        ...overrides
    };
}
