/**
 * Reason Form Management
 * Handles block reason creation and management
 */

import { blockReasonsAPI } from '../core/admin-api.js';
import { showToast, formUtils } from '../core/admin-utils.js';
import { stateManager } from '../core/admin-state.js';

export class ReasonForm {
    constructor() {
        this.setupEventListeners();
    }

    setupEventListeners() {
        const reasonForm = document.getElementById('reason-form');
        if (reasonForm) {
            reasonForm.addEventListener('submit', (e) => this.handleSubmit(e));
        }

        // Setup form validation
        this.setupFormValidation();
    }

    setupFormValidation() {
        const form = document.getElementById('reason-form');
        if (!form) return;

        const inputs = form.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            input.addEventListener('change', () => this.validateForm());
            input.addEventListener('input', () => this.validateForm());
        });

        // Initial validation
        this.validateForm();
    }

    validateForm() {
        const form = document.getElementById('reason-form');
        if (!form) return false;

        const reasonName = form.querySelector('#reason-name')?.value;
        const isValid = reasonName && reasonName.trim() !== '';

        const submitBtn = form.querySelector('button[type="submit"]');
        if (submitBtn) {
            submitBtn.disabled = !isValid;
        }

        return isValid;
    }

    async handleSubmit(event) {
        event.preventDefault();
        
        if (!this.validateForm()) {
            showToast('Bitte geben Sie einen Grund-Namen ein', 'error');
            return;
        }

        const formData = formUtils.getFormData(event.target);
        
        const reasonData = {
            name: formData['reason-name'],
            description: formData['reason-description'] || '',
            color: formData['reason-color'] || '#007bff',
            is_active: formData['reason-active'] !== undefined
        };

        try {
            const result = await blockReasonsAPI.create(reasonData);

            if (result.success) {
                showToast('Grund erfolgreich erstellt', 'success');
                
                // Reset form and reload reasons
                this.resetForm();
                await this.loadReasons();
                
                // Close modal if it exists
                const modal = document.getElementById('reason-modal');
                if (modal && window.bootstrap) {
                    const bsModal = window.bootstrap.Modal.getInstance(modal);
                    if (bsModal) bsModal.hide();
                }
            } else {
                showToast(result.error || 'Fehler beim Erstellen des Grundes', 'error');
            }
        } catch (error) {
            console.error('Error creating reason:', error);
            showToast('Fehler beim Erstellen des Grundes', 'error');
        }
    }

    resetForm() {
        const form = document.getElementById('reason-form');
        if (form) {
            formUtils.clearForm(form);
            
            // Set default color
            const colorInput = form.querySelector('#reason-color');
            if (colorInput) {
                colorInput.value = '#007bff';
            }
            
            // Set default active state
            const activeCheckbox = form.querySelector('#reason-active');
            if (activeCheckbox) {
                activeCheckbox.checked = true;
            }
            
            this.validateForm();
        }
    }

    async loadReasons() {
        try {
            const result = await blockReasonsAPI.load();
            
            if (result.success) {
                stateManager.setBlockReasons(result.reasons);
                this.renderReasonList();
                this.updateReasonSelects();
            } else {
                showToast(result.error || 'Fehler beim Laden der Gründe', 'error');
            }
        } catch (error) {
            console.error('Error loading reasons:', error);
            showToast('Fehler beim Laden der Gründe', 'error');
        }
    }

    renderReasonList() {
        const container = document.getElementById('reason-list');
        if (!container) return;

        const reasons = stateManager.getBlockReasons();

        if (reasons.length === 0) {
            container.innerHTML = '<p class="text-muted">Keine Gründe gefunden.</p>';
            return;
        }

        const html = reasons.map(reason => `
            <div class="card mb-3">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-start">
                        <div>
                            <h6 class="card-title">
                                <span class="badge me-2" style="background-color: ${reason.color}">&nbsp;</span>
                                ${reason.name}
                                ${!reason.is_active ? '<span class="badge bg-secondary ms-2">Inaktiv</span>' : ''}
                            </h6>
                            ${reason.description ? `<p class="card-text">${reason.description}</p>` : ''}
                            <small class="text-muted">
                                Verwendet in ${reason.usage_count || 0} Sperrungen
                            </small>
                        </div>
                        <div class="btn-group btn-group-sm">
                            <button class="btn btn-outline-primary" onclick="editReason(${reason.id})">
                                Bearbeiten
                            </button>
                            <button class="btn btn-outline-danger" onclick="deleteReason(${reason.id})" 
                                    ${reason.usage_count > 0 ? 'disabled title="Grund wird verwendet"' : ''}>
                                Löschen
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `).join('');

        container.innerHTML = html;
    }

    updateReasonSelects() {
        const reasons = stateManager.getBlockReasons().filter(r => r.is_active);
        const selects = document.querySelectorAll('select[name*="reason"], select[id*="reason"]');

        console.log('Updating reason selects:', reasons.length, 'reasons found,', selects.length, 'selects found'); // Debug log

        // Filter reasons based on user role
        const availableReasons = reasons.filter(reason => {
            // Admins see all active reasons
            if (window.currentUserIsAdmin) {
                return true;
            }
            // Teamsters only see teamster-usable reasons
            if (window.currentUserIsTeamster) {
                return reason.teamster_usable === true;
            }
            return false;
        });

        console.log('Filtered reasons for user role:', availableReasons.length, 'available'); // Debug log

        selects.forEach(select => {
            const currentValue = select.value;

            // Clear existing options except the first one (usually "Grund auswählen")
            const firstOption = select.querySelector('option:first-child');
            select.innerHTML = '';
            if (firstOption) {
                select.appendChild(firstOption);
            }

            // Add filtered reason options
            availableReasons.forEach(reason => {
                const option = document.createElement('option');
                option.value = reason.id;
                option.textContent = reason.name;
                select.appendChild(option);
            });

            // Restore previous value if it still exists in filtered list
            if (currentValue && availableReasons.some(r => r.id == currentValue)) {
                select.value = currentValue;
            }
        });
    }

    async editReason(reasonId, reasonData) {
        try {
            const result = await blockReasonsAPI.update(reasonId, reasonData);
            
            if (result.success) {
                showToast('Grund erfolgreich aktualisiert', 'success');
                await this.loadReasons();
            } else {
                showToast(result.error || 'Fehler beim Aktualisieren des Grundes', 'error');
            }
        } catch (error) {
            console.error('Error updating reason:', error);
            showToast('Fehler beim Aktualisieren des Grundes', 'error');
        }
    }

    async deleteReason(reasonId) {
        if (!confirm('Sind Sie sicher, dass Sie diesen Grund löschen möchten?')) {
            return;
        }

        try {
            const result = await blockReasonsAPI.delete(reasonId);
            
            if (result.success) {
                showToast('Grund erfolgreich gelöscht', 'success');
                await this.loadReasons();
            } else {
                showToast(result.error || 'Fehler beim Löschen des Grundes', 'error');
            }
        } catch (error) {
            console.error('Error deleting reason:', error);
            showToast('Fehler beim Löschen des Grundes', 'error');
        }
    }
}

