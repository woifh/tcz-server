/**
 * Block Form Management
 * Handles multi-court block creation and editing forms
 */

import { stateManager } from '../core/admin-state.js';
import { blocksAPI } from '../core/admin-api.js';
import { showToast, formUtils, dateUtils } from '../core/admin-utils.js';

// Form validation and submission
export class BlockForm {
    constructor() {
        this.isEditMode = false;
        this.editBlockId = null;
        this.editBatchId = null;
        
        console.log('🏗️ BlockForm constructor called');
        
        this.setupEventListeners();
        
        // Delay initialization to ensure DOM is fully loaded
        setTimeout(() => {
            this.initializeFromDataAttributes();
        }, 100);
        
        // Make this instance globally accessible for debugging
        window.debugBlockForm = this;
        
        console.log('✅ BlockForm initialization complete:', {
            isEditMode: this.isEditMode,
            editBatchId: this.editBatchId,
            editBlockId: this.editBlockId
        });
    }

    setupEventListeners() {
        // Multi-court form
        const multiCourtForm = document.getElementById('multi-court-form');
        if (multiCourtForm) {
            multiCourtForm.addEventListener('submit', (e) => this.handleSubmit(e));
        }

        // Update button event listener (for edit mode)
        const updateBtn = document.getElementById('update-block-btn');
        if (updateBtn) {
            updateBtn.addEventListener('click', (e) => this.handleSubmit(e));
        }

        // Save as New Event button event listener
        const saveAsNewBtn = document.getElementById('clone-block-btn');
        if (saveAsNewBtn) {
            saveAsNewBtn.addEventListener('click', (e) => this.handleSaveAsNew(e));
        }

        // Cancel button event listener
        const cancelBtn = document.getElementById('cancel-btn');
        if (cancelBtn) {
            cancelBtn.addEventListener('click', (e) => this.handleCancel(e));
        }

        // Court selection buttons
        const selectAllBtn = document.getElementById('select-all-courts');
        const clearAllBtn = document.getElementById('clear-all-courts');
        
        if (selectAllBtn) {
            selectAllBtn.addEventListener('click', () => this.selectAllCourts());
        }
        
        if (clearAllBtn) {
            clearAllBtn.addEventListener('click', () => this.clearAllCourts());
        }

        // Form validation
        this.setupFormValidation();
    }

    initializeFromDataAttributes() {
        const form = document.getElementById('multi-court-form');
        if (!form) {
            console.log('❌ Form multi-court-form not found');
            return;
        }

        // Read data attributes to determine edit mode
        const editMode = form.getAttribute('data-edit-mode') === 'true';
        const batchId = form.getAttribute('data-batch-id');
        const blockId = form.getAttribute('data-block-id');

        console.log('🔍 Form data attributes:', {
            editMode: form.getAttribute('data-edit-mode'),
            batchId: form.getAttribute('data-batch-id'),
            blockId: form.getAttribute('data-block-id'),
            parsedEditMode: editMode,
            hasBatchId: !!batchId,
            batchIdLength: batchId ? batchId.length : 0,
            batchIdType: typeof batchId,
            batchIdValue: `"${batchId}"`
        });

        // Initialize edit mode if we have valid data
        if (editMode) {
            this.isEditMode = true;
            this.editBlockId = blockId;
            
            // Try multiple sources for batch_id in order of reliability
            let validBatchId = null;
            
            // 1. Data attribute (most reliable after template fix)
            if (batchId && batchId !== '' && batchId !== 'null' && batchId !== 'None' && batchId !== 'undefined' && batchId.length > 0) {
                validBatchId = batchId;
                console.log('✅ Using batch_id from data attributes:', validBatchId);
            }
            
            // 2. Extract from URL as fallback
            if (!validBatchId) {
                const urlPath = window.location.pathname;
                const match = urlPath.match(/\/admin\/court-blocking\/([a-f0-9-]{36})/);
                if (match) {
                    validBatchId = match[1];
                    console.log('✅ Extracted batch_id from URL:', validBatchId);
                }
            }
            
            // 3. Check window.editBlockData as last resort
            if (!validBatchId && window.editBlockData && window.editBlockData.batch_id) {
                validBatchId = window.editBlockData.batch_id;
                console.log('✅ Using batch_id from window.editBlockData:', validBatchId);
            }
            
            if (validBatchId) {
                this.editBatchId = validBatchId;
                console.log('✅ Initializing form in edit mode:', { editMode, batchId: validBatchId, blockId });
                this.updateFormForEditMode();
            } else {
                console.log('❌ Edit mode detected but no valid batch_id found. Falling back to create mode.');
                this.isEditMode = false;
                this.editBatchId = null;
            }
        } else {
            console.log('ℹ️ Form initialized in create mode:', { editMode, batchId, hasBatchId: !!batchId, batchIdType: typeof batchId });
        }
        
        // CRITICAL: Log the final state after data attribute initialization
        console.log('📊 State after data attribute initialization:', {
            isEditMode: this.isEditMode,
            editBatchId: this.editBatchId,
            editBlockId: this.editBlockId
        });
        
        // Also try to get data from window.editBlockData if available
        if (window.editBlockData) {
            console.log('🔄 Found window.editBlockData, using it to populate form data');
            this.populateEditForm(window.editBlockData);
        } else {
            // Ensure button visibility is correct for create mode
            this.updateButtonVisibility();
        }
        
        // Final state logging
        console.log('📊 Final initialization state:', {
            isEditMode: this.isEditMode,
            editBatchId: this.editBatchId,
            editBlockId: this.editBlockId
        });
    }

