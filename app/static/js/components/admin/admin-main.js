/**
 * Main Admin Panel Module
 * Coordinates all admin functionality and initializes components
 */

// Core imports
import { stateManager } from './core/admin-state.js';
import { blockReasonsAPI } from './core/admin-api.js';
import { showToast } from './core/admin-utils.js';
import { blocksManager } from './core/blocks-manager.js';
import { showTab, modalUtils, getReasonColor, loadingUtils } from './core/ui-helpers.js';

// Form imports
import { blockForm } from './forms/block-form.js';
import { reasonForm } from './forms/reason-form.js';

// Filtering imports
import { blockFilters } from './filtering/block-filters.js';

// Calendar imports
import { calendarView } from './calendar/calendar-view.js';

export class AdminPanel {
    constructor() {
        this.isInitialized = false;
    }

    async initialize() {
        if (this.isInitialized) return;

        try {
            // Load initial data
            await this.loadInitialData();
            
            // Initialize components
            this.initializeComponents();
            
            // Setup global event listeners
            this.setupGlobalEventListeners();
            
            // Initialize forms with default values
            this.initializeForms();
            
            // Load blocks
            await this.loadUpcomingBlocks();
            
            // Handle edit mode if edit block data is available
            if (window.editBlockData) {
                blockForm.populateEditForm(window.editBlockData);
            }
            
            // Initialize filters from URL
            blockFilters.initializeFromUrl();
            
            this.isInitialized = true;
            
            console.log('Admin panel initialized successfully');
        } catch (error) {
            console.error('Error initializing admin panel:', error);
            showToast('Fehler beim Initialisieren des Admin-Panels', 'error');
        }
    }

    async loadInitialData() {
        // Load block reasons
        const reasonsResult = await blockReasonsAPI.load();
        if (reasonsResult.success) {
            stateManager.setBlockReasons(reasonsResult.reasons);
            // Update all reason dropdowns on the page
            reasonForm.updateReasonSelects();
        } else {
            console.error('Failed to load block reasons:', reasonsResult.error);
            showToast('Fehler beim Laden der Gründe', 'error');
        }
    }

    initializeComponents() {
        // Forms are already initialized via imports
        // Bulk operations are already initialized via imports
        // Filters are already initialized via imports
        
        // Initialize calendar if container exists
        const calendarContainer = document.getElementById('calendar-container');
        if (calendarContainer) {
            calendarView.initialize();
        }
    }

    setupGlobalEventListeners() {
        // Global event listeners can be added here if needed
    }

    initializeForms() {
        blockForm.initializeForm();
    }

    async loadUpcomingBlocks() {
        // Delegate to blocksManager
        await blocksManager.loadUpcomingBlocks();
    }

    // Global functions that need to be accessible from HTML
    setupGlobalFunctions() {
        // Make functions available globally for onclick handlers
        window.deleteBatch = (batchId) => blocksManager.deleteBatch(batchId);
        window.loadUpcomingBlocks = () => blocksManager.loadUpcomingBlocks();

        // Block manager functions
        window.blocksManager = blocksManager;

        // Form functions
        window.blockForm = blockForm;
        window.reasonForm = reasonForm;

        // Filter functions
        window.blockFilters = blockFilters;

        // Calendar functions
        window.calendarView = calendarView;

        // UI helper functions
        window.showTab = showTab;
        window.modalUtils = modalUtils;
        window.getReasonColor = getReasonColor;
        window.loadingUtils = loadingUtils;

        // Legacy function names for backward compatibility
        window.loadBlockReasons = () => reasonForm.loadReasons();
    }
}

// Create and initialize admin panel
const adminPanel = new AdminPanel();

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        adminPanel.setupGlobalFunctions();
        adminPanel.initialize();
    });
} else {
    adminPanel.setupGlobalFunctions();
    adminPanel.initialize();
}

// Export for external access
export { adminPanel };