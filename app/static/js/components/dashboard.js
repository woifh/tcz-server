/**
 * Alpine.js Dashboard Component
 * Manages court availability grid, date navigation, and user reservations
 */

// Track which component instances have been initialized to prevent double init
const initializedComponents = new WeakSet();

export function dashboard() {
    return {
        // State
        selectedDate: new Date().toISOString().split('T')[0],
        courts: [],
        timeSlots: [],
        availability: {},
        userReservations: [],
        bookingsForOthers: [],
        loading: false,
        error: null,
        currentUserId: null,
        isAuthenticated: true, // Default to authenticated, will be overridden for anonymous users
        
        // Lifecycle
        init() {
            // Prevent double initialization (e.g., from Alpine reinit or x-init calling twice)
            if (initializedComponents.has(this.$el)) return;
            initializedComponents.add(this.$el);

            // Detect authentication status from global variable or DOM
            this.isAuthenticated = window.isAuthenticated !== undefined ? window.isAuthenticated : true;

            // Get current user ID from the page (only for authenticated users)
            if (this.isAuthenticated) {
                const bookingForSelect = document.getElementById('booking-for');
                if (bookingForSelect) {
                    const firstOption = bookingForSelect.querySelector('option');
                    this.currentUserId = firstOption ? parseInt(firstOption.value) : null;
                }
            }

            // Load initial availability
            this.loadAvailability();

            // Only load user reservations for authenticated users
            if (this.isAuthenticated) {
                this.loadUserReservations();
            }
        },
        
        // Methods
        async loadAvailability() {
            this.loading = true;
            this.error = null;
            
            try {
                const response = await fetch(`/courts/availability?date=${this.selectedDate}`);
                
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                const data = await response.json();
                console.log('Availability data received:', data);
                
                // Handle both test data format and production format
                if (data.grid) {
                    this.availability = data;
                    this.courts = data.grid;
                    
                    // Debug: Check for short-notice bookings
                    data.grid.forEach((court, courtIdx) => {
                        court.slots.forEach((slot, slotIdx) => {
                            if (slot.status === 'short_notice') {
                                console.log(`Short-notice booking found: Court ${courtIdx + 1}, Slot ${slotIdx} (${6 + slotIdx}:00)`, slot);
                            }
                        });
                    });
                    
                    // Generate time slots if not already set
                    if (this.timeSlots.length === 0) {
                        this.timeSlots = this.generateTimeSlots();
                    }
                } else if (data.slots) {
                    // Test data format
                    this.availability = data;
                    this.courts = data.slots;
                    
                    if (this.timeSlots.length === 0) {
                        this.timeSlots = this.generateTimeSlots();
                    }
                } else if (data.error) {
                    this.error = data.error;
                }
            } catch (err) {
                console.error('Error loading availability:', err);
                this.error = 'Fehler beim Laden der Verfügbarkeit';
            } finally {
                this.loading = false;
            }
        },

        async refreshAvailability() {
            // Refresh availability without showing loading state (prevents table flicker)
            try {
                const response = await fetch(`/courts/availability?date=${this.selectedDate}`);
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                const data = await response.json();

                // Handle production format with grid
                const newCourts = data.grid || data.slots || [];

                // Update only changed slots, preserving table structure
                newCourts.forEach((newCourt, courtIndex) => {
                    if (this.courts[courtIndex]) {
                        newCourt.slots.forEach((newSlot, slotIndex) => {
                            const oldSlot = this.courts[courtIndex].slots[slotIndex];
                            if (oldSlot && this.slotHasChanged(oldSlot, newSlot)) {
                                Object.assign(this.courts[courtIndex].slots[slotIndex], newSlot);
                            }
                        });
                    }
                });
            } catch (err) {
                console.error('Error refreshing availability:', err);
            }
        },

        slotHasChanged(oldSlot, newSlot) {
            return oldSlot.status !== newSlot.status ||
                   oldSlot.reservation_id !== newSlot.reservation_id ||
                   JSON.stringify(oldSlot.details) !== JSON.stringify(newSlot.details);
        },

        async loadUserReservations() {
            try {
                const response = await fetch('/reservations/?format=json');

                if (response.ok) {
                    const data = await response.json();
                    const allReservations = data.reservations || [];

                    // Split reservations: my own vs bookings I made for others
                    // userReservations: where I am the booked_for person (counts toward my limits)
                    // bookingsForOthers: where I booked for someone else
                    this.userReservations = allReservations.filter(r => r.booked_for_id === this.currentUserId);
                    this.bookingsForOthers = allReservations.filter(r =>
                        r.booked_by_id === this.currentUserId && r.booked_for_id !== this.currentUserId
                    );
                }
            } catch (err) {
                console.error('Error loading user reservations:', err);
            }
        },
        
        changeDate(offset) {
            const date = new Date(this.selectedDate);
            date.setDate(date.getDate() + offset);
            this.selectedDate = date.toISOString().split('T')[0];
            this.loadAvailability();
        },
        
        goToToday() {
            this.selectedDate = new Date().toISOString().split('T')[0];
            this.loadAvailability();
        },
        
        handleSlotClick(court, time, slot) {
            console.log('Slot clicked:', { court, time, slot });
            
            // Don't allow any interactions for anonymous users
            if (!this.isAuthenticated) {
                console.log('Anonymous user - no slot interactions allowed');
                return;
            }
            
            // Don't allow clicking on past time slots
            if (this.isSlotInPast(time)) {
                console.log('Slot is in the past, ignoring click');
                return;
            }
            
            if (slot.status === 'available') {
                console.log('Opening booking modal for available slot');
                this.openBookingModal(court, time);
            } else if ((slot.status === 'reserved' || slot.status === 'short_notice') && this.canCancelSlot(slot)) {
                console.log('Cancelling reservation');
                // Handle both test format (reservation) and production format (details)
                const reservation = slot.reservation || slot.details;
                const reservationId = reservation.reservation_id || reservation.id;
                this.cancelReservation(reservationId);
            }
        },
        
        openBookingModal(courtNumber, time) {
            // Find the booking modal Alpine component and open it
            const modalEl = document.querySelector('[x-data*="bookingModal"]');
            if (modalEl && window.Alpine) {
                try {
                    const modalComponent = window.Alpine.$data(modalEl);
                    if (modalComponent && typeof modalComponent.open === 'function') {
                        modalComponent.open(courtNumber, time, this.selectedDate);
                    }
                } catch (e) {
                    console.error('Error opening booking modal:', e);
                }
            }
        },
        
        async cancelReservation(reservationId) {
            // Keep confirmation dialog for cancellation request
            if (!confirm('Möchten Sie diese Buchung wirklich stornieren?')) {
                return;
            }
            
            try {
                const response = await fetch(`/reservations/${reservationId}`, {
                    method: 'DELETE'
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    // Show success as toast message (not dialog)
                    this.showSuccess('Buchung erfolgreich storniert');
                    await this.refreshAvailability();
                    await this.loadUserReservations();
                } else {
                    this.showError(data.error || 'Fehler beim Stornieren der Buchung');
                }
            } catch (err) {
                console.error('Error cancelling reservation:', err);
                this.showError('Fehler beim Stornieren der Buchung');
            }
        },
        
        getSlotClass(slot, time) {
            let classes = 'border border-gray-300 px-2 py-4 text-center';
            
            // Debug logging
            console.log('getSlotClass called with slot:', slot);
            
            // Check if slot is in the past
            const isPast = this.isSlotInPast(time);
            
            if (slot.status === 'available') {
                if (isPast) {
                    classes += ' bg-gray-200 text-gray-500';
                } else {
                    classes += ' bg-green-500 text-white';
                    // Only add interactive styles for authenticated users
                    if (this.isAuthenticated) {
                        classes += ' cursor-pointer hover:opacity-80';
                    }
                }
            } else if (slot.status === 'short_notice') {
                // Short notice bookings get orange background
                classes += ' bg-orange-500 text-white text-xs short-notice-booking';
                console.log('Short-notice slot detected, applying classes:', classes);

                // Add pointer cursor if user can cancel and not in past (authenticated users only)
                if (!isPast && this.isAuthenticated && this.canCancelSlot(slot)) {
                    classes += ' cursor-pointer hover:opacity-80';
                } else if (isPast) {
                    classes += ' opacity-75';
                }
            } else if (slot.status === 'reserved') {
                // Handle both test format (reservation) and production format (details)
                const reservation = slot.reservation || slot.details;
                
                // Check if short notice (fallback for different data formats)
                if (reservation && reservation.is_short_notice) {
                    classes += ' bg-orange-500 text-white text-xs short-notice-booking';
                    console.log('Reserved slot with short notice detected, applying classes:', classes);
                } else {
                    classes += ' bg-red-500 text-white text-xs';
                }

                // Add pointer cursor if user can cancel and not in past (authenticated users only)
                if (!isPast && this.isAuthenticated && this.canCancelSlot(slot)) {
                    classes += ' cursor-pointer hover:opacity-80';
                } else if (isPast) {
                    classes += ' opacity-75';
                }
            } else if (slot.status === 'blocked') {
                classes += ' bg-gray-400 text-white text-xs min-h-16';
                if (isPast) {
                    classes += ' opacity-75';
                }
            }
            
            console.log('Final classes for slot:', classes);
            return classes;
        },
        
        canCancelSlot(slot) {
            // Anonymous users cannot cancel any slots
            if (!this.isAuthenticated) {
                return false;
            }
            
            if (slot.status !== 'reserved' && slot.status !== 'short_notice') {
                return false;
            }
            
            // Handle both test format (reservation) and production format (details)
            const reservation = slot.reservation || slot.details;
            if (!reservation) {
                return false;
            }
            
            // Short notice bookings cannot be cancelled (per business rules)
            if (slot.status === 'short_notice' || reservation.is_short_notice) {
                return false;
            }
            
            // User can cancel if they booked it or if it's booked for them
            return this.currentUserId && (
                reservation.booked_for_id === this.currentUserId ||
                reservation.booked_by_id === this.currentUserId ||
                reservation.member_id === this.currentUserId
            );
        },
        
        isSlotInPast(time) {
            const now = new Date();
            const today = now.toISOString().split('T')[0];
            
            // If selected date is before today, all slots are in the past
            if (this.selectedDate < today) {
                return true;
            }
            
            // If selected date is after today, no slots are in the past
            if (this.selectedDate > today) {
                return false;
            }
            
            // If selected date is today, check the time
            const currentHour = now.getHours();
            const [slotHour, slotMinute] = time.split(':').map(Number);
            
            // Slot is in the past only if it's before current hour
            // Current hour is still bookable as short notice booking
            return slotHour < currentHour;
        },
        
        generateTimeSlots() {
            const slots = [];
            for (let hour = 8; hour < 22; hour++) {
                slots.push(`${hour.toString().padStart(2, '0')}:00`);
            }
            return slots;
        },
        
        showSuccess(message) {
            // Use existing toast notification system
            if (typeof window.showToast === 'function') {
                window.showToast(message, 'success');
            } else if (typeof window.showSuccess === 'function') {
                window.showSuccess(message);
            } else {
                alert(message);
            }
        },
        
        showError(message) {
            // Use existing toast notification system
            if (typeof window.showToast === 'function') {
                window.showToast(message, 'error');
            } else if (typeof window.showError === 'function') {
                window.showError(message);
            } else {
                alert(message);
            }
        },
        
        // Template helper methods
        getSlot(courtIndex, time) {
            if (!this.courts || !this.courts[courtIndex] || !this.courts[courtIndex].slots) {
                return { status: 'available' };
            }
            
            const timeIndex = this.timeSlots.indexOf(time);
            return this.courts[courtIndex].slots[timeIndex] || { status: 'available' };
        },
        
        getSlotContent(slot, time) {
            if (slot.status === 'available') {
                if (this.isSlotInPast(time)) {
                    return 'Vergangen';
                }
                return 'Frei';
            } else if (slot.status === 'short_notice') {
                const reservation = slot.reservation || slot.details;
                if (reservation && this.isAuthenticated) {
                    // Show member details only to authenticated users
                    // Simplify display for own bookings (don't show redundant "von" info)
                    if (reservation.booked_for_id === reservation.booked_by_id) {
                        return reservation.booked_for;
                    }
                    return `${reservation.booked_for}<br>(von ${reservation.booked_by})`;
                }
                return 'Gebucht'; // Anonymous users see generic "Gebucht"
            } else if (slot.status === 'reserved') {
                const reservation = slot.reservation || slot.details;
                if (reservation && this.isAuthenticated) {
                    // Show member details only to authenticated users
                    // Simplify display for own bookings (don't show redundant "von" info)
                    if (reservation.booked_for_id === reservation.booked_by_id) {
                        return reservation.booked_for;
                    }
                    return `${reservation.booked_for}<br>(von ${reservation.booked_by})`;
                }
                return 'Gebucht'; // Anonymous users see generic "Gebucht"
            } else if (slot.status === 'blocked') {
                const blockDetails = slot.details;
                console.log('Blocked slot details:', blockDetails); // Debug log
                if (blockDetails && blockDetails.reason) {
                    let content = blockDetails.reason;
                    if (blockDetails.details && blockDetails.details.trim()) {
                        console.log('Adding details:', blockDetails.details); // Debug log
                        content += `<br><span style="font-size: 0.7em; opacity: 0.9;">${blockDetails.details}</span>`;
                    }
                    console.log('Final blocked content:', content); // Debug log
                    return content;
                }
                return 'Gesperrt';
            }
            return '';
        },
        
        formatDate(dateStr) {
            if (!dateStr) return '';
            const [year, month, day] = dateStr.split('-');
            return `${day}.${month}.${year}`;
        },
        
        // Availability calculation methods
        getAvailableSlots() {
            if (!this.userReservations) return 2;
            
            // Count regular (non-short-notice) active booking sessions
            const regularBookings = this.userReservations.filter(r => !r.is_short_notice);
            return Math.max(0, 2 - regularBookings.length);
        },
        
        getShortNoticeSlots() {
            if (!this.userReservations) return 1;
            
            // Count short notice active booking sessions
            const shortNoticeBookings = this.userReservations.filter(r => r.is_short_notice);
            return Math.max(0, 1 - shortNoticeBookings.length);
        }
    };
}
