/**
 * Block Management Module
 * Handles block operations, batch operations, and related modals
 */

import { blocksAPI } from './admin-api.js';
import { showToast, dateUtils } from './admin-utils.js';

export class BlocksManager {
    constructor() {
        this.currentBlocks = [];
    }

    /**
     * Load and display upcoming blocks
     */
    async loadUpcomingBlocks() {
        const blocksList = document.getElementById('blocks-list');
        if (!blocksList) return;

        // Show loading state
        blocksList.innerHTML = `
            <div class="p-4 text-center text-gray-600">
                <div class="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-green-600 mr-2"></div>
                Lade Sperrungen...
            </div>
        `;

        try {
            const today = dateUtils.getTodayString();
            const nextMonth = dateUtils.getDatePlusDays(30);

            const result = await blocksAPI.load({
                date_range_start: today,
                date_range_end: nextMonth
            });

            if (result.success) {
                this.displayUpcomingBlocks(result.blocks);
            } else {
                blocksList.innerHTML = `
                    <div class="p-4 text-center text-red-600">
                        Fehler beim Laden der Sperrungen: ${result.error || 'Unbekannter Fehler'}
                    </div>
                `;
            }
        } catch (error) {
            console.error('Error loading upcoming blocks:', error);
            blocksList.innerHTML = `
                <div class="p-4 text-center text-red-600">
                    Fehler beim Laden der Sperrungen
                </div>
            `;
        }
    }

    /**
     * Display upcoming blocks in a list
     */
    displayUpcomingBlocks(blocks) {
        const blocksList = document.getElementById('blocks-list');
        if (!blocksList) return;

        if (blocks.length === 0) {
            blocksList.innerHTML = `
                <div class="p-4 text-center text-gray-600">
                    Keine kommenden Sperrungen gefunden.
                </div>
            `;
            return;
        }

        // Group blocks by batch
        const groupedBlocks = this.groupBlocksByBatch(blocks);

        let html = '<div class="divide-y divide-gray-200">';

        groupedBlocks.forEach(group => {
            html += this.renderBlockGroup(group);
        });

        html += '</div>';
        blocksList.innerHTML = html;
    }

    /**
     * Group blocks by batch using batch_id
     */
    groupBlocksByBatch(blocks) {
        const groups = new Map();

        blocks.forEach(block => {
            const key = `batch_${block.batch_id}`;

            if (!groups.has(key)) {
                groups.set(key, {
                    key: key,
                    blocks: []
                });
            }

            groups.get(key).blocks.push(block);
        });

        // Convert to array and sort by date/time
        return Array.from(groups.values()).sort((a, b) => {
            const dateA = new Date(`${a.blocks[0].date}T${a.blocks[0].start_time}`);
            const dateB = new Date(`${b.blocks[0].date}T${b.blocks[0].start_time}`);
            return dateA - dateB;
        });
    }

    /**
     * Render a block group
     */
    renderBlockGroup(group) {
        const firstBlock = group.blocks[0];
        const date = dateUtils.formatDate(firstBlock.date);
        const startTime = firstBlock.start_time.slice(0, 5);
        const endTime = firstBlock.end_time.slice(0, 5);

        // Sort court numbers
        const courtNumbers = group.blocks.map(b => b.court_number).sort((a, b) => a - b);

        // Format court display
        let courtsDisplay;
        if (courtNumbers.length === 1) {
            courtsDisplay = `Platz ${courtNumbers[0]}`;
        } else if (courtNumbers.length === 2) {
            courtsDisplay = `Plätze ${courtNumbers.join(' & ')}`;
        } else {
            courtsDisplay = `Plätze ${courtNumbers.join(', ')}`;
        }

        // Use batch_id directly without prefix
        const batchId = firstBlock.batch_id;

        return `
            <div class="p-4 hover:bg-gray-50 flex items-center justify-between">
                <div class="flex-1">
                    <div class="flex items-center gap-4">
                        <div class="font-medium text-gray-900">
                            ${courtsDisplay}
                        </div>
                        <div class="text-gray-600">
                            ${date} • ${startTime} - ${endTime}
                        </div>
                        <div class="text-sm text-gray-500">
                            ${firstBlock.reason_name}${firstBlock.details ? ' • ' + firstBlock.details : ''}
                        </div>
                        ${group.blocks.length > 1 ? `
                            <div class="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                                ${group.blocks.length} Plätze
                            </div>
                        ` : ''}
                    </div>
                </div>
                <div class="flex items-center gap-2">
                    <button onclick="window.blocksManager.editBatch('${batchId}')" class="text-blue-600 hover:text-blue-800 text-sm">
                        Bearbeiten
                    </button>
                    <button onclick="window.blocksManager.deleteBatch('${batchId}')" class="text-red-600 hover:text-red-800 text-sm">
                        Löschen
                    </button>
                </div>
            </div>
        `;
    }

    /**
     * Edit a batch of blocks
     */
    editBatch(batchId) {
        // Navigate to edit page with batch_id (no prefix needed)
        window.location.href = `/admin/court-blocking/${batchId}`;
    }