    updateFormForEditMode() {
        // Update form data attributes to reflect edit mode
        const form = document.getElementById('multi-court-form');
        if (form) {
            form.setAttribute('data-edit-mode', 'true');
            form.setAttribute('data-batch-id', this.editBatchId || '');
            form.setAttribute('data-block-id', this.editBlockId || '');
        }
        
        // Show/hide appropriate buttons based on mode
        this.updateButtonVisibility();
        
        // Ensure validation runs to enable buttons
        this.validateForm();
        
        console.log('✅ Form updated for edit mode:', {
            isEditMode: this.isEditMode,
            editBatchId: this.editBatchId,
            editBlockId: this.editBlockId
        });
    }

    updateButtonVisibility() {
        const createBtn = document.getElementById('create-block-btn');
        const updateBtn = document.getElementById('update-block-btn');
        const cloneBtn = document.getElementById('clone-block-btn');
        const cancelBtn = document.getElementById('cancel-btn');
        
        if (this.isEditMode) {
            // Edit mode: show update, clone, and cancel buttons; hide create button
            if (createBtn) createBtn.style.display = 'none';
            if (updateBtn) updateBtn.style.display = 'inline-block';
            if (cloneBtn) cloneBtn.style.display = 'inline-block';
            if (cancelBtn) cancelBtn.style.display = 'inline-block';
        } else {
            // Create mode: show create button; hide update, clone, and cancel buttons
            if (createBtn) createBtn.style.display = 'inline-block';
            if (updateBtn) updateBtn.style.display = 'none';
            if (cloneBtn) cloneBtn.style.display = 'none';
            if (cancelBtn) cancelBtn.style.display = 'none';
        }
    }

    setupFormValidation() {
        const courtCheckboxes = document.querySelectorAll('input[name="multi-courts"]');
        const startTimeInput = document.getElementById('multi-start');
        const endTimeInput = document.getElementById('multi-end');
        const reasonSelect = document.getElementById('multi-reason');
        const dateInput = document.getElementById('multi-date');
        
        // Court selection validation
        courtCheckboxes.forEach(cb => {
            cb.addEventListener('change', () => this.validateForm());
        });
        
        // Time validation
        if (startTimeInput && endTimeInput) {
            startTimeInput.addEventListener('change', () => {
                this.validateTimeRange();
                this.validateForm();
            });
            
            endTimeInput.addEventListener('change', () => {
                this.validateTimeRange();
                this.validateForm();
            });
        }
        
        // Other field validation
        if (reasonSelect) {
            reasonSelect.addEventListener('change', () => this.validateForm());
        }
        
        if (dateInput) {
            dateInput.addEventListener('change', () => this.validateForm());
        }
        
        // Initial validation
        this.validateForm();
    }

