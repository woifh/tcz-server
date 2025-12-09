/**
 * API utility functions
 * Handles HTTP requests with error handling and retry logic
 */

/**
 * Make an API request with error handling
 * @param {string} url - API endpoint
 * @param {Object} options - Fetch options
 * @returns {Promise<Object>} Response data
 */
export async function apiRequest(url, options = {}) {
    try {
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new ApiError(data.error || 'Request failed', response.status, data);
        }
        
        return data;
    } catch (error) {
        if (error instanceof ApiError) {
            throw error;
        }
        throw new ApiError('Network error', 0, { originalError: error.message });
    }
}

/**
 * GET request
 */
export async function get(url) {
    return apiRequest(url, { method: 'GET' });
}

/**
 * POST request
 */
export async function post(url, data) {
    return apiRequest(url, {
        method: 'POST',
        body: JSON.stringify(data)
    });
}

/**
 * DELETE request
 */
export async function del(url) {
    return apiRequest(url, { method: 'DELETE' });
}

/**
 * Custom API Error class
 */
export class ApiError extends Error {
    constructor(message, status, data) {
        super(message);
        this.name = 'ApiError';
        this.status = status;
        this.data = data;
    }
}

/**
 * Retry a function with exponential backoff
 * @param {Function} fn - Function to retry
 * @param {number} maxRetries - Maximum number of retries
 * @param {number} delay - Initial delay in ms
 * @returns {Promise<any>} Result of function
 */
export async function retry(fn, maxRetries = 3, delay = 1000) {
    let lastError;
    
    for (let i = 0; i < maxRetries; i++) {
        try {
            return await fn();
        } catch (error) {
            lastError = error;
            
            // Don't retry on client errors (4xx)
            if (error instanceof ApiError && error.status >= 400 && error.status < 500) {
                throw error;
            }
            
            if (i < maxRetries - 1) {
                await new Promise(resolve => setTimeout(resolve, delay * Math.pow(2, i)));
            }
        }
    }
    
    throw lastError;
}
