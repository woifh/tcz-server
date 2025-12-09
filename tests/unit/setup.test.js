/**
 * Test to verify testing infrastructure is set up correctly
 */

import { describe, it, expect } from 'vitest';

describe('Testing Infrastructure', () => {
    it('should run tests successfully', () => {
        expect(true).toBe(true);
    });

    it('should have access to global fetch mock', () => {
        expect(global.fetch).toBeDefined();
    });

    it('should have access to Alpine mock', () => {
        expect(global.Alpine).toBeDefined();
        expect(global.Alpine.data).toBeDefined();
        expect(global.Alpine.store).toBeDefined();
    });
});
