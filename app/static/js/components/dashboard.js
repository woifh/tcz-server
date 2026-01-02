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
        
        async loadUserReservations() {
            try {
                const response = await fetch('/reservations/?format=json');
                
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
            console.log('Slot clicked:', { court, time, slot });
            
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
        
        getSlotClass(slot, time) {
            let classes = 'border border-gray-300 px-2 py-4 text-center';
            
            // Debug logging
            console.log('getSlotClass called with slot:', slot);
            
            // Check if slot is in the past
            const isPast = this.isSlotInPast(time);
            
            if (slot.status === 'available') {
                if (isPast) {
                    classes += ' bg-gray-200 text-gray-500 cursor-not-allowed';
                } else {
                    classes += ' bg-green-500 text-white cursor-pointer hover:opacity-80';
                }
            } else if (slot.status === 'short_notice') {
                // Short notice bookings get orange background
                classes += ' bg-orange-500 text-white text-xs short-notice-booking';
                console.log('Short-notice slot detected, applying classes:', classes);
                
                // Add pointer cursor if user can cancel and not in past
                if (!isPast && this.canCancelSlot(slot)) {
                    classes += ' cursor-pointer hover:opacity-80';
                } else if (isPast) {
                    classes += ' cursor-not-allowed opacity-75';
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
                
                // Add pointer cursor if user can cancel and not in past
                if (!isPast && this.canCancelSlot(slot)) {
                    classes += ' cursor-pointer hover:opacity-80';
                } else if (isPast) {
                    classes += ' cursor-not-allowed opacity-75';
                }
            } else if (slot.status === 'blocked') {
                classes += ' bg-gray-400 text-white text-xs min-h-16';
                if (isPast) {
                    classes += ' cursor-not-allowed opacity-75';
                }
            }
            
            console.log('Final classes for slot:', classes);
            return classes;
        },
        
        canCancelSlot(slot) {
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
            for (let hour = 6; hour < 22; hour++) {
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
                if (reservation) {
                    return `Gebucht für ${reservation.booked_for}<br>von ${reservation.booked_by}`;
                }
                return 'Kurzfristig gebucht';
            } else if (slot.status === 'reserved') {
                const reservation = slot.reservation || slot.details;
                if (reservation) {
                    return `Gebucht für ${reservation.booked_for}<br>von ${reservation.booked_by}`;
                }
                return 'Gebucht';
            } else if (slot.status === 'blocked') {
                const blockDetails = slot.details;
                console.log('Blocked slot details:', blockDetails); // Debug log
                if (blockDetails && blockDetails.reason) {
                    let content = blockDetails.reason;
                    if (blockDetails.sub_reason && blockDetails.sub_reason.trim()) {
                        console.log('Adding sub-reason:', blockDetails.sub_reason); // Debug log
                        content += `<br><span style="font-size: 0.7em; opacity: 0.9;">${blockDetails.sub_reason}</span>`;
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
        }
    };
}
