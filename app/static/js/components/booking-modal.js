/**
 * Alpine.js Booking Modal Component
 * Handles booking creation workflow with form validation and API submission
 */

import { getToday } from '../utils/date-utils.js';

/**
 * Get CSRF token from meta tag
 */
function getCsrfToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute('content') : null;
}

export function bookingModal() {
    return {
        // State
        show: false,
        date: '',
        court: null,
        courtName: '',
        time: '',
        bookedFor: null,
        favourites: [], // Initialize as empty array
        submitting: false,
        error: null,
        _favouritesLoaded: false, // Prevent duplicate API calls

        // Member search state
        showSearch: false,
        searchQuery: '',
        searchResults: [],
        searchLoading: false,
        searchError: null,
        searchHighlightIndex: -1,

        // Lifecycle
        init() {
            // Register this component with Alpine store for external access
            if (window.Alpine && window.Alpine.store) {
                const bookingStore = window.Alpine.store('booking');
                if (bookingStore) {
                    bookingStore.modalComponent = this;
                }
            }

            // Only load favourites once per component instance
            if (!this._favouritesLoaded) {
                this._favouritesLoaded = true;
                this.loadFavourites();
            }
        },

        // Methods
        open(courtNumber, time, date) {
            this.court = courtNumber;
            this.courtName = `Platz ${courtNumber}`;
            this.time = time;
            this.date = date || getToday();
            this.error = null;
            this.show = true;

            // Set default booked for to current user
            const bookingForSelect = document.getElementById('booking-for');
            if (bookingForSelect && bookingForSelect.options.length > 0) {
                this.bookedFor = bookingForSelect.options[0].value;
            }
        },

        close() {
            this.show = false;
            this.reset();
        },

        reset() {
            this.error = null;
            this.submitting = false;
            this.court = null;
            this.courtName = '';
            this.time = '';
            this.date = '';
            this.resetSearch();
        },

        // Member search methods
        toggleSearch() {
            this.showSearch = !this.showSearch;
            if (this.showSearch) {
                this.$nextTick(() => {
                    const searchInput = document.getElementById('booking-member-search');
                    if (searchInput) searchInput.focus();
                });
            } else {
                this.resetSearch();
            }
        },

        resetSearch() {
            this.showSearch = false;
            this.searchQuery = '';
            this.searchResults = [];
            this.searchLoading = false;
            this.searchError = null;
            this.searchHighlightIndex = -1;
        },

        async searchMembers() {
            const query = this.searchQuery.trim();
            if (!query) {
                this.searchResults = [];
                this.searchError = null;
                this.searchHighlightIndex = -1;
                return;
            }

            this.searchLoading = true;
            this.searchError = null;
            this.searchHighlightIndex = -1;

            try {
                const response = await fetch(`/api/members/search?q=${encodeURIComponent(query)}`);
                const data = await response.json();

                if (response.ok) {
                    this.searchResults = data.results || [];
                } else {
                    this.searchError = data.error || 'Fehler bei der Suche';
                    this.searchResults = [];
                }
            } catch (err) {
                console.error('Member search error:', err);
                this.searchError = 'Netzwerkfehler bei der Suche';
                this.searchResults = [];
            } finally {
                this.searchLoading = false;
            }
        },

        searchHighlightNext() {
            if (this.searchResults.length === 0) return;
            this.searchHighlightIndex = Math.min(
                this.searchHighlightIndex + 1,
                this.searchResults.length - 1
            );
        },

        searchHighlightPrevious() {
            if (this.searchResults.length === 0) return;
            this.searchHighlightIndex = Math.max(this.searchHighlightIndex - 1, 0);
        },

        searchSelectHighlighted() {
            if (
                this.searchHighlightIndex >= 0 &&
                this.searchHighlightIndex < this.searchResults.length
            ) {
                this.selectSearchResult(this.searchResults[this.searchHighlightIndex]);
            }
        },

        selectSearchResult(member) {
            // Add to local favourites array for immediate UI display
            // Server will persist the favourite when booking is created
            this.favourites.push({
                id: member.id,
                name: member.name,
                email: member.email,
            });

            // Select this member for booking
            this.bookedFor = member.id;

            // Clear any previous booking error since member changed
            this.error = null;

            // Close search UI
            this.resetSearch();
        },

        async submit() {
            if (!this.validate()) {
                return;
            }

            this.submitting = true;
            this.error = null;

            const bookingData = {
                court_id: this.court,
                date: this.date,
                start_time: this.time,
                booked_for_id: this.bookedFor,
            };

            try {
                const response = await fetch('/api/reservations/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCsrfToken(),
                    },
                    body: JSON.stringify(bookingData),
                });

                const data = await response.json();

                if (response.ok) {
                    this.close();
                    this.showSuccess('Buchung erfolgreich erstellt!');

                    // Refresh favourites (server may have added new favourite)
                    this.loadFavourites();

                    // Trigger dashboard reload
                    this.reloadDashboard();
                } else {
                    // Build error message, including active sessions if available
                    let errorMsg = data.error || 'Fehler beim Erstellen der Buchung';

                    if (data.active_sessions && data.active_sessions.length > 0) {
                        const sessionLines = data.active_sessions.map((s) => {
                            const dateObj = new Date(s.date);
                            const formattedDate = dateObj.toLocaleDateString('de-DE', {
                                weekday: 'short',
                                day: '2-digit',
                                month: '2-digit',
                            });
                            // Calculate end time (1 hour after start)
                            const [startHour] = s.start_time.split(':');
                            const endHour = (parseInt(startHour) + 1).toString().padStart(2, '0');
                            const endTime = `${endHour}:00`;
                            return `• ${formattedDate}, ${s.start_time}-${endTime}, Platz ${s.court_number}`;
                        });

                        errorMsg += '\n' + sessionLines.join('\n');
                    }

                    this.error = errorMsg;

                    // Refresh grid to show current state (e.g., slot was booked by someone else)
                    this.reloadDashboard();
                }
            } catch (err) {
                console.error('Error creating booking:', err);
                this.error = 'Fehler beim Erstellen der Buchung';
            } finally {
                this.submitting = false;
            }
        },

        validate() {
            if (!this.court || !this.date || !this.time || !this.bookedFor) {
                this.error = 'Bitte füllen Sie alle Felder aus';
                return false;
            }
            return true;
        },

        async loadFavourites() {
            console.log('Loading favourites...');
            try {
                const bookingForSelect = document.getElementById('booking-for');
                console.log('Booking select element:', bookingForSelect);
                if (!bookingForSelect) {
                    console.log('No booking-for select found');
                    return;
                }

                const firstOption = bookingForSelect.querySelector('option');
                const currentUserId = firstOption ? firstOption.value : null;
                console.log('Current user ID:', currentUserId);
                console.log('First option:', firstOption);

                if (!currentUserId) {
                    console.log('No current user ID found');
                    return;
                }

                console.log(`Fetching favourites from: /api/members/${currentUserId}/favourites`);
                const response = await fetch(`/api/members/${currentUserId}/favourites`);
                console.log('Favourites response:', response.status, response.ok);

                if (response.ok) {
                    const data = await response.json();
                    console.log('Favourites data:', data);
                    this.favourites = data.favourites || [];
                    console.log('Set favourites:', this.favourites);
                } else {
                    console.log('Favourites request failed:', response.status);
                }
            } catch (err) {
                console.error('Error loading favourites:', err);
            }
        },

        reloadDashboard() {
            // Trigger dashboard component refresh (partial update to avoid table flicker)
            const dashboardEl = document.querySelector('[x-data*="dashboard"]');
            if (dashboardEl && window.Alpine) {
                try {
                    const dashboard = window.Alpine.$data(dashboardEl);
                    if (dashboard) {
                        // Use refreshAvailability for partial update (no flicker)
                        if (typeof dashboard.refreshAvailability === 'function') {
                            dashboard.refreshAvailability();
                        } else if (typeof dashboard.loadAvailability === 'function') {
                            dashboard.loadAvailability();
                        }
                        if (typeof dashboard.loadUserReservations === 'function') {
                            dashboard.loadUserReservations();
                        }
                    }
                } catch (e) {
                    console.error('Error reloading dashboard:', e);
                }
            }
        },

        showSuccess(message) {
            if (typeof window.showSuccess === 'function') {
                window.showSuccess(message);
            }
        },

        getTimeRange() {
            if (!this.time) return '';
            const [hour] = this.time.split(':');
            const endHour = parseInt(hour) + 1;
            return `${this.time} - ${endHour.toString().padStart(2, '0')}:00`;
        },
    };
}

// Initialize Alpine store for booking
if (typeof window !== 'undefined') {
    document.addEventListener('alpine:init', () => {
        if (window.Alpine) {
            window.Alpine.store('booking', {
                modalComponent: null,
            });
        }
    });
}
