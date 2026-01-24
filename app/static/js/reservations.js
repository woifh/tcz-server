/**
 * User reservations management
 */

import { formatDateGerman, showSuccess, showError } from './utils.js';
import { loadAvailability } from './grid.js';

/**
 * Get CSRF token from meta tag
 */
function getCsrfToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute('content') : null;
}

/**
 * Load user's upcoming reservations
 */
export async function loadUserReservations() {
    const container = document.getElementById('user-reservations');
    if (!container) return;

    try {
        const response = await fetch('/api/reservations/');
        const data = await response.json();

        if (response.ok && data.reservations && data.reservations.length > 0) {
            // Sort by date and time
            const sortedReservations = data.reservations.sort((a, b) => {
                const dateCompare = a.date.localeCompare(b.date);
                if (dateCompare !== 0) return dateCompare;
                return a.start_time.localeCompare(b.start_time);
            });

            // Show only next 5 reservations
            const upcomingReservations = sortedReservations.slice(0, 5);

            container.innerHTML = upcomingReservations
                .map(
                    (res) => `
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
                            onclick="window.cancelReservationFromDashboard(${res.id}, '${res.booked_for}', '${formatDateGerman(res.date)}', '${res.start_time}')"
                            class="bg-red-500 hover:bg-red-600 text-white text-sm font-semibold py-2 px-4 rounded transition-colors"
                            title="Buchung stornieren">
                            Stornieren
                        </button>
                    </div>
                </div>
            `
                )
                .join('');
        } else {
            container.innerHTML =
                '<p class="text-gray-500 text-center py-4">Keine kommenden Buchungen vorhanden.</p>';
        }
    } catch (error) {
        console.error('Error loading user reservations:', error);
        container.innerHTML =
            '<p class="text-red-500 text-center py-4">Fehler beim Laden der Buchungen</p>';
    }
}

/**
 * Cancel reservation from dashboard
 */
export async function cancelReservationFromDashboard(reservationId, _bookedFor, _date, _time) {
    try {
        const response = await fetch(`/api/reservations/${reservationId}`, {
            method: 'DELETE',
            headers: { 'X-CSRFToken': getCsrfToken() },
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
export async function cancelReservation(reservationId) {
    try {
        const response = await fetch(`/api/reservations/${reservationId}`, {
            method: 'DELETE',
            headers: { 'X-CSRFToken': getCsrfToken() },
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
