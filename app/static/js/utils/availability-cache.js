/**
 * Availability Cache Module
 * Memory-based cache for court availability data with TTL
 */

const CACHE_TTL_MS = 30 * 1000; // 30 seconds

class AvailabilityCache {
    constructor() {
        // Map<dateString, { data: Object, fetchedAt: number }>
        this.cache = new Map();
    }

    /**
     * Get cached data for a date
     * @param {string} dateStr - Date in YYYY-MM-DD format
     * @returns {{ data: Object, isStale: boolean } | null}
     */
    get(dateStr) {
        const entry = this.cache.get(dateStr);
        if (!entry) return null;

        const age = Date.now() - entry.fetchedAt;
        return {
            data: entry.data,
            isStale: age > CACHE_TTL_MS,
        };
    }

    /**
     * Store data for a date
     * @param {string} dateStr - Date in YYYY-MM-DD format
     * @param {Object} data - Availability data for this date
     */
    set(dateStr, data) {
        this.cache.set(dateStr, {
            data,
            fetchedAt: Date.now(),
        });
    }

    /**
     * Check if date is in cache (regardless of staleness)
     * @param {string} dateStr - Date in YYYY-MM-DD format
     * @returns {boolean}
     */
    has(dateStr) {
        return this.cache.has(dateStr);
    }

    /**
     * Clear all cached data
     */
    clear() {
        this.cache.clear();
    }

    /**
     * Get cache size for debugging
     * @returns {number}
     */
    get size() {
        return this.cache.size;
    }
}

// Singleton instance
export const availabilityCache = new AvailabilityCache();
