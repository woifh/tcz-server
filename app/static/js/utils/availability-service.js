/**
 * Availability Service Module
 * Handles fetching availability data with caching and prefetching
 */

import { availabilityCache } from './availability-cache.js';
import { getToday, addDays } from './date-utils.js';

const PREFETCH_DAYS = 14;
const PREFETCH_BUFFER = 3; // Prefetch when within 3 days of cache edge

class AvailabilityService {
    constructor() {
        this.baseUrl = '/api/courts/availability';
        this.pendingFetches = new Set(); // Track in-flight requests
    }

    /**
     * Get availability for a single date (cache-first)
     * @param {string} dateStr - Date in YYYY-MM-DD format
     * @returns {Promise<{ data: Object, fromCache: boolean }>}
     */
    async getForDate(dateStr) {
        const cached = availabilityCache.get(dateStr);

        if (cached && !cached.isStale) {
            return { data: cached.data, fromCache: true };
        }

        if (cached && cached.isStale) {
            // Return stale data immediately, refresh in background
            this._refreshInBackground(dateStr);
            return { data: cached.data, fromCache: true };
        }

        // Not in cache - fetch synchronously
        const data = await this._fetchSingle(dateStr);
        return { data, fromCache: false };
    }

    /**
     * Initial load - fetch range starting from today
     * @returns {Promise<void>}
     */
    async initialLoad() {
        const today = getToday();
        try {
            await this._fetchRange(today, PREFETCH_DAYS);
        } catch (err) {
            console.warn('Range fetch failed, falling back to single date:', err);
            // Fall back to single date fetch
            await this._fetchSingle(today);
        }
    }

    /**
     * Prefetch dates around a center date if near cache edge
     * @param {string} centerDate - Date in YYYY-MM-DD format
     */
    async prefetchAround(centerDate) {
        // Check if we're near the edge of cached dates
        const checkAhead = addDays(centerDate, PREFETCH_BUFFER);
        const checkBehind = addDays(centerDate, -PREFETCH_BUFFER);

        const needsAhead = !availabilityCache.has(checkAhead);
        const needsBehind = !availabilityCache.has(checkBehind);

        if (needsAhead) {
            // Prefetch 7 days ahead in background
            const startAhead = addDays(centerDate, 1);
            this._fetchRange(startAhead, 7).catch((err) => {
                console.warn('Prefetch ahead failed:', err);
            });
        }

        if (needsBehind) {
            // Prefetch 7 days behind in background
            const startBehind = addDays(centerDate, -7);
            this._fetchRange(startBehind, 7).catch((err) => {
                console.warn('Prefetch behind failed:', err);
            });
        }
    }

    /**
     * Fetch a single date from the API
     * @param {string} dateStr - Date in YYYY-MM-DD format
     * @returns {Promise<Object>}
     */
    async _fetchSingle(dateStr) {
        const response = await fetch(`${this.baseUrl}?date=${dateStr}`);
        if (!response.ok) {
            throw new Error(`Failed to fetch availability: ${response.status}`);
        }
        const data = await response.json();
        availabilityCache.set(dateStr, data);
        return data;
    }

    /**
     * Fetch a date range from the API
     * @param {string} startDate - Start date in YYYY-MM-DD format
     * @param {number} numDays - Number of days to fetch
     * @returns {Promise<void>}
     */
    async _fetchRange(startDate, numDays) {
        const cacheKey = `${startDate}-${numDays}`;

        // Prevent duplicate fetches for same range
        if (this.pendingFetches.has(cacheKey)) {
            return;
        }

        this.pendingFetches.add(cacheKey);

        try {
            const response = await fetch(
                `${this.baseUrl}/range?start=${startDate}&days=${numDays}`
            );

            if (!response.ok) {
                throw new Error(`Failed to fetch availability range: ${response.status}`);
            }

            const data = await response.json();

            // Store each day in cache
            if (data.days) {
                for (const [dateStr, dayData] of Object.entries(data.days)) {
                    availabilityCache.set(dateStr, dayData);
                }
            }
        } finally {
            this.pendingFetches.delete(cacheKey);
        }
    }

    /**
     * Refresh a date in the background (fire and forget)
     * @param {string} dateStr - Date in YYYY-MM-DD format
     */
    async _refreshInBackground(dateStr) {
        try {
            await this._fetchSingle(dateStr);
        } catch (err) {
            console.warn('Background refresh failed:', err);
        }
    }

    /**
     * Force fetch fresh data for a date (bypasses cache check)
     * @param {string} dateStr - Date in YYYY-MM-DD format
     * @returns {Promise<Object>}
     */
    async fetchFresh(dateStr) {
        return await this._fetchSingle(dateStr);
    }

    /**
     * Clear the cache
     */
    clearCache() {
        availabilityCache.clear();
    }
}

// Singleton instance
export const availabilityService = new AvailabilityService();

// Re-export cache for direct access in dashboard
export { availabilityCache };