// Reason edit modal
export class ReasonEditModal {
    constructor() {
        this.currentReason = null;
    }

    show(reason) {
        this.currentReason = reason;
        
        // Create modal HTML if it doesn't exist
        this.createModal();
        
        // Populate form with reason data
        this.populateForm();
        
        // Show modal
        const modal = document.getElementById('edit-reason-modal');
        if (modal && window.bootstrap) {
            const bsModal = new window.bootstrap.Modal(modal);
            bsModal.show();
        }
    }

    createModal() {
        const existingModal = document.getElementById('edit-reason-modal');
        if (existingModal) return;

        const modalHtml = `
            <div class="modal fade" id="edit-reason-modal" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Grund bearbeiten</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <form id="edit-reason-form">
                                <div class="mb-3">
                                    <label for="edit-reason-name" class="form-label">Name *</label>
                                    <input type="text" class="form-control" id="edit-reason-name" name="name" required>
                                </div>
                                <div class="mb-3">
                                    <label for="edit-reason-description" class="form-label">Beschreibung</label>
                                    <textarea class="form-control" id="edit-reason-description" name="description" rows="3"></textarea>
                                </div>
                                <div class="mb-3">
                                    <label for="edit-reason-color" class="form-label">Farbe</label>
                                    <input type="color" class="form-control form-control-color" id="edit-reason-color" name="color" value="#007bff">
                                </div>
                                <div class="mb-3 form-check">
                                    <input type="checkbox" class="form-check-input" id="edit-reason-active" name="is_active" checked>
                                    <label class="form-check-label" for="edit-reason-active">
                                        Aktiv
                                    </label>
                                </div>
                            </form>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Abbrechen</button>
                            <button type="button" class="btn btn-primary" onclick="reasonEditModal.handleSave()">Speichern</button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHtml);
    }

    populateForm() {
        if (!this.currentReason) return;

        const nameInput = document.getElementById('edit-reason-name');
        const descriptionInput = document.getElementById('edit-reason-description');
        const colorInput = document.getElementById('edit-reason-color');
        const activeCheckbox = document.getElementById('edit-reason-active');
        
        if (nameInput) nameInput.value = this.currentReason.name;
        if (descriptionInput) descriptionInput.value = this.currentReason.description || '';
        if (colorInput) colorInput.value = this.currentReason.color || '#007bff';
        if (activeCheckbox) activeCheckbox.checked = this.currentReason.is_active;
    }

    async handleSave() {
        const form = document.getElementById('edit-reason-form');
        if (!form || !this.currentReason) return;

        const formData = formUtils.getFormData(form);
        
        const reasonData = {
            name: formData.name,
            description: formData.description || '',
            color: formData.color || '#007bff',
            is_active: formData.is_active !== undefined
        };

        try {
            const result = await blockReasonsAPI.update(this.currentReason.id, reasonData);
            
            if (result.success) {
                showToast('Grund erfolgreich aktualisiert', 'success');
                
                // Close modal
                const modal = document.getElementById('edit-reason-modal');
                if (modal && window.bootstrap) {
                    const bsModal = window.bootstrap.Modal.getInstance(modal);
                    if (bsModal) bsModal.hide();
                }
                
                // Reload reasons
                if (window.reasonForm) {
                    await window.reasonForm.loadReasons();
                }
            } else {
                showToast(result.error || 'Fehler beim Aktualisieren des Grundes', 'error');
            }
        } catch (error) {
            console.error('Error updating reason:', error);
            showToast('Fehler beim Aktualisieren des Grundes', 'error');
        }
    }
}

// Export instances
export const reasonForm = new ReasonForm();
export const reasonEditModal = new ReasonEditModal();