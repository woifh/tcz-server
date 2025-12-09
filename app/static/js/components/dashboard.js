/**
 * Alpine.js Dashboard Component
 * Manages court availability grid, date navigation, and user reservations
 */

export function dashboard() {
    return {
        // State
        selectedDate: new Date().toISOString().split('T')[0],
        courts: [],
        timeSlots: [],
        availability: {},
        userReservations: [],
        loading: false,
        error: null,
        currentUserId: null,
        
        // Lifecycle
        init() {
            // Get current user ID from the page
            const bookingForSelect = document.getElementById('booking-for');
            if (bookingForSelect) {
                const firstOption = bookingForSelect.querySelector('option');
                this.currentUserId = firstOption ? parseInt(firstOption.value) : null;
            }
            
            this.loadAvailability();
            this.loadUserReservations();
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
                
                // Handle both test data format and production format
                if (data.grid) {
                    this.availability = data;
                    this.courts = data.grid;
                    
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
        
        async loadUserReservations() {
            try {
                const response = await fetch('/reservations/user/upcoming');
                
                if (response.ok) {
                    const data = await response.json();
                    this.userReservations = data.reservations || [];
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
            if (slot.status === 'available') {
                this.openBookingModal(court, time);
            } else if (slot.status === 'reserved' && this.canCancelSlot(slot)) {
                // Handle both test format (reservation) and production format (details)
                const reservation = slot.reservation || slot.details;
                const reservationId = reservation.reservation_id || reservation.id;
                this.cancelReservation(reservationId);
            }
        },
        
        openBookingModal(courtNumber, time) {
            // Trigger Alpine.js booking modal
            if (window.Alpine && window.Alpine.store) {
                const bookingStore = window.Alpine.store('booking');
                if (bookingStore && bookingStore.modalComponent) {
                    bookingStore.modalComponent.open(courtNumber, time, this.selectedDate);
                }
            }
        },
        
        async cancelReservation(reservationId) {
            if (!confirm('Möchten Sie diese Buchung wirklich stornieren?')) {
                return;
            }
            
            try {
                const response = await fetch(`/reservations/${reservationId}`, {
                    method: 'DELETE'
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    this.showSuccess('Buchung erfolgreich storniert');
                    await this.loadAvailability();
                    await this.loadUserReservations();
                } else {
                    this.showError(data.error || 'Fehler beim Stornieren der Buchung');
                }
            } catch (err) {
                console.error('Error cancelling reservation:', err);
                this.showError('Fehler beim Stornieren der Buchung');
            }
        },
        
        getSlotClass(slot) {
            let classes = 'border border-gray-300 px-2 py-4 text-center';
            
            if (slot.status === 'available') {
                classes += ' bg-green-500 text-white cursor-pointer hover:opacity-80';
            } else if (slot.status === 'reserved') {
                // Handle both test format (reservation) and production format (details)
                const reservation = slot.reservation || slot.details;
                
                // Check if short notice
                if (reservation && reservation.is_short_notice) {
                    classes += ' text-white text-xs';
                    classes += ' bg-orange-500'; // Using orange for short notice
                } else {
                    classes += ' bg-red-500 text-white text-xs';
                }
                
                // Add pointer cursor if user can cancel
                if (this.canCancelSlot(slot)) {
                    classes += ' cursor-pointer hover:opacity-80';
                }
            } else if (slot.status === 'blocked') {
                classes += ' bg-gray-400 text-white';
            }
            
            return classes;
        },
        
        canCancelSlot(slot) {
            if (slot.status !== 'reserved') {
                return false;
            }
            
            // Handle both test format (reservation) and production format (details)
            const reservation = slot.reservation || slot.details;
            if (!reservation) {
                return false;
            }
            
            // User can cancel if they booked it or if it's booked for them
            return this.currentUserId && (
                reservation.booked_for_id === this.currentUserId ||
                reservation.booked_by_id === this.currentUserId ||
                reservation.member_id === this.currentUserId
            );
        },
        
        generateTimeSlots() {
            const slots = [];
            for (let hour = 6; hour < 22; hour++) {
                slots.push(`${hour.toString().padStart(2, '0')}:00`);
            }
            return slots;
        },
        
        showSuccess(message) {
            // Use existing toast notification system
            if (typeof window.showSuccess === 'function') {
                window.showSuccess(message);
            } else {
                alert(message);
            }
        },
        
        showError(message) {
            // Use existing toast notification system
            if (typeof window.showError === 'function') {
                window.showError(message);
            } else {
                alert(message);
            }
        }
    };
}
