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
        beforeEach(() => {
            // Set component as authenticated for these tests
            component.isAuthenticated = true;
            // Mock a future time to avoid "past slot" logic
            vi.spyOn(component, 'isSlotInPast').mockReturnValue(false);
        });

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

        it('should not allow any interactions for anonymous users', () => {
            component.isAuthenticated = false;
            const slot = { status: 'available' };
            const openModalSpy = vi.fn();
            component.openBookingModal = openModalSpy;
            
            component.handleSlotClick(1, '10:00', slot);
            expect(openModalSpy).not.toHaveBeenCalled();
        });
    });

    describe('Slot Styling', () => {
        beforeEach(() => {
            // Set component as authenticated for these tests
            component.isAuthenticated = true;
            // Mock a future time to avoid "past slot" logic
            vi.spyOn(component, 'isSlotInPast').mockReturnValue(false);
        });

        it('should return green class for available slot', () => {
            const slot = { status: 'available' };
            const classes = component.getSlotClass(slot, '10:00');
            expect(classes).toContain('bg-green-500');
        });

        it('should return red class for reserved slot', () => {
            const slot = { status: 'reserved' };
            const classes = component.getSlotClass(slot, '10:00');
            expect(classes).toContain('bg-red-500');
        });

        it('should return gray class for blocked slot', () => {
            const slot = { status: 'blocked' };
            const classes = component.getSlotClass(slot, '10:00');
            expect(classes).toContain('bg-gray-400');
        });

        it('should return orange class for short notice reservation (reserved status)', () => {
            const slot = { 
                status: 'reserved',
                reservation: { is_short_notice: true }
            };
            const classes = component.getSlotClass(slot, '10:00');
            expect(classes).toContain('orange');
        });

        it('should return orange class for short notice reservation (short_notice status)', () => {
            const slot = { 
                status: 'short_notice',
                details: { booked_for: 'Test User' }
            };
            const classes = component.getSlotClass(slot, '10:00');
            expect(classes).toContain('bg-orange-500');
        });

        it('should include pointer cursor for available slots when authenticated', () => {
            const slot = { status: 'available' };
            const classes = component.getSlotClass(slot, '10:00');
            expect(classes).toContain('cursor-pointer');
        });

        it('should not include pointer cursor for available slots when anonymous', () => {
            component.isAuthenticated = false;
            const slot = { status: 'available' };
            const classes = component.getSlotClass(slot, '10:00');
            expect(classes).not.toContain('cursor-pointer');
        });

        it('should include pointer cursor for own reservations when authenticated', () => {
            const slot = { 
                status: 'reserved',
                reservation: { id: 1, member_id: 1 }
            };
            component.currentUserId = 1;
            const classes = component.getSlotClass(slot, '10:00');
            expect(classes).toContain('cursor-pointer');
        });

        it('should not include pointer cursor for other reservations', () => {
            const slot = { 
                status: 'reserved',
                reservation: { id: 1, member_id: 2 }
            };
            component.currentUserId = 1;
            const classes = component.getSlotClass(slot, '10:00');
            expect(classes).not.toContain('cursor-pointer');
        });
    });

    describe('Can Cancel Slot', () => {
        beforeEach(() => {
            component.isAuthenticated = true;
        });

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

        it('should return false for any slot when anonymous', () => {
            component.isAuthenticated = false;
            const slot = { 
                status: 'reserved',
                reservation: { member_id: 1 }
            };
            component.currentUserId = 1;
            expect(component.canCancelSlot(slot)).toBe(false);
        });
    });

    describe('Authentication Detection', () => {
        beforeEach(() => {
            // Clear any global authentication state
            delete window.isAuthenticated;
        });

        it('should default to authenticated when no global variable is set', () => {
            const newComponent = createComponent(dashboard);
            newComponent.init();
            expect(newComponent.isAuthenticated).toBe(true);
        });

        it('should detect anonymous user from global variable', () => {
            window.isAuthenticated = false;
            const newComponent = createComponent(dashboard);
            newComponent.init();
            expect(newComponent.isAuthenticated).toBe(false);
        });

        it('should detect authenticated user from global variable', () => {
            window.isAuthenticated = true;
            const newComponent = createComponent(dashboard);
            newComponent.init();
            expect(newComponent.isAuthenticated).toBe(true);
        });

        it('should not load user reservations for anonymous users', () => {
            window.isAuthenticated = false;
            const newComponent = createComponent(dashboard);
            const loadReservationsSpy = vi.spyOn(newComponent, 'loadUserReservations');
            newComponent.init();
            expect(loadReservationsSpy).not.toHaveBeenCalled();
        });

        it('should load user reservations for authenticated users', () => {
            window.isAuthenticated = true;
            const newComponent = createComponent(dashboard);
            const loadReservationsSpy = vi.spyOn(newComponent, 'loadUserReservations');
            newComponent.init();
            expect(loadReservationsSpy).toHaveBeenCalled();
        });
    });

    describe('Slot Content for Anonymous Users', () => {
        it('should show member details for authenticated users', () => {
            component.isAuthenticated = true;
            const slot = { 
                status: 'reserved',
                reservation: { booked_for: 'John Doe', booked_by: 'Jane Smith' }
            };
            const content = component.getSlotContent(slot, '10:00');
            expect(content).toContain('John Doe');
            expect(content).toContain('Jane Smith');
        });

        it('should hide member details for anonymous users', () => {
            component.isAuthenticated = false;
            const slot = { 
                status: 'reserved',
                reservation: { booked_for: 'John Doe', booked_by: 'Jane Smith' }
            };
            const content = component.getSlotContent(slot, '10:00');
            expect(content).toBe('Gebucht');
            expect(content).not.toContain('John Doe');
            expect(content).not.toContain('Jane Smith');
        });

        it('should hide short notice member details for anonymous users', () => {
            component.isAuthenticated = false;
            const slot = { 
                status: 'short_notice',
                reservation: { booked_for: 'John Doe', booked_by: 'Jane Smith' }
            };
            const content = component.getSlotContent(slot, '10:00');
            expect(content).toBe('Gebucht');
            expect(content).not.toContain('John Doe');
            expect(content).not.toContain('Jane Smith');
        });

        it('should show block details for both authenticated and anonymous users', () => {
            component.isAuthenticated = false;
            const slot = { 
                status: 'blocked',
                details: { reason: 'Maintenance', details: 'Court resurfacing' }
            };
            const content = component.getSlotContent(slot, '10:00');
            expect(content).toContain('Maintenance');
            expect(content).toContain('Court resurfacing');
        });
    });
});
