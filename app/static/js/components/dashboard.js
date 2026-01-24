/**
 * Alpine.js Dashboard Component
 * Manages court availability grid, date navigation, and user reservations
 */

import {
    getToday,
    toBerlinDateString,
    isToday,
    generateDateRange,
    formatDateHeaderGerman,
} from '../utils/date-utils.js';
import { availabilityService, availabilityCache } from '../utils/availability-service.js';

/**
 * Get CSRF token from meta tag
 */
function getCsrfToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute('content') : null;
}

// Track which component instances have been initialized to prevent double init
const initializedComponents = new WeakSet();

export function dashboard() {
    return {
        // State
        selectedDate: getToday(),
        courts: [],
        timeSlots: [],
        availability: {},
        userReservations: [],
        bookingsForOthers: [],
        loading: false,
        error: null,
        currentUserId: null,
        isAuthenticated: true, // Default to authenticated, will be overridden for anonymous users
        defaultCellClass:
            'px-2 py-3 text-center text-xs rounded-lg bg-gray-100 border border-gray-200', // Default class for cells before data loads

        // Date navigation state
        dateRange: [],
        visibleDays: [],
        windowStartIndex: 0,
        visibleDaysCount: 7,
        isSelectedToday: true,

        // Lifecycle
        init() {
            // Prevent double initialization (e.g., from Alpine reinit or x-init calling twice)
            if (initializedComponents.has(this.$el)) return;
            initializedComponents.add(this.$el);

            // Detect authentication status from global variable or DOM
            this.isAuthenticated =
                window.isAuthenticated !== undefined ? window.isAuthenticated : true;

            // Get current user ID from the page (only for authenticated users)
            if (this.isAuthenticated) {
                const bookingForSelect = document.getElementById('booking-for');
                if (bookingForSelect) {
                    const firstOption = bookingForSelect.querySelector('option');
                    this.currentUserId = firstOption ? firstOption.value : null;
                }
            }

            // Initialize date strip for mobile
            this.initDateStrip();

            // Load initial availability with caching
            this.loadWithCache(true);

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
                const response = await fetch(`/api/courts/availability?date=${this.selectedDate}`);

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const data = await response.json();

                // Generate time slots if not already set
                if (this.timeSlots.length === 0) {
                    this.timeSlots = this.generateTimeSlots();
                }

                // Handle sparse format (new) - has 'courts' with 'occupied' arrays
                if (data.courts && data.courts[0]?.occupied !== undefined) {
                    this.availability = data;
                    this.courts = this.transformSparseResponse(data);
                }
                // Handle legacy full format - has 'grid' with 'slots' arrays
                else if (data.grid) {
                    this.availability = data;
                    this.courts = data.grid;
                }
                // Handle test data format
                else if (data.slots) {
                    this.availability = data;
                    this.courts = data.slots;
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

        /**
         * Load availability with cache-first strategy.
         * Shows cached data immediately if available, fetches fresh data in background if stale.
         * @param {boolean} isInitialLoad - True for first load, triggers range prefetch
         */
        async loadWithCache(isInitialLoad = false) {
            // Generate time slots if not already set
            if (this.timeSlots.length === 0) {
                this.timeSlots = this.generateTimeSlots();
            }

            // Check cache first
            const cached = availabilityCache.get(this.selectedDate);

            if (cached) {
                // Show cached data immediately
                this.applyAvailabilityData(cached.data);
                this.loading = false;

                // Always refresh in background to ensure data is current
                this.refreshInBackground();

                // Prefetch surrounding dates
                availabilityService.prefetchAround(this.selectedDate);
                return;
            }

            // No cache - need to fetch
            this.loading = true;
            this.error = null;

            try {
                if (isInitialLoad) {
                    // Initial load: fetch range for better UX
                    await availabilityService.initialLoad();
                    const freshCached = availabilityCache.get(this.selectedDate);
                    if (freshCached) {
                        this.applyAvailabilityData(freshCached.data);
                    }
                } else {
                    // Single date fetch
                    const { data } = await availabilityService.getForDate(this.selectedDate);
                    this.applyAvailabilityData(data);
                }
            } catch (err) {
                console.error('Error loading availability:', err);
                this.error = 'Fehler beim Laden der Verfügbarkeit';
                // Fall back to direct fetch
                await this.loadAvailability();
            } finally {
                this.loading = false;
            }
        },

        /**
         * Apply availability data to component state.
         * @param {Object} data - Availability data from API or cache
         */
        applyAvailabilityData(data) {
            if (!data) return;

            // Handle sparse format (has 'courts' with 'occupied' arrays)
            if (data.courts && data.courts[0]?.occupied !== undefined) {
                this.availability = data;
                this.courts = this.transformSparseResponse(data);
            }
            // Handle legacy full format (has 'grid' with 'slots' arrays)
            else if (data.grid) {
                this.availability = data;
                this.courts = data.grid;
            }
            // Handle test data format
            else if (data.slots) {
                this.availability = data;
                this.courts = data.slots;
            } else if (data.error) {
                this.error = data.error;
            }
        },

        /**
         * Refresh current date in background without UI blocking.
         * Always fetches fresh data from API to ensure accuracy.
         */
        async refreshInBackground() {
            const dateToRefresh = this.selectedDate;
            try {
                const data = await availabilityService.fetchFresh(dateToRefresh);

                // Only update if we're still viewing the same date
                if (data && this.selectedDate === dateToRefresh) {
                    const newCourts = this.transformSparseResponse(data);
                    // Merge updates without full re-render
                    newCourts.forEach((newCourt, courtIndex) => {
                        if (this.courts[courtIndex]) {
                            newCourt.slots.forEach((newSlot, slotIndex) => {
                                const oldSlot = this.courts[courtIndex].slots[slotIndex];
                                if (oldSlot && this.slotHasChanged(oldSlot, newSlot)) {
                                    Object.assign(
                                        this.courts[courtIndex].slots[slotIndex],
                                        newSlot
                                    );
                                }
                            });
                        }
                    });
                }
            } catch (err) {
                console.warn('Background refresh failed:', err);
            }
        },

        /**
         * Transform sparse API response to dense grid format for template compatibility.
         * Sparse format only includes occupied slots; this fills in available slots.
         */
        transformSparseResponse(data) {
            return data.courts.map((court) => {
                // Build lookup map for occupied slots
                const occupiedMap = {};
                for (const slot of court.occupied) {
                    occupiedMap[slot.time] = slot;
                }

                // Generate full slots array
                const slots = this.timeSlots.map((time) => {
                    const occupied = occupiedMap[time];

                    if (occupied) {
                        // Occupied slot - compute CSS and content
                        return {
                            time: occupied.time,
                            status: occupied.status,
                            details: occupied.details,
                            cssClass: this.getSlotClass(occupied, time),
                            content: this.getSlotContent(occupied, time),
                            isPast: this.isSlotInPast(time),
                            canCancel: this.canCancelSlot(occupied),
                        };
                    } else {
                        // Available slot - generate default
                        const isPast = this.isSlotInPast(time);
                        return {
                            time,
                            status: 'available',
                            details: null,
                            cssClass: this.getAvailableSlotClass(isPast),
                            content: isPast ? '' : 'Frei',
                            isPast,
                            canCancel: false,
                        };
                    }
                });

                return {
                    court_id: court.court_id,
                    court_number: court.court_number,
                    slots,
                };
            });
        },

        /**
         * Get CSS classes for an available slot.
         */
        getAvailableSlotClass(isPast) {
            const base = 'border border-gray-300 px-2 py-4 text-center text-xs';
            if (isPast) {
                return `${base} bg-gray-200 text-gray-500`;
            }
            if (this.isAuthenticated) {
                return `${base} bg-white text-gray-700 cursor-pointer hover:bg-gray-50`;
            }
            return `${base} bg-white text-gray-700`;
        },

        async refreshAvailability() {
            // Refresh availability without showing loading state (prevents table flicker)
            try {
                const response = await fetch(`/api/courts/availability?date=${this.selectedDate}`);
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                const data = await response.json();

                // Transform sparse format or use legacy format
                let newCourts;
                if (data.courts && data.courts[0]?.occupied !== undefined) {
                    newCourts = this.transformSparseResponse(data);
                } else {
                    newCourts = data.grid || data.slots || [];
                }

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
            return (
                oldSlot.status !== newSlot.status ||
                oldSlot.reservation_id !== newSlot.reservation_id ||
                JSON.stringify(oldSlot.details) !== JSON.stringify(newSlot.details)
            );
        },

        async loadUserReservations() {
            try {
                const response = await fetch('/api/reservations/');

                if (response.ok) {
                    const data = await response.json();
                    const allReservations = data.reservations || [];

                    // Split reservations: my own vs bookings I made for others
                    // userReservations: where I am the booked_for person (counts toward my limits)
                    // bookingsForOthers: where I booked for someone else
                    this.userReservations = allReservations.filter(
                        (r) => r.booked_for_id === this.currentUserId
                    );
                    this.bookingsForOthers = allReservations.filter(
                        (r) =>
                            r.booked_by_id === this.currentUserId &&
                            r.booked_for_id !== this.currentUserId
                    );
                }
            } catch (err) {
                console.error('Error loading user reservations:', err);
            }
        },

        changeDate(offset) {
            const date = new Date(this.selectedDate + 'T12:00:00'); // Use noon to avoid DST issues
            date.setDate(date.getDate() + offset);
            this.selectedDate = toBerlinDateString(date);
            this.isSelectedToday = isToday(this.selectedDate);
            this.loadWithCache();
        },

        goToToday() {
            this.selectedDate = getToday();
            this.isSelectedToday = true;
            this.centerWindowOnDate(this.selectedDate);
            this.loadWithCache();
        },

        // Date navigation methods
        initDateStrip() {
            this.dateRange = generateDateRange(30, 90);
            this.isSelectedToday = isToday(this.selectedDate);
            this.updateVisibleDaysCount();
            this.centerWindowOnDate(this.selectedDate);

            // Listen for resize to adjust visible days count
            window.addEventListener('resize', () => this.handleResize());
        },

        updateVisibleDaysCount() {
            // Responsive: 7 on desktop (≥768px), 5 on mobile
            const width = window.innerWidth;
            this.visibleDaysCount = width >= 768 ? 7 : 5;
        },

        handleResize() {
            const oldCount = this.visibleDaysCount;
            this.updateVisibleDaysCount();
            if (oldCount !== this.visibleDaysCount) {
                this.centerWindowOnDate(this.selectedDate);
            }
        },

        centerWindowOnDate(isoDate) {
            const index = this.dateRange.findIndex((d) => d.isoDate === isoDate);
            if (index === -1) return;

            const centerOffset = Math.floor(this.visibleDaysCount / 2);
            this.windowStartIndex = Math.max(
                0,
                Math.min(index - centerOffset, this.dateRange.length - this.visibleDaysCount)
            );
            this.updateVisibleDays();
        },

        shiftWindow(offset) {
            // Change selected date by offset days
            const currentIndex = this.dateRange.findIndex((d) => d.isoDate === this.selectedDate);
            const newIndex = currentIndex + offset;

            // Check bounds
            if (newIndex < 0 || newIndex >= this.dateRange.length) return;

            // Update selected date
            const newDate = this.dateRange[newIndex];
            this.selectedDate = newDate.isoDate;
            this.isSelectedToday = newDate.isToday;

            // Shift window if selected date would go out of view
            const visibleStart = this.windowStartIndex;
            const visibleEnd = this.windowStartIndex + this.visibleDaysCount - 1;

            if (newIndex < visibleStart) {
                this.windowStartIndex = newIndex;
                this.updateVisibleDays();
            } else if (newIndex > visibleEnd) {
                this.windowStartIndex = newIndex - this.visibleDaysCount + 1;
                this.updateVisibleDays();
            }

            // Load availability for new date
            this.loadWithCache();
        },

        updateVisibleDays() {
            this.visibleDays = this.dateRange.slice(
                this.windowStartIndex,
                this.windowStartIndex + this.visibleDaysCount
            );
        },

        selectDate(isoDate) {
            this.selectedDate = isoDate;
            this.isSelectedToday = isToday(isoDate);
            this.loadWithCache();
        },

        getDayCellClasses(day) {
            const isSelected = day.isoDate === this.selectedDate;
            if (isSelected) {
                return 'day-card-selected';
            }
            if (day.isToday) {
                return 'day-card-today';
            }
            return 'day-card-default';
        },

        formatDateHeader(isoDate) {
            return formatDateHeaderGerman(isoDate);
        },

        onDatePickerChange() {
            this.isSelectedToday = isToday(this.selectedDate);
            this.centerWindowOnDate(this.selectedDate);
            this.loadWithCache();
        },

        handleSlotClick(court, time, slot) {
            // Don't allow any interactions for anonymous users
            if (!this.isAuthenticated) {
                return;
            }

            // Don't allow clicking on past time slots
            if (this.isSlotInPast(time)) {
                return;
            }

            if (slot.status === 'available') {
                this.openBookingModal(court, time);
            } else if (
                (slot.status === 'reserved' || slot.status === 'short_notice') &&
                this.canCancelSlot(slot)
            ) {
                // Handle both test format (reservation) and production format (details)
                const reservation = slot.reservation || slot.details;
                const reservationId = reservation.reservation_id || reservation.id;
                this.cancelReservation(reservationId);
            } else if (slot.status === 'blocked_temporary' && this.canCancelSlot(slot)) {
                // Handle suspended reservation cancellation
                const suspended = slot.details?.suspended_reservation;
                if (suspended) {
                    this.cancelReservation(suspended.reservation_id || suspended.id);
                }
            }
        },

        // Optimized slot click handler using pre-computed server data
        handleSlotClickPrecomputed(courtIndex, timeIndex) {
            const slot = this.courts[courtIndex]?.slots[timeIndex];
            if (!slot) return;

            // Use pre-computed flags from server
            if (slot.isPast) return;
            if (!this.isAuthenticated) return;

            if (slot.status === 'available') {
                const time = this.timeSlots[timeIndex];
                this.openBookingModal(courtIndex + 1, time);
            } else if (slot.canCancel) {
                // For suspended reservations, the ID is in suspended_reservation
                const suspended = slot.details?.suspended_reservation;
                if (suspended) {
                    const reservationId = suspended.reservation_id || suspended.id;
                    if (reservationId) {
                        this.cancelReservation(reservationId);
                    }
                } else {
                    // Regular reservation
                    const reservation = slot.details;
                    const reservationId = reservation?.reservation_id || reservation?.id;
                    if (reservationId) {
                        this.cancelReservation(reservationId);
                    }
                }
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
                const response = await fetch(`/api/reservations/${reservationId}`, {
                    method: 'DELETE',
                    headers: { 'X-CSRFToken': getCsrfToken() },
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

        /**
         * Compute CSS classes for a slot based on status and time.
         * Used when transforming sparse API responses.
         */
        getSlotClass(slot, time) {
            // Use pre-computed class if available (legacy format)
            if (slot.cssClass) {
                return slot.cssClass;
            }

            // Compute classes from status - tile style with rounded corners
            let classes = 'px-2 py-3 text-center text-xs rounded-lg';
            const isPast = this.isSlotInPast(time);

            if (slot.status === 'available') {
                if (isPast) {
                    classes += ' bg-gray-100 text-gray-400 border border-gray-200';
                } else {
                    classes += ' bg-white text-gray-500 border border-gray-200';
                    if (this.isAuthenticated) {
                        classes += ' cursor-pointer hover:bg-gray-50';
                    }
                }
            } else if (slot.status === 'short_notice') {
                classes += ' bg-orange-400 text-black';
                if (!isPast && this.isAuthenticated && this.canCancelSlot(slot)) {
                    classes += ' cursor-pointer hover:opacity-80';
                } else if (isPast) {
                    classes += ' opacity-60';
                }
            } else if (slot.status === 'reserved') {
                const reservation = slot.reservation || slot.details;
                if (reservation && reservation.is_short_notice) {
                    classes += ' bg-orange-400 text-black';
                } else {
                    classes += ' bg-green-500 text-black';
                }
                if (!isPast && this.isAuthenticated && this.canCancelSlot(slot)) {
                    classes += ' cursor-pointer hover:opacity-80';
                } else if (isPast) {
                    classes += ' opacity-60';
                }
            } else if (slot.status === 'blocked_temporary') {
                // Temporary block - yellow/amber color with dark text for readability
                classes += ' bg-yellow-400 text-yellow-900 min-h-16';
                if (!isPast && this.isAuthenticated && this.canCancelSlot(slot)) {
                    classes += ' cursor-pointer hover:opacity-80';
                } else if (isPast) {
                    classes += ' opacity-75';
                }
            } else if (slot.status === 'blocked') {
                classes += ' bg-gray-400 text-white min-h-16';
                if (isPast) {
                    classes += ' opacity-75';
                }
            }

            return classes;
        },

        canCancelSlot(slot) {
            // Anonymous users cannot cancel
            if (!this.isAuthenticated) {
                return false;
            }

            // Handle suspended reservations in temporary blocks
            if (slot.status === 'blocked_temporary') {
                return slot.details?.suspended_reservation?.can_cancel === true;
            }

            // Use server-computed flag for regular reservations
            return slot.details?.can_cancel === true;
        },

        isSlotInPast(time) {
            const today = getToday();

            // If selected date is before today, all slots are in the past
            if (this.selectedDate < today) {
                return true;
            }

            // If selected date is after today, no slots are in the past
            if (this.selectedDate > today) {
                return false;
            }

            // If selected date is today, check the time
            // Get current hour in Berlin timezone
            const berlinHour = parseInt(
                new Date().toLocaleTimeString('de-DE', {
                    timeZone: 'Europe/Berlin',
                    hour: '2-digit',
                    hour12: false,
                }),
                10
            );
            const [slotHour] = time.split(':').map(Number);

            // Slot is in the past only if it's before current hour
            // Current hour is still bookable as short notice booking
            return slotHour < berlinHour;
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

        /**
         * Compute display content for a slot based on status and details.
         * Used when transforming sparse API responses.
         */
        getSlotContent(slot, time) {
            // Use pre-computed content if available (legacy format)
            if (slot.content !== undefined) {
                return slot.content;
            }

            // Compute content from status
            if (slot.status === 'available') {
                return this.isSlotInPast(time) ? '' : 'Frei';
            }

            if (slot.status === 'short_notice' || slot.status === 'reserved') {
                const reservation = slot.reservation || slot.details;
                if (reservation && this.isAuthenticated) {
                    const hasProfilePic = reservation.booked_for_has_profile_picture;

                    if (hasProfilePic) {
                        // Vertical stack: avatar centered on top, name below (iOS style)
                        const avatar = `<img src="/api/members/${reservation.booked_for_id}/profile-picture?v=${reservation.booked_for_profile_picture_version || 0}" alt="" style="width: 28px; height: 28px; border-radius: 9999px; object-fit: cover;" loading="lazy">`;

                        if (reservation.booked_for_id === reservation.booked_by_id) {
                            return `<div class="flex flex-col items-center gap-1">${avatar}<span class="truncate text-[10px] leading-tight">${reservation.booked_for}</span></div>`;
                        }
                        return `<div class="flex flex-col items-center gap-1">${avatar}<span class="truncate text-[10px] leading-tight">${reservation.booked_for}</span><span class="truncate text-[8px] opacity-70 leading-tight">(${reservation.booked_by})</span></div>`;
                    } else {
                        // No profile picture - show only name(s) centered
                        if (reservation.booked_for_id === reservation.booked_by_id) {
                            return `<span class="text-[11px]">${reservation.booked_for}</span>`;
                        }
                        return `<div class="flex flex-col items-center"><span class="text-[11px]">${reservation.booked_for}</span><span class="text-[8px] opacity-70">(${reservation.booked_by})</span></div>`;
                    }
                }
                return 'Gebucht';
            }

            if (slot.status === 'blocked_temporary') {
                const blockDetails = slot.details;
                let content = blockDetails?.reason || 'Vorübergehend gesperrt';
                if (blockDetails?.details?.trim()) {
                    content += `<br><span style="font-size: 0.7em; opacity: 0.9;">${blockDetails.details}</span>`;
                }
                content += `<br><span style="font-size: 0.65em; font-style: italic;">(vorübergehend)</span>`;
                // Show suspended reservation info if available
                if (blockDetails?.suspended_reservation) {
                    const suspended = blockDetails.suspended_reservation;
                    if (suspended.booked_for_has_profile_picture) {
                        const suspendedAvatar = `<img src="/api/members/${suspended.booked_for_id}/profile-picture?v=${suspended.booked_for_profile_picture_version || 0}" alt="" style="width: 16px; height: 16px; border-radius: 9999px; object-fit: cover;" loading="lazy">`;
                        content += `<br><span style="font-size: 0.65em; margin-top: 4px; display: inline-flex; align-items: center; gap: 4px; background: rgba(255,255,255,0.3); padding: 2px 4px; border-radius: 2px;">⏸ ${suspendedAvatar} ${suspended.booked_for}</span>`;
                    } else {
                        content += `<br><span style="font-size: 0.65em; margin-top: 4px; display: inline-block; background: rgba(255,255,255,0.3); padding: 2px 4px; border-radius: 2px;">⏸ ${suspended.booked_for}</span>`;
                    }
                }
                return content;
            }

            if (slot.status === 'blocked') {
                const blockDetails = slot.details;
                if (blockDetails && blockDetails.reason) {
                    let content = blockDetails.reason;
                    if (blockDetails.details && blockDetails.details.trim()) {
                        content += `<br><span style="font-size: 0.7em; opacity: 0.9;">${blockDetails.details}</span>`;
                    }
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
            const regularBookings = this.userReservations.filter((r) => !r.is_short_notice);
            return Math.max(0, 2 - regularBookings.length);
        },

        getShortNoticeSlots() {
            if (!this.userReservations) return 1;

            // Count short notice active booking sessions
            const shortNoticeBookings = this.userReservations.filter((r) => r.is_short_notice);
            return Math.max(0, 1 - shortNoticeBookings.length);
        },
    };
}