    validateTimeRange() {
        const startTimeInput = document.getElementById('multi-start');
        const endTimeInput = document.getElementById('multi-end');
        const timeError = document.getElementById('time-error');
        
        if (!startTimeInput || !endTimeInput || !timeError) return;
        
        const startTime = startTimeInput.value;
        const endTime = endTimeInput.value;
        
        if (startTime && endTime) {
            if (!dateUtils.isValidTimeRange(startTime, endTime)) {
                timeError.textContent = 'Endzeit muss nach Startzeit liegen';
                timeError.style.display = 'block';
                startTimeInput.classList.add('is-invalid');
                endTimeInput.classList.add('is-invalid');
                return false;
            } else {
                timeError.style.display = 'none';
                startTimeInput.classList.remove('is-invalid');
                endTimeInput.classList.remove('is-invalid');
                return true;
            }
        }
        
        return true;
    }

    validateForm() {
        const courtCheckboxes = document.querySelectorAll('input[name="multi-courts"]:checked');
        const startTime = document.getElementById('multi-start')?.value;
        const endTime = document.getElementById('multi-end')?.value;
        const reason = document.getElementById('multi-reason')?.value;
        const date = document.getElementById('multi-date')?.value;
        
        // Debug logging
        console.log('🔍 Form validation:', {
            courts: courtCheckboxes.length,
            startTime,
            endTime,
            reason,
            date,
            timeRangeValid: this.validateTimeRange()
        });
        
        const isValid = courtCheckboxes.length > 0 && 
                       startTime && 
                       endTime && 
                       reason && 
                       date && 
                       this.validateTimeRange();
        
        // Enable/disable all form buttons based on validation
        const createBtn = document.getElementById('create-block-btn');
        const updateBtn = document.getElementById('update-block-btn');
        const cloneBtn = document.getElementById('clone-block-btn');
        
        console.log('🔍 Button states:', {
            isValid,
            createBtn: !!createBtn,
            updateBtn: !!updateBtn,
            cloneBtn: !!cloneBtn
        });
        
        if (createBtn) createBtn.disabled = !isValid;
        if (updateBtn) updateBtn.disabled = !isValid;
        if (cloneBtn) cloneBtn.disabled = !isValid;
        
        return isValid;
    }

    selectAllCourts() {
        document.querySelectorAll('input[name="multi-courts"]').forEach(cb => cb.checked = true);
        this.validateForm();
    }

    clearAllCourts() {
        document.querySelectorAll('input[name="multi-courts"]').forEach(cb => cb.checked = false);
        this.validateForm();
    }