    /**
     * Delete a batch of blocks with confirmation
     */
    async deleteBatch(batchId) {
        if (!batchId) {
            showToast('Fehler: Keine Batch-ID gefunden', 'error');
            return;
        }

        try {
            // Load batch details
            const today = dateUtils.getTodayString();
            const nextMonth = dateUtils.getDatePlusDays(30);

            const response = await fetch(`/admin/blocks?date_range_start=${today}&date_range_end=${nextMonth}`);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Fehler beim Laden der Sperrungen');
            }

            // Find all blocks with this batch_id
            const batchBlocks = data.blocks.filter(block => block.batch_id === batchId);

            if (batchBlocks.length === 0) {
                showToast('Keine Sperrungen mit dieser Batch-ID gefunden', 'error');
                return;
            }

            // Show confirmation modal
            this.showBatchDeleteConfirmation(batchId, batchBlocks);

        } catch (error) {
            console.error('Error loading batch details:', error);
            showToast('Fehler beim Laden der Sperrungsdetails', 'error');
        }
    }

    /**
     * Show batch delete confirmation modal
     */
    showBatchDeleteConfirmation(batchId, batchBlocks) {
        const isMultiCourt = batchBlocks.length > 1;
        const courtNumbers = batchBlocks.map(b => b.court_number).sort((a, b) => a - b);
        const firstBlock = batchBlocks[0];

        const date = dateUtils.formatDate(firstBlock.date);
        const startTime = firstBlock.start_time.slice(0, 5);
        const endTime = firstBlock.end_time.slice(0, 5);

        let courtsDisplay;
        if (courtNumbers.length === 1) {
            courtsDisplay = `Platz ${courtNumbers[0]}`;
        } else if (courtNumbers.length === 2) {
            courtsDisplay = `Plätze ${courtNumbers.join(' & ')}`;
        } else {
            courtsDisplay = `Plätze ${courtNumbers.join(', ')}`;
        }

        const modal = document.createElement('div');
        modal.id = 'batch-delete-modal';
        modal.className = 'fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50';

        modal.innerHTML = `
            <div class="bg-white rounded-lg p-6 max-w-md w-full mx-4">
                <div class="flex items-center mb-4">
                    <div class="flex-shrink-0 w-10 h-10 bg-red-100 rounded-full flex items-center justify-center">
                        <svg class="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"></path>
                        </svg>
                    </div>
                    <div class="ml-4">
                        <h3 class="text-lg font-medium text-gray-900">Sperrung löschen</h3>
                    </div>
                </div>

                <div class="mb-4">
                    <p class="text-sm text-gray-600 mb-3">
                        Möchten Sie diese Sperrung wirklich löschen?
                    </p>

                    <div class="bg-gray-50 rounded-lg p-3">
                        <div class="font-medium text-gray-900">${courtsDisplay}</div>
                        <div class="text-sm text-gray-600">${date} • ${startTime} - ${endTime}</div>
                        <div class="text-sm text-gray-500">${firstBlock.reason_name}${firstBlock.details ? ' • ' + firstBlock.details : ''}</div>
                        ${isMultiCourt ? `<div class="text-xs text-blue-600 mt-1">${batchBlocks.length} Plätze betroffen</div>` : ''}
                    </div>
                </div>

                <div class="flex gap-3">
                    <button onclick="window.blocksManager.confirmBatchDelete('${batchId}')" class="flex-1 bg-red-600 text-white py-2 px-4 rounded hover:bg-red-700">
                        ${isMultiCourt ? `${batchBlocks.length} Sperrungen löschen` : 'Sperrung löschen'}
                    </button>
                    <button onclick="window.blocksManager.closeBatchDeleteConfirmation()" class="flex-1 bg-gray-300 text-gray-700 py-2 px-4 rounded hover:bg-gray-400">
                        Abbrechen
                    </button>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
    }

    /**
     * Close batch delete confirmation modal
     */
    closeBatchDeleteConfirmation() {
        const modal = document.getElementById('batch-delete-modal');
        if (modal) {
            modal.remove();
        }
    }

    /**
     * Confirm and execute batch delete
     */
    async confirmBatchDelete(batchId) {
        this.closeBatchDeleteConfirmation();

        try {
            const response = await fetch(`/admin/blocks/${batchId}`, {
                method: 'DELETE'
            });

            const data = await response.json();

            if (response.ok) {
                showToast(data.message || 'Batch-Sperrung erfolgreich gelöscht', 'success');
                await this.loadUpcomingBlocks();
            } else {
                showToast(data.error || 'Fehler beim Löschen der Batch-Sperrung', 'error');
            }
        } catch (error) {
            console.error('Error deleting batch:', error);
            showToast('Fehler beim Löschen der Batch-Sperrung', 'error');
        }
    }

    /**
     * Duplicate a block
     */
    async duplicateBlock(blockId) {
        try {
            const response = await fetch(`/admin/blocks/${blockId}`);
            const data = await response.json();

            if (!response.ok || !data.block) {
                showToast(data.error || 'Block-Daten nicht gefunden', 'error');
                return;
            }

            const block = data.block;

            // Populate form with block data
            document.getElementById('multi-date').value = block.date;
            document.getElementById('multi-start').value = block.start_time;
            document.getElementById('multi-end').value = block.end_time;
            document.getElementById('multi-reason').value = block.reason_id;
            document.getElementById('multi-details').value = block.details || '';

            // Select the court
            const courtCheckbox = document.querySelector(`input[name="multi-courts"][value="${block.court_id}"]`);
            if (courtCheckbox) {
                courtCheckbox.checked = true;
            }

            // Scroll to form
            const form = document.getElementById('multi-court-form');
            if (form) {
                form.scrollIntoView({ behavior: 'smooth' });
            }

            showToast('Block-Daten in Formular geladen', 'info');
        } catch (error) {
            showToast('Fehler beim Laden der Sperrung', 'error');
        }
    }
}

// Create singleton instance
export const blocksManager = new BlocksManager();
