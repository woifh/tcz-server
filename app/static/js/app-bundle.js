/**
 * Tennis Club Reservation System - Bundled Version
 * All modules combined into one file for compatibility
 */

// ============================================================================
// UTILS MODULE
// ============================================================================

/**
 * Calculate end time (1 hour after start)
 */
function getEndTime(startTime) {
    const [hours, minutes] = startTime.split(':').map(Number);
    const endHours = (hours + 1).toString().padStart(2, '0');
    return `${endHours}:${minutes.toString().padStart(2, '0')}`;
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
 * Show success message
 */
function showSuccess(message) {
    const flashDiv = document.createElement('div');
    flashDiv.className = 'fixed top-4 right-4 bg-green-100 text-green-700 px-6 py-4 rounded-lg shadow-lg z-50';
    flashDiv.textContent = message;
    document.body.appendChild(flashDiv);
    
    setTimeout(() => {
        flashDiv.remove();
    }, 3000);
}

/**
 * Show error message
 */
function showError(message) {
    const flashDiv = document.createElement('div');
    flashDiv.className = 'fixed top-4 right-4 bg-red-100 text-red-700 px-6 py-4 rounded-lg shadow-lg z-50';
    flashDiv.textContent = message;
    document.body.appendChild(flashDiv);
    
    setTimeout(() => {
        flashDiv.remove();
    }, 5000);
}

/**
 * Generate time slots from 06:00 to 21:00
 */
function generateTimeSlots() {
    const timeSlots = [];
    for (let hour = 6; hour <= 21; hour++) {
        timeSlots.push(`${hour.toString().padStart(2, '0')}:00`);
    }
    return timeSlots;
}

// ============================================================================
// GRID MODULE
// ============================================================================

/**
 * Load court availability for the selected date
 */
async function loadAvailability(currentDate) {
    console.log('Loading availability for date:', currentDate);
    try {
        const response = await fetch(`/courts/availability?date=${currentDate}`);
        console.log('Response status:', response.status);
        
        if (!response.ok) {
            console.error('Response not OK:', response.status, response.statusText);
            showError(`Fehler beim Laden: ${response.status}`);
            return;
        }
        
        const data = await response.json();
        console.log('Received data:', data);
        
        if (data.grid) {
            renderGrid(data.grid);
        } else {
            showError(data.error || 'Fehler beim Laden der Verfügbarkeit');
        }
    } catch (error) {
        console.error('Error loading availability:', error);
        showError('Fehler beim Laden der Verfügbarkeit: ' + error.message);
    }
}

/**
 * Render the availability grid
 */
function renderGrid(grid) {
    const gridBody = document.getElementById('grid-body');
    if (!gridBody) return;
    
    // Get current user ID from the booking dropdown
    const bookingForSelect = document.getElementById('booking-for');
    const currentUserId = bookingForSelect ? parseInt(bookingForSelect.querySelector('option')?.value) : null;
    
    const timeSlots = generateTimeSlots();
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
                
                // Check if current user can cancel this reservation
                const canCancel = currentUserId && (
                    slot.details.booked_for_id === currentUserId || 
                    slot.details.booked_by_id === currentUserId
                );
                
                if (canCancel) {
                    clickHandler = `onclick="handleReservationClick(${slot.details.reservation_id}, '${slot.details.booked_for}', '${time}')"`;
                }
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

// ============================================================================
// BOOKING MODULE
// ============================================================================

let selectedSlot = null;
let currentDate = new Date().toISOString().split('T')[0];

/**
 * Initialize booking module
 */
function initBooking(date) {
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
function setCurrentDate(date) {
    currentDate = date;
}

/**
 * Open booking modal with pre-filled data
 */
function openBookingModal(courtNumber, time) {
    const dateSelector = document.getElementById('date-selector');
    const currentDate = dateSelector ? dateSelector.value : new Date().toISOString().split('T')[0];
    
    selectedSlot = { courtNumber, time };
    
    // Get modal elements with null checks
    const bookingDate = document.getElementById('booking-date');
    const bookingCourt = document.getElementById('booking-court');
    const bookingTime = document.getElementById('booking-time');
    const bookingError = document.getElementById('booking-error');
    const bookingModal = document.getElementById('booking-modal');
    
    // Check if all elements exist
    if (!bookingDate || !bookingCourt || !bookingTime || !bookingError || !bookingModal) {
        console.error('Booking modal elements not found');
        return;
    }
    
    // Set values
    bookingDate.value = currentDate;
    bookingCourt.value = `Platz ${courtNumber}`;
    bookingTime.value = `${time} - ${getEndTime(time)}`;
    bookingError.classList.add('hidden');
    bookingModal.classList.remove('hidden');
}

/**
 * Close booking modal
 */
function closeBookingModal() {
    const bookingModal = document.getElementById('booking-modal');
    if (bookingModal) {
        bookingModal.classList.add('hidden');
    }
    selectedSlot = null;
}

// Old Alpine.js bridge code removed - now using vanilla JS modal

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
            console.log('Booking created successfully, reloading data...');
            showSuccess('Buchung erfolgreich erstellt!');
            
            // Reload both the grid and reservations list
            console.log('Reloading availability...');
            await loadAvailability(currentDate);
            console.log('Reloading user reservations...');
            await loadUserReservations();
            console.log('Data reload complete');
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
async function handleReservationClick(reservationId, bookedFor, time) {
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

// ============================================================================
// RESERVATIONS MODULE
// ============================================================================

/**
 * Load user's upcoming reservations
 */
async function loadUserReservations() {
    console.log('loadUserReservations called');
    const container = document.getElementById('user-reservations');
    if (!container) {
        console.log('user-reservations container not found');
        return;
    }
    
    console.log('Fetching reservations...');
    try {
        const response = await fetch('/reservations/?format=json');
        const data = await response.json();
        console.log('Reservations data:', data);
        
        if (response.ok && data.reservations && data.reservations.length > 0) {
            // Sort by date and time
            const sortedReservations = data.reservations.sort((a, b) => {
                const dateCompare = a.date.localeCompare(b.date);
                if (dateCompare !== 0) return dateCompare;
                return a.start_time.localeCompare(b.start_time);
            });
            
            // Show only next 5 reservations
            const upcomingReservations = sortedReservations.slice(0, 5);
            
            container.innerHTML = upcomingReservations.map(res => `
                <div class="bg-white rounded-lg p-4 border border-gray-200 hover:border-blue-300 transition-colors">
                    <div class="flex justify-between items-start">
                        <div class="flex-1">
                            <div class="flex items-center gap-2 mb-2">
                                <span class="font-semibold text-lg">Platz ${res.court_number}</span>
                                <span class="text-gray-600">•</span>
                                <span class="text-gray-700">${formatDateGerman(res.date)}</span>
                            </div>
                            <div class="text-gray-600 text-sm mb-1">
                                <span class="font-medium">Zeit:</span> ${res.start_time} - ${res.end_time} Uhr
                            </div>
                            <div class="text-gray-600 text-sm">
                                <span class="font-medium">Gebucht für:</span> ${res.booked_for}
                                ${res.booked_by !== res.booked_for ? `<span class="text-gray-500">(von ${res.booked_by})</span>` : ''}
                            </div>
                        </div>
                        <button 
                            onclick="cancelReservationFromDashboard(${res.id}, '${res.booked_for}', '${formatDateGerman(res.date)}', '${res.start_time}')"
                            class="bg-red-500 hover:bg-red-600 text-white text-sm font-semibold py-2 px-4 rounded transition-colors flex items-center gap-2"
                            title="Buchung stornieren">
                            <span class="material-icons text-sm">cancel</span>
                            Stornieren
                        </button>
                    </div>
                </div>
            `).join('');
        } else {
            container.innerHTML = '<p class="text-gray-500 text-center py-4">Keine kommenden Buchungen vorhanden.</p>';
        }
    } catch (error) {
        console.error('Error loading user reservations:', error);
        container.innerHTML = '<p class="text-red-500 text-center py-4">Fehler beim Laden der Buchungen</p>';
    }
}

/**
 * Cancel reservation from dashboard
 */
async function cancelReservationFromDashboard(reservationId, bookedFor, date, time) {
    try {
        const response = await fetch(`/reservations/${reservationId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showSuccess('Buchung erfolgreich storniert');
            loadUserReservations();
            
            // Reload grid if available
            const dateSelector = document.getElementById('date-selector');
            if (dateSelector) {
                loadAvailability(dateSelector.value);
            }
        } else {
            showError(data.error || 'Fehler beim Stornieren der Buchung');
        }
    } catch (error) {
        console.error('Error cancelling reservation:', error);
        showError('Fehler beim Stornieren der Buchung');
    }
}

/**
 * Cancel a reservation (generic)
 */
async function cancelReservation(reservationId) {
    try {
        const response = await fetch(`/reservations/${reservationId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showSuccess('Buchung erfolgreich storniert');
            window.location.reload();
        } else {
            showError(data.error || 'Fehler beim Stornieren der Buchung');
        }
    } catch (error) {
        console.error('Error cancelling reservation:', error);
        showError('Fehler beim Stornieren der Buchung');
    }
}

// ============================================================================
// MAIN APP
// ============================================================================

/**
 * Change date by offset (days)
 */
function changeDate(offset) {
    const date = new Date(currentDate);
    date.setDate(date.getDate() + offset);
    currentDate = date.toISOString().split('T')[0];
    
    const dateSelector = document.getElementById('date-selector');
    if (dateSelector) {
        dateSelector.value = currentDate;
    }
    
    setCurrentDate(currentDate);
    loadAvailability(currentDate);
}

/**
 * Go to today's date
 */
function goToToday() {
    currentDate = new Date().toISOString().split('T')[0];
    
    const dateSelector = document.getElementById('date-selector');
    if (dateSelector) {
        dateSelector.value = currentDate;
    }
    
    setCurrentDate(currentDate);
    loadAvailability(currentDate);
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    console.log('Tennis Club Reservation System loaded - Bundled version');
    console.log('Current date:', currentDate);
    
    // Set today's date as default
    const dateSelector = document.getElementById('date-selector');
    console.log('Date selector found:', !!dateSelector);
    
    if (dateSelector) {
        dateSelector.value = currentDate;
        dateSelector.addEventListener('change', function() {
            currentDate = this.value;
            setCurrentDate(currentDate);
            loadAvailability(currentDate);
        });
        
        // Load initial availability
        console.log('Loading initial availability...');
        loadAvailability(currentDate);
    } else {
        console.error('Date selector not found!');
    }
    
    // Initialize booking module
    console.log('Initializing booking module...');
    initBooking(currentDate);
    
    // Load user's upcoming reservations
    console.log('Loading user reservations...');
    loadUserReservations();
});