    async handleSubmit(event) {
        console.log('🚀 Form submit handler called'); // Debug log
        event.preventDefault();
        
        console.log('📊 Form state at submission:', {
            isEditMode: this.isEditMode,
            editBatchId: this.editBatchId,
            editBlockId: this.editBlockId
        });
        
        if (!this.validateForm()) {
            showToast('Bitte füllen Sie alle erforderlichen Felder aus', 'error');
            return;
        }

        // Manual form data collection
        const selectedCourts = Array.from(document.querySelectorAll('input[name="multi-courts"]:checked')).map(cb => cb.value);

        const blockData = {
            court_ids: selectedCourts,
            date: document.getElementById('multi-date')?.value,
            start_time: document.getElementById('multi-start')?.value,
            end_time: document.getElementById('multi-end')?.value,
            reason_id: document.getElementById('multi-reason')?.value,
            details: document.getElementById('multi-details')?.value || ''
        };

        console.log('📤 Submitting block data:', blockData);

        // Validate that reason_id is set
        if (!blockData.reason_id) {
            showToast('Bitte wählen Sie einen Grund aus', 'error');
            return;
        }

        try {
            let result;
            
            // Final validation: ensure we have a valid batch_id for edit mode
            if (this.isEditMode && (!this.editBatchId || this.editBatchId === 'null' || this.editBatchId === 'undefined' || this.editBatchId === '')) {
                console.log('❌ Edit mode detected but no valid batch_id found. Attempting to re-read data attributes...');
                
                // Try one more time to get batch_id from data attributes
                const form = document.getElementById('multi-court-form');
                if (form) {
                    const dataAttributeBatchId = form.getAttribute('data-batch-id');
                    if (dataAttributeBatchId && dataAttributeBatchId !== '' && dataAttributeBatchId !== 'null' && dataAttributeBatchId !== 'None' && dataAttributeBatchId !== 'undefined') {
                        this.editBatchId = dataAttributeBatchId;
                        console.log('✅ Recovered batch_id from data attributes:', dataAttributeBatchId);
                    } else {
                        console.log('❌ No valid batch_id in data attributes either. Falling back to create mode.');
                        this.isEditMode = false;
                    }
                }
            }
            
            if (this.isEditMode && this.editBatchId) {
                console.log('🔄 Using batch update (PUT) for batch:', this.editBatchId);
                // Use batch update for editing existing blocks
                result = await blocksAPI.update(this.editBatchId, blockData);
            } else {
                console.log('➕ Using create (POST)');
                // Create new block(s)
                result = await blocksAPI.create(blockData);
                
                // Debug: log the full response structure
                console.log('🔍 Full API response:', result);
                console.log('🔍 Response data:', result.data);
                console.log('🔍 Looking for batch_id in result.data:', result.data);
            }

            if (result.success) {
                const message = this.isEditMode 
                    ? 'Sperrung erfolgreich aktualisiert' 
                    : 'Sperrung erfolgreich erstellt';
                showToast(message, 'success');
                
                // For updates: keep the form data and stay in edit mode
                // For new creations: redirect to the edit page
                if (this.isEditMode) {
                    // Stay in edit mode with current data - no changes needed
                    console.log('✅ Update successful - staying in edit mode');
                    
                    // Reload blocks list
                    if (window.loadUpcomingBlocks) {
                        window.loadUpcomingBlocks();
                    }
                } else {
                    // New event created - redirect to edit page
                    if (result.data && result.data.batch_id) {
                        console.log('✅ New event created - redirecting to edit page');
                        window.location.href = `/admin/court-blocking/${result.data.batch_id}`;
                    } else {
                        console.log('⚠️ New event created but no batch_id returned');
                        console.log('🔍 Full response:', result);
                        // Fallback: reload blocks list
                        if (window.loadUpcomingBlocks) {
                            window.loadUpcomingBlocks();
                        }
                    }
                }
                
                // Don't close modal - keep form open for further editing (only for updates)
            } else {
                showToast(result.error || 'Fehler beim Speichern der Sperrung', 'error');
            }
        } catch (error) {
            console.error('❌ Error submitting form:', error);
            showToast('Fehler beim Speichern der Sperrung', 'error');
        }
    }

