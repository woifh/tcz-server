/**
 * Alpine.js Application Entry Point
 * Imports and registers all Alpine components and stores
 */

import { dashboard } from './components/dashboard.js';
import { bookingModal } from './components/booking-modal.js';
import './components/favourites-store.js';

// Make components globally available for Alpine
window.dashboard = dashboard;
window.bookingModal = bookingModal;

// Initialize Alpine when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    console.log('Alpine.js Tennis Club App initialized');
});
