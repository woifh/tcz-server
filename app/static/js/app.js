/**
 * Frontend JavaScript for Tennis Club Reservation System
 */

// Global state
let currentDate = new Date().toISOString().split('T')[0];
let selectedSlot = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    console.log('Tennis Club Reservation System loaded');
    
    // Set today's date as default
    const dateSelector = document.getElementById('date-selector');
    if (dateSelector) {
        dateSelector.value = currentDate;
        dateSelector.addEventListener('change', function() {
            currentDate = this.value;
            loadAvailability();
        });
        
        // Load initial availability
        loadAvailability();
    }
    
    // Setup booking form
    const bookingForm = document.getElementById('booking-form');
    if (bookingForm) {
        bookingForm.addEventListener('submit', handleBookingSubmit);
    }
    
    // Load favourites for booking dropdown
    loadFavourites();
});

/**
 * Load court availability for the selected date
 */
async function loadAvailability() {
    try {
        const response = await fetch(`/courts/availability?date=${currentDate}`);
        const data = await response.json();
        
        if (response.ok) {
            renderGrid(data.grid);
        } else {
            showError(data.error || 'Fehler beim Laden der Verfügbarkeit');
        }
    } catch (error) {
        console.error('Error loading availability:', error);
        showError('Fehler beim Laden der Verfügbarkeit');
    }
}

/**
 * Render the availability grid
 */
function renderGrid(grid) {
    const gridBody = document.getElementById('grid-body');
    if (!gridBody) return;
    
    // Time slots from 06:00 to 20:00
    const timeSlots = [];
    for (let hour = 6; hour <= 20; hour++) {
        timeSlots.push(`${hour.toString().padStart(2, '0')}:00`);
    }
    
    let html = '';
    
    timeSlots.forEach((time, timeIndex) => {
        html += '<tr>';
        html += `<td class="border border-gray-300 px-4 py-2 font-semibold">${time}</td>`;
        
        // For each court
        for (let courtIndex = 0; courtIndex < 6; courtIndex++) {
            const court = grid[courtIndex];
            const slot = court.slots[timeIndex];
            
            let cellClass = 'border border-gray-300 px-2 py-4 text-center cursor-pointer hover:opacity-80';
            let cellContent = '';
            let clickHandler = '';
            
            if (slot.status === 'available') {
                cellClass += ' bg-green-500 text-white';
                cellContent = 'Frei';
                clickHandler = `onclick="openBookingModal(${court.court_number}, '${time}')"`;
            } else if (slot.status === 'reserved') {
                cellClass += ' bg-red-500 text-white text-xs';
                cellContent = `Gebucht für ${slot.details.booked_for}<br>von ${slot.details.booked_by}`;
                clickHandler = '';
            } else if (slot.status === 'blocked') {
                cellClass += ' bg-gray-400 text-white';
                cellContent = 'Gesperrt';
                clickHandler = '';
            }
            
            html += `<td class="${cellClass}" ${clickHandler}>${cellContent}</td>`;
        }
        
        html += '</tr>';
    });
    
    gridBody.innerHTML = html;
}

/**
 * Open booking modal with pre-filled data
 */
function openBookingModal(courtNumber, time) {
    selectedSlot = { courtNumber, time };
    
    document.getElementById('booking-date').value = currentDate;
    document.getElementById('booking-court').value = `Platz ${courtNumber}`;
    document.getElementById('booking-time').value = `${time} - ${getEndTime(time)}`;
    
    document.getElementById('booking-modal').classList.remove('hidden');
}

/**
 * Close booking modal
 */
function closeBookingModal() {
    document.getElementById('booking-modal').classList.add('hidden');
    selectedSlot = null;
}

/**
 * Handle booking form submission
 */
async function handleBookingSubmit(event) {
    event.preventDefault();
    
    if (!selectedSlot) return;
    
    const bookedForId = document.getElementById('booking-for').value;
    
    // Find court ID from court number
    const courtId = selectedSlot.courtNumber;
    
    const bookingData = {
        court_id: courtId,
        date: currentDate,
        start_time: selectedSlot.time,
        booked_for_id: parseInt(bookedForId)
    };
    
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
            closeBookingModal();
            loadAvailability(); // Reload grid
        } else {
            showError(data.error || 'Fehler beim Erstellen der Buchung');
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
    
    // Keep the current user option
    const currentUserOption = bookingForSelect.querySelector('option');
    
    // In a full implementation, we would fetch favourites from the API
    // For now, the dropdown will just show the current user
}

/**
 * Calculate end time (1 hour after start)
 */
function getEndTime(startTime) {
    const [hours, minutes] = startTime.split(':').map(Number);
    const endHours = (hours + 1).toString().padStart(2, '0');
    return `${endHours}:${minutes.toString().padStart(2, '0')}`;
}

/**
 * Show success message
 */
function showSuccess(message) {
    // Create a flash message element
    const flashDiv = document.createElement('div');
    flashDiv.className = 'fixed top-4 right-4 bg-green-100 text-green-700 px-6 py-4 rounded-lg shadow-lg z-50';
    flashDiv.textContent = message;
    document.body.appendChild(flashDiv);
    
    // Remove after 3 seconds
    setTimeout(() => {
        flashDiv.remove();
    }, 3000);
}

/**
 * Show error message
 */
function showError(message) {
    // Create a flash message element
    const flashDiv = document.createElement('div');
    flashDiv.className = 'fixed top-4 right-4 bg-red-100 text-red-700 px-6 py-4 rounded-lg shadow-lg z-50';
    flashDiv.textContent = message;
    document.body.appendChild(flashDiv);
    
    // Remove after 5 seconds
    setTimeout(() => {
        flashDiv.remove();
    }, 5000);
}

/**
 * Format date in German convention (DD.MM.YYYY)
 */
function formatDateGerman(dateString) {
    const date = new Date(dateString);
    const day = date.getDate().toString().padStart(2, '0');
    const month = (date.getMonth() + 1).toString().padStart(2, '0');
    const year = date.getFullYear();
    return `${day}.${month}.${year}`;
}

/**
 * Cancel a reservation
 */
async function cancelReservation(reservationId) {
    if (!confirm('Möchten Sie diese Buchung wirklich stornieren?')) {
        return;
    }
    
    try {
        const response = await fetch(`/reservations/${reservationId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showSuccess('Buchung erfolgreich storniert');
            // Reload the page or update the list
            window.location.reload();
        } else {
            showError(data.error || 'Fehler beim Stornieren der Buchung');
        }
    } catch (error) {
        console.error('Error cancelling reservation:', error);
        showError('Fehler beim Stornieren der Buchung');
    }
}
