/**
 * Alpine.js Favourites Store
 * Centralized state management for user's favourite members
 */

/**
 * Get CSRF token from meta tag
 */
function getCsrfToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute('content') : null;
}

export function initFavouritesStore() {
    if (typeof window === 'undefined' || !window.Alpine) return;

    document.addEventListener('alpine:init', () => {
        window.Alpine.store('favourites', {
            // State
            items: [],
            loading: false,
            error: null,

            // Methods
            async load() {
                this.loading = true;
                this.error = null;

                try {
                    // Get current user ID
                    const bookingForSelect = document.getElementById('booking-for');
                    if (!bookingForSelect) return;

                    const firstOption = bookingForSelect.querySelector('option');
                    const currentUserId = firstOption ? firstOption.value : null;

                    if (!currentUserId) return;

                    const response = await fetch(`/api/members/${currentUserId}/favourites`);

                    if (response.ok) {
                        const data = await response.json();
                        this.items = data.favourites || [];
                    } else {
                        this.error = 'Fehler beim Laden der Favoriten';
                    }
                } catch (err) {
                    console.error('Error loading favourites:', err);
                    this.error = 'Fehler beim Laden der Favoriten';
                } finally {
                    this.loading = false;
                }
            },

            async add(memberId) {
                this.loading = true;
                this.error = null;

                try {
                    const response = await fetch('/api/members/favourites', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': getCsrfToken(),
                        },
                        body: JSON.stringify({ member_id: memberId }),
                    });

                    if (response.ok) {
                        await this.load(); // Reload the list
                        return true;
                    } else {
                        const data = await response.json();
                        this.error = data.error || 'Fehler beim Hinzufügen';
                        return false;
                    }
                } catch (err) {
                    console.error('Error adding favourite:', err);
                    this.error = 'Fehler beim Hinzufügen';
                    return false;
                } finally {
                    this.loading = false;
                }
            },

            async remove(favouriteId) {
                this.loading = true;
                this.error = null;

                try {
                    const response = await fetch(`/api/members/favourites/${favouriteId}`, {
                        method: 'DELETE',
                        headers: { 'X-CSRFToken': getCsrfToken() },
                    });

                    if (response.ok) {
                        await this.load(); // Reload the list
                        return true;
                    } else {
                        const data = await response.json();
                        this.error = data.error || 'Fehler beim Entfernen';
                        return false;
                    }
                } catch (err) {
                    console.error('Error removing favourite:', err);
                    this.error = 'Fehler beim Entfernen';
                    return false;
                } finally {
                    this.loading = false;
                }
            },

            getById(id) {
                return this.items.find((item) => item.id === id);
            },

            getAll() {
                return this.items;
            },
        });
    });
}

// Auto-initialize
if (typeof window !== 'undefined') {
    initFavouritesStore();
}
