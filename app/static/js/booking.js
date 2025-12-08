/**
 * Booking form and reservation management
 */

import { getEndTime, showSuccess, showError } from './utils.js';
import { loadAvailability } from './grid.js';
import { loadUserReservations } from './reservations.js';

let selectedSlot = null;
let currentDate = null;

/**
 * Initialize booking module
 */
export function initBooking(date) {
    currentDate = date;
    
    const bookingForm = document.getElementById('booking-form');
    if (bookingForm) {
        bookingForm.addEventListener('submit', handleBookingSubmit);
    }
    
    // Load favourites for booking dropdown
    loadFavourites();
}

/**
 * Update current date
 */
export function setCurrentDate(date) {
    currentDate = date;
}

/**
 * Open booking modal with pre-filled data
 * Bridge function to Alpine.js component
 */
export function openBookingModal(courtNumber, time) {
    const dateSelector = document.getElementById('date-selector');
    const currentDate = dateSelector ? dateSelector.value : new Date().toISOString().split('T')[0];
    
    // Try Alpine store first
    if (window.Alpine && window.Alpine.store) {
        const bookingStore = window.Alpine.store('booking');
        if (bookingStore && bookingStore.modalComponent && typeof bookingStore.modalComponent.open === 'function') {
            bookingStore.modalComponent.open(courtNumber, time, currentDate);
            return;
        }
    }
    
    // Fallback: try to find Alpine component directly
    if (window.Alpine) {
        const modalEl = document.querySelector('[x-data*="bookingModal"]');
        if (modalEl) {
            try {
                const component = window.Alpine.$data(modalEl);
                if (component && typeof component.open === 'function') {
                    component.open(courtNumber, time, currentDate);
                    return;
                }
            } catch (e) {
                console.error('Error accessing Alpine component:', e);
            }
        }
    }
    
    console.error('Booking modal component not available. Alpine may not be initialized yet.');
}

/**
 * Close booking modal
 * Bridge function to Alpine.js component
 */
export function closeBookingModal() {
    // Try Alpine store first
    if (window.Alpine && window.Alpine.store) {
        const bookingStore = window.Alpine.store('booking');
        if (bookingStore && bookingStore.modalComponent && typeof bookingStore.modalComponent.close === 'function') {
            bookingStore.modalComponent.close();
            return;
        }
    }
    
    // Fallback: try to find Alpine component directly
    if (window.Alpine) {
        const modalEl = document.querySelector('[x-data*="bookingModal"]');
        if (modalEl) {
            try {
                const component = window.Alpine.$data(modalEl);
                if (component && typeof component.close === 'function') {
                    component.close();
                    return;
                }
            } catch (e) {
                console.error('Error accessing Alpine component:', e);
            }
        }
    }
}

/**
 * Handle booking form submission
 */
async function handleBookingSubmit(event) {
    event.preventDefault();
    
    if (!selectedSlot) return;
    
    const bookedForId = document.getElementById('booking-for').value;
    const courtId = selectedSlot.courtNumber;
    
    const bookingData = {
        court_id: courtId,
        date: currentDate,
        start_time: selectedSlot.time,
        booked_for_id: parseInt(bookedForId)
    };
    
    // Close modal immediately for better UX
    closeBookingModal();
    
    try {
        const response = await fetch('/reservations/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(bookingData)
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showSuccess('Buchung erfolgreich erstellt!');
            
            // Reload both the grid and reservations list
            await loadAvailability(currentDate);
            await loadUserReservations();
        } else {
            showError(data.error || 'Fehler beim Erstellen der Buchung');
            // If there's an error, we might want to reopen the modal
            // but for now just show the error
        }
    } catch (error) {
        console.error('Error creating booking:', error);
        showError('Fehler beim Erstellen der Buchung');
    }
}

/**
 * Load user's favourites for the booking dropdown
 */
async function loadFavourites() {
    const bookingForSelect = document.getElementById('booking-for');
    if (!bookingForSelect) return;
    
    try {
        const currentUserOption = bookingForSelect.querySelector('option');
        const currentUserId = currentUserOption ? currentUserOption.value : null;
        
        if (!currentUserId) return;
        
        const response = await fetch(`/members/${currentUserId}/favourites`);
        
        if (response.ok) {
            const data = await response.json();
            
            if (data.favourites && data.favourites.length > 0) {
                data.favourites.forEach(fav => {
                    const option = document.createElement('option');
                    option.value = fav.id;
                    option.textContent = fav.name;
                    bookingForSelect.appendChild(option);
                });
            }
        }
    } catch (error) {
        console.error('Error loading favourites:', error);
    }
}

/**
 * Handle click on a reserved slot
 */
export async function handleReservationClick(reservationId, bookedFor, time) {
    try {
        const response = await fetch(`/reservations/${reservationId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showSuccess('Buchung erfolgreich storniert');
            loadAvailability(currentDate);
            loadUserReservations();
        } else {
            showError(data.error || 'Fehler beim Stornieren der Buchung');
        }
    } catch (error) {
        console.error('Error cancelling reservation:', error);
        showError('Fehler beim Stornieren der Buchung');
    }
}
