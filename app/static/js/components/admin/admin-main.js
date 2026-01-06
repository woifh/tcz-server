/**
 * Main Admin Panel Module
 * Coordinates all admin functionality and initializes components
 */

// Core imports
import { stateManager } from './core/admin-state.js';
import { blockReasonsAPI, blocksAPI } from './core/admin-api.js';
import { showToast, dateUtils } from './core/admin-utils.js';

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
        try {
            const filters = stateManager.getCurrentFilters();
            
            // If no date filters are set, default to upcoming blocks
            if (!filters.date_range_start && !filters.date_range_end) {
                filters.date_range_start = dateUtils.getTodayString();
                filters.date_range_end = dateUtils.getDatePlusDays(30);
            }

            const result = await blocksAPI.load(filters);
            
            if (result.success) {
                this.renderBlocksList(result.blocks);
            } else {
                showToast(result.error || 'Fehler beim Laden der Sperrungen', 'error');
            }
        } catch (error) {
            console.error('Error loading blocks:', error);
            showToast('Fehler beim Laden der Sperrungen', 'error');
        }
    }

    renderBlocksList(blocks) {
        const container = document.getElementById('upcoming-blocks-list') || document.getElementById('blocks-list');
        if (!container) return;

        if (blocks.length === 0) {
            container.innerHTML = `
                <div class="text-center py-4">
                    <p class="text-muted">Keine Sperrungen gefunden.</p>
                </div>
            `;
            return;
        }

        // Group blocks by batch_id
        const batches = this.groupBlocksByBatch(blocks);
        
        const html = Object.keys(batches).map(batchId => {
            const batchBlocks = batches[batchId];
            return this.renderBatchGroup(batchId, batchBlocks);
        }).join('');

        container.innerHTML = html;
    }

    groupBlocksByBatch(blocks) {
        const batches = {};

        blocks.forEach(block => {
            const batchId = block.batch_id;
            if (!batches[batchId]) {
                batches[batchId] = [];
            }
            batches[batchId].push(block);
        });

        return batches;
    }

    renderEditDeleteButtons(block, batchId) {
        // Check if current user can edit this block
        // Admin can edit all blocks, teamster can only edit blocks they created
        const canEdit = window.currentUserIsAdmin ||
                       (window.currentUserIsTeamster && block.created_by_id === window.currentUserId);

        if (!canEdit) {
            // Return empty string - no buttons for blocks user cannot edit
            return '';
        }

        // User can edit - show both edit and delete buttons
        return `
            <a href="/admin/court-blocking/${batchId}" class="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700">
                Bearbeiten
            </a>
            <button class="px-3 py-1 text-sm bg-red-600 text-white rounded hover:bg-red-700" onclick="deleteBatch('${batchId}')">
                Löschen
            </button>
        `;
    }

    renderBatchGroup(batchId, blocks) {
        const firstBlock = blocks[0];
        const courtNumbers = blocks.map(b => b.court_number || b.court_id).sort((a, b) => a - b).join(', ');
        const blockCount = blocks.length;
        
        // Determine if this is a past, current, or future block
        const now = new Date();
        const blockDate = new Date(`${firstBlock.date}T${firstBlock.end_time}`);
        const isPast = blockDate < now;
        const isToday = firstBlock.date === dateUtils.getTodayString();
        
        let statusClass = '';
        let statusText = '';
        
        if (isPast) {
            statusClass = 'past-block';
            statusText = 'Vergangen';
        } else if (isToday) {
            statusClass = 'today-block';
            statusText = 'Heute';
        } else {
            statusClass = 'future-block';
            statusText = 'Geplant';
        }

        return `
            <div class="bg-white border border-gray-200 rounded-lg p-4 mb-3 block-batch ${statusClass}" data-batch-id="${batchId}">
                <div class="flex items-center justify-between">
                    <div>
                        <div class="flex items-center space-x-2 mb-1">
                            <h6 class="font-semibold text-gray-900">
                                ${firstBlock.reason_name || 'Unbekannter Grund'}
                            </h6>
                            <span class="px-2 py-1 text-xs font-medium bg-gray-100 text-gray-800 rounded">${statusText}</span>
                            ${blockCount > 1 ? `<span class="px-2 py-1 text-xs font-medium bg-blue-100 text-blue-800 rounded">${blockCount} Plätze</span>` : ''}
                        </div>
                        <p class="text-sm text-gray-600 mb-1">
                            <strong>${dateUtils.formatDate(firstBlock.date)}</strong> 
                            von <strong>${dateUtils.formatTime(firstBlock.start_time)}</strong> 
                            bis <strong>${dateUtils.formatTime(firstBlock.end_time)}</strong>
                        </p>
                        <p class="text-sm text-gray-500 mb-1">
                            Plätze: ${courtNumbers || 'Unbekannt'}
                        </p>
                        ${firstBlock.details ? `
                            <p class="text-sm text-gray-500 mb-1">
                                Details: ${firstBlock.details}
                            </p>
                        ` : ''}
                        <p class="text-xs text-gray-400">
                            Batch ID: ${batchId}
                        </p>
                    </div>
                    <div class="flex space-x-2">
                        ${this.renderEditDeleteButtons(firstBlock, batchId)}
                    </div>
                </div>
            </div>
        `;
    }

    // Global functions that need to be accessible from HTML
    setupGlobalFunctions() {
        // Make functions available globally for onclick handlers
        window.deleteBatch = (batchId) => this.deleteBatch(batchId);
        window.loadUpcomingBlocks = () => this.loadUpcomingBlocks();
        window.renderBlocksList = (blocks) => this.renderBlocksList(blocks);

        // Form functions
        window.blockForm = blockForm;
        window.reasonForm = reasonForm;

        // Filter functions
        window.blockFilters = blockFilters;

        // Calendar functions
        window.calendarView = calendarView;

        // Legacy function names for backward compatibility
        window.loadBlockReasons = () => reasonForm.loadReasons();
    }

    async deleteBatch(batchId) {
        if (!confirm('Möchten Sie diese Sperrung wirklich löschen?')) {
            return;
        }

        try {
            const response = await fetch(`/admin/blocks/${batchId}`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            const result = await response.json();

            if (result.success) {
                showToast('Sperrung erfolgreich gelöscht', 'success');
                await this.loadUpcomingBlocks();
            } else {
                showToast(result.error || 'Fehler beim Löschen', 'error');
            }
        } catch (error) {
            console.error('Error deleting batch:', error);
            showToast('Fehler beim Löschen der Sperrung', 'error');
        }
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