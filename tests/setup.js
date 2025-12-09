/**
 * Test setup file for Vitest
 * This file runs before all tests
 */

import { beforeAll, afterEach, vi } from 'vitest';

// Mock Alpine.js for testing
global.Alpine = {
    data: vi.fn((name, callback) => callback),
    store: vi.fn((name, data) => data),
    start: vi.fn(),
};

// Setup DOM environment
beforeAll(() => {
    // Add any global setup here
});

// Cleanup after each test
afterEach(() => {
    vi.clearAllMocks();
});

// Mock fetch for API calls
global.fetch = vi.fn();