    async handleSaveAsNew(event) {
        console.log('🚀 Save as New Event handler called');
        event.preventDefault();
        
        if (!this.validateForm()) {
            showToast('Bitte füllen Sie alle erforderlichen Felder aus', 'error');
            return;
        }

        // Collect form data (same as regular submit)
        const selectedCourts = Array.from(document.querySelectorAll('input[name="multi-courts"]:checked')).map(cb => cb.value);

        const blockData = {
            court_ids: selectedCourts,
            date: document.getElementById('multi-date')?.value,
            start_time: document.getElementById('multi-start')?.value,
            end_time: document.getElementById('multi-end')?.value,
            reason_id: document.getElementById('multi-reason')?.value,
            details: document.getElementById('multi-details')?.value || ''
        };

        console.log('📤 Submitting new event data:', blockData);

        // Validate that reason_id is set
        if (!blockData.reason_id) {
            showToast('Bitte wählen Sie einen Grund aus', 'error');
            return;
        }

        try {
            // Always use POST for "Save as New Event" (create new event)
            console.log('➕ Using create (POST) for new event');
            const result = await blocksAPI.create(blockData);
            
            // Debug: log the full response structure
            console.log('🔍 Full API response (Save as New):', result);
            console.log('🔍 Response data (Save as New):', result.data);
            console.log('🔍 Looking for batch_id in result.data:', result.data);

            if (result.success) {
                showToast('Neue Sperrung erfolgreich erstellt', 'success');
                
                // Redirect to edit page for the newly created event
                if (result.data && result.data.batch_id) {
                    console.log('✅ New event created from existing - redirecting to edit page');
                    window.location.href = `/admin/court-blocking/${result.data.batch_id}`;
                } else {
                    console.log('⚠️ New event created but no batch_id returned');
                    console.log('🔍 Full response:', result);
                }
                
                // Don't reload blocks list or close modal - we're redirecting
            } else {
                showToast(result.error || 'Fehler beim Erstellen der neuen Sperrung', 'error');
            }
        } catch (error) {
            console.error('❌ Error creating new event:', error);
            showToast('Fehler beim Erstellen der neuen Sperrung', 'error');
        }
    }

    handleCancel(event) {
        console.log('🚀 Cancel handler called');
        event.preventDefault();
        
        // Clear the form completely and reset to create mode
        this.resetForm();
        
        // Navigate back to the main court blocking page
        window.location.href = '/admin/court-blocking';
    }

    populateEditForm(blockData) {
        console.log('🔄 populateEditForm called with data:', blockData);
        
        this.isEditMode = true;
        this.editBlockId = blockData.id;
        
        // CRITICAL FIX: Use the batch_id that was already set during initialization
        // Only override if we don't have a valid batch_id yet
        if (!this.editBatchId && blockData.batch_id && blockData.batch_id !== 'undefined' && blockData.batch_id !== '' && blockData.batch_id !== 'null' && blockData.batch_id !== 'None') {
            this.editBatchId = blockData.batch_id;
            console.log('📝 Set batch_id from blockData:', blockData.batch_id);
        }
        
        console.log('📝 Edit mode set via populateEditForm - Block ID:', this.editBlockId, 'Batch ID:', this.editBatchId);
        
        // Set form values
        const dateInput = document.getElementById('multi-date');
        const startTimeInput = document.getElementById('multi-start');
        const endTimeInput = document.getElementById('multi-end');
        const reasonSelect = document.getElementById('multi-reason');
        const detailsInput = document.getElementById('multi-details');
        const descriptionInput = document.getElementById('multi-description');
        
        if (dateInput) dateInput.value = blockData.date;
        if (startTimeInput) startTimeInput.value = blockData.start_time;
        if (endTimeInput) endTimeInput.value = blockData.end_time;
        if (reasonSelect) reasonSelect.value = blockData.reason_id;
        if (detailsInput) detailsInput.value = blockData.details || '';
        if (descriptionInput) descriptionInput.value = blockData.description || '';
        
        // Set selected courts - use court_ids from batch data
        if (blockData.court_ids) {
            document.querySelectorAll('input[name="multi-courts"]').forEach(cb => {
                cb.checked = blockData.court_ids.includes(parseInt(cb.value));
            });
        } else if (blockData.courts) {
            // Fallback for old format
            document.querySelectorAll('input[name="multi-courts"]').forEach(cb => {
                cb.checked = blockData.courts.includes(parseInt(cb.value));
            });
        }
        
        // Update form UI for edit mode
        this.updateFormForEditMode();
        
        this.validateForm();
        
        console.log('✅ populateEditForm completed. Final state:', {
            isEditMode: this.isEditMode,
            editBatchId: this.editBatchId,
            editBlockId: this.editBlockId
        });
    }

