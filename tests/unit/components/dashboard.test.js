/**
 * Unit tests for Alpine.js dashboard component
 * Feature: alpine-tdd-migration
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { 
    createComponent, 
    mockApiSuccess, 
    mockApiError,
    createMockDate,
    createMockAvailability 
} from '../../utils/alpine-test-utils.js';

// Import the dashboard component (will be created)
import { dashboard } from '../../../app/static/js/components/dashboard.js';

describe('Dashboard Component', () => {
    let component;

    beforeEach(() => {
        component = createComponent(dashboard);
        vi.clearAllMocks();
    });

    describe('Initialization', () => {
        it('should initialize with today\'s date', () => {
            const today = new Date().toISOString().split('T')[0];
            expect(component.selectedDate).toBe(today);
        });

        it('should initialize with empty courts array', () => {
            expect(component.courts).toEqual([]);
        });

        it('should initialize with empty timeSlots array', () => {
            expect(component.timeSlots).toEqual([]);
        });

        it('should initialize with empty availability object', () => {
            expect(component.availability).toEqual({});
        });

        it('should initialize with loading false', () => {
            expect(component.loading).toBe(false);
        });

        it('should initialize with null error', () => {
            expect(component.error).toBeNull();
        });
    });

    describe('Date Navigation', () => {
        it('should change date by positive offset', () => {
            component.selectedDate = '2025-01-15';
            component.changeDate(1);
            expect(component.selectedDate).toBe('2025-01-16');
        });

        it('should change date by negative offset', () => {
            component.selectedDate = '2025-01-15';
            component.changeDate(-1);
            expect(component.selectedDate).toBe('2025-01-14');
        });

        it('should handle month boundary when incrementing', () => {
            component.selectedDate = '2025-01-31';
            component.changeDate(1);
            expect(component.selectedDate).toBe('2025-02-01');
        });

        it('should handle month boundary when decrementing', () => {
            component.selectedDate = '2025-02-01';
            component.changeDate(-1);
            expect(component.selectedDate).toBe('2025-01-31');
        });

        it('should go to today when goToToday is called', () => {
            component.selectedDate = '2025-01-15';
            component.goToToday();
            const today = new Date().toISOString().split('T')[0];
            expect(component.selectedDate).toBe(today);
        });

        it('should call loadAvailability after changing date', async () => {
            const loadSpy = vi.spyOn(component, 'loadAvailability');
            component.changeDate(1);
            expect(loadSpy).toHaveBeenCalled();
        });

        it('should call loadAvailability after goToToday', async () => {
            const loadSpy = vi.spyOn(component, 'loadAvailability');
            component.goToToday();
            expect(loadSpy).toHaveBeenCalled();
        });
    });

    describe('Load Availability', () => {
        it('should set loading to true while loading', async () => {
            mockApiSuccess(createMockAvailability(createMockDate()));
            
            const loadPromise = component.loadAvailability();
            expect(component.loading).toBe(true);
            
            await loadPromise;
        });

        it('should set loading to false after successful load', async () => {
            mockApiSuccess(createMockAvailability(createMockDate()));
            
            await component.loadAvailability();
            expect(component.loading).toBe(false);
        });

        it('should populate availability data on successful load', async () => {
            const mockData = createMockAvailability(createMockDate());
            mockApiSuccess(mockData);
            
            await component.loadAvailability();
            expect(component.availability).toEqual(mockData);
        });

        it('should set error on failed load', async () => {
            mockApiError(500, 'Server error');
            
            await component.loadAvailability();
            expect(component.error).toBeTruthy();
            expect(component.loading).toBe(false);
        });

        it('should clear previous error on new load', async () => {
            component.error = 'Previous error';
            mockApiSuccess(createMockAvailability(createMockDate()));
            
            await component.loadAvailability();
            expect(component.error).toBeNull();
        });

        it('should fetch availability for selected date', async () => {
            component.selectedDate = '2025-01-15';
            mockApiSuccess(createMockAvailability('2025-01-15'));
            
            await component.loadAvailability();
            
            expect(global.fetch).toHaveBeenCalledWith(
                expect.stringContaining('date=2025-01-15')
            );
        });
    });

    describe('Slot Click Handling', () => {
        it('should open booking modal for available slot', () => {
            const slot = { status: 'available' };
            const openModalSpy = vi.fn();
            component.openBookingModal = openModalSpy;
            
            component.handleSlotClick(1, '10:00', slot);
            expect(openModalSpy).toHaveBeenCalledWith(1, '10:00');
        });

        it('should not open modal for blocked slot', () => {
            const slot = { status: 'blocked' };
            const openModalSpy = vi.fn();
            component.openBookingModal = openModalSpy;
            
            component.handleSlotClick(1, '10:00', slot);
            expect(openModalSpy).not.toHaveBeenCalled();
        });

        it('should handle cancellation for own reservation', () => {
            const slot = { 
                status: 'reserved',
                reservation: { id: 1, member_id: 1 }
            };
            component.currentUserId = 1;
            const cancelSpy = vi.fn();
            component.cancelReservation = cancelSpy;
            
            component.handleSlotClick(1, '10:00', slot);
            expect(cancelSpy).toHaveBeenCalledWith(1);
        });

        it('should not handle cancellation for other user reservation', () => {
            const slot = { 
                status: 'reserved',
                reservation: { id: 1, member_id: 2 }
            };
            component.currentUserId = 1;
            const cancelSpy = vi.fn();
            component.cancelReservation = cancelSpy;
            
            component.handleSlotClick(1, '10:00', slot);
            expect(cancelSpy).not.toHaveBeenCalled();
        });
    });

    describe('Slot Styling', () => {
        it('should return green class for available slot', () => {
            const slot = { status: 'available' };
            const classes = component.getSlotClass(slot);
            expect(classes).toContain('bg-green-500');
        });

        it('should return red class for reserved slot', () => {
            const slot = { status: 'reserved' };
            const classes = component.getSlotClass(slot);
            expect(classes).toContain('bg-red-500');
        });

        it('should return gray class for blocked slot', () => {
            const slot = { status: 'blocked' };
            const classes = component.getSlotClass(slot);
            expect(classes).toContain('bg-gray-400');
        });

        it('should return orange class for short notice reservation', () => {
            const slot = { 
                status: 'reserved',
                reservation: { is_short_notice: true }
            };
            const classes = component.getSlotClass(slot);
            expect(classes).toContain('orange');
        });

        it('should include pointer cursor for available slots', () => {
            const slot = { status: 'available' };
            const classes = component.getSlotClass(slot);
            expect(classes).toContain('cursor-pointer');
        });

        it('should include pointer cursor for own reservations', () => {
            const slot = { 
                status: 'reserved',
                reservation: { id: 1, member_id: 1 }
            };
            component.currentUserId = 1;
            const classes = component.getSlotClass(slot);
            expect(classes).toContain('cursor-pointer');
        });

        it('should not include pointer cursor for other reservations', () => {
            const slot = { 
                status: 'reserved',
                reservation: { id: 1, member_id: 2 }
            };
            component.currentUserId = 1;
            const classes = component.getSlotClass(slot);
            expect(classes).not.toContain('cursor-pointer');
        });
    });

    describe('Can Cancel Slot', () => {
        it('should return true for own reservation', () => {
            const slot = { 
                status: 'reserved',
                reservation: { member_id: 1 }
            };
            component.currentUserId = 1;
            expect(component.canCancelSlot(slot)).toBe(true);
        });

        it('should return false for other user reservation', () => {
            const slot = { 
                status: 'reserved',
                reservation: { member_id: 2 }
            };
            component.currentUserId = 1;
            expect(component.canCancelSlot(slot)).toBe(false);
        });

        it('should return false for available slot', () => {
            const slot = { status: 'available' };
            component.currentUserId = 1;
            expect(component.canCancelSlot(slot)).toBe(false);
        });

        it('should return false for blocked slot', () => {
            const slot = { status: 'blocked' };
            component.currentUserId = 1;
            expect(component.canCancelSlot(slot)).toBe(false);
        });
    });
});