    resetForm() {
        this.isEditMode = false;
        this.editBlockId = null;
        this.editBatchId = null;
        
        const form = document.getElementById('multi-court-form');
        if (form) {
            formUtils.clearForm(form);
            // Reset data attributes
            form.setAttribute('data-edit-mode', 'false');
            form.setAttribute('data-batch-id', '');
            form.setAttribute('data-block-id', '');
        }
        
        // Update button visibility for create mode
        this.updateButtonVisibility();
        
        // Set default date
        const dateInput = document.getElementById('multi-date');
        if (dateInput) {
            dateInput.value = dateUtils.getTodayString();
        }
        
        // Ensure end time field is enabled
        const endTimeInput = document.getElementById('multi-end');
        if (endTimeInput) {
            endTimeInput.disabled = false;
        }
        
        this.validateForm();
        
        console.log('✅ Form reset to create mode');
    }

    // Debug method to manually check data attributes
    debugDataAttributes() {
        const form = document.getElementById('multi-court-form');
        if (!form) {
            console.log('❌ Form not found');
            return;
        }
        
        const attrs = {
            'data-edit-mode': form.getAttribute('data-edit-mode'),
            'data-batch-id': form.getAttribute('data-batch-id'),
            'data-block-id': form.getAttribute('data-block-id'),
            'data-related-block-ids': form.getAttribute('data-related-block-ids')
        };
        
        console.log('🔍 Current form data attributes:', attrs);
        console.log('🔍 Current form state:', {
            isEditMode: this.isEditMode,
            editBatchId: this.editBatchId,
            editBlockId: this.editBlockId
        });
        
        // Also check window.editBlockData
        if (window.editBlockData) {
            console.log('🔍 window.editBlockData:', window.editBlockData);
        } else {
            console.log('❌ window.editBlockData not found');
        }
        
        // Check the form HTML
        console.log('🔍 Form element HTML (first 500 chars):');
        console.log(form.outerHTML.substring(0, 500));
        
        return attrs;
    }

    // Debug method to manually fix the batch_id
    fixBatchId() {
        const form = document.getElementById('multi-court-form');
        if (!form) {
            console.log('❌ Form not found');
            return false;
        }
        
        let batchId = null;
        
        // Try multiple sources for batch_id
        // 1. Data attributes
        const dataAttributeBatchId = form.getAttribute('data-batch-id');
        if (dataAttributeBatchId && dataAttributeBatchId !== '' && dataAttributeBatchId !== 'null' && dataAttributeBatchId !== 'None' && dataAttributeBatchId !== 'undefined') {
            batchId = dataAttributeBatchId;
            console.log('✅ Found batch_id in data attributes:', batchId);
        }
        
        // 2. window.editBlockData
        if (!batchId && window.editBlockData && window.editBlockData.batch_id) {
            batchId = window.editBlockData.batch_id;
            console.log('✅ Found batch_id in window.editBlockData:', batchId);
        }
        
        // 3. Extract from URL as last resort
        if (!batchId) {
            const urlPath = window.location.pathname;
            const match = urlPath.match(/\/admin\/court-blocking\/([a-f0-9-]{36})/);
            if (match) {
                batchId = match[1];
                console.log('✅ Extracted batch_id from URL:', batchId);
            }
        }
        
        if (batchId) {
            this.editBatchId = batchId;
            this.isEditMode = true;
            console.log('✅ Fixed! editBatchId set to:', this.editBatchId);
            console.log('✅ Edit mode enabled');
            return true;
        } else {
            console.log('❌ No valid batch_id found in any source');
            return false;
        }
    }
    initializeForm() {
        const today = dateUtils.getTodayString();
        
        // Set default date for multi-court form
        const multiDateInput = document.getElementById('multi-date');
        if (multiDateInput) {
            multiDateInput.value = today;
        }
        
        // Set default start time to 08:00
        const startTimeInput = document.getElementById('multi-start');
        if (startTimeInput) {
            startTimeInput.value = '08:00';
        }
        
        // Set default end time to 22:00
        const endTimeInput = document.getElementById('multi-end');
        if (endTimeInput) {
            endTimeInput.disabled = false;
            endTimeInput.value = '22:00';
        }
        
        this.validateForm();
    }
}

// Export singleton instance
export const blockForm = new BlockForm();