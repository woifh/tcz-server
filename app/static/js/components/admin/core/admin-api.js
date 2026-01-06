/**
 * Admin Panel API Functions
 * All API calls for admin panel functionality
 */

// Block Reasons API
export const blockReasonsAPI = {
    async load() {
        try {
            const response = await fetch('/admin/block-reasons');
            const data = await response.json();
            
            if (response.ok) {
                return { success: true, reasons: data.reasons };
            } else {
                return { success: false, error: data.error || 'Fehler beim Laden der Gründe' };
            }
        } catch (error) {
            return { success: false, error: 'Fehler beim Laden der Gründe' };
        }
    },

    async create(reasonData) {
        try {
            const response = await fetch('/admin/block-reasons', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(reasonData)
            });
            
            const data = await response.json();
            return { success: response.ok, data, error: response.ok ? null : data.error };
        } catch (error) {
            return { success: false, error: 'Fehler beim Erstellen des Grundes' };
        }
    },

    async update(reasonId, reasonData) {
        try {
            const response = await fetch(`/admin/block-reasons/${reasonId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(reasonData)
            });
            
            const data = await response.json();
            return { success: response.ok, data, error: response.ok ? null : data.error };
        } catch (error) {
            return { success: false, error: 'Fehler beim Aktualisieren des Grundes' };
        }
    },

    async delete(reasonId) {
        try {
            const response = await fetch(`/admin/block-reasons/${reasonId}`, {
                method: 'DELETE'
            });
            
            const data = await response.json();
            return { success: response.ok, data, error: response.ok ? null : data.error };
        } catch (error) {
            return { success: false, error: 'Fehler beim Löschen des Grundes' };
        }
    },

    async loadDetailsTemplates(reasonId) {
        try {
            const response = await fetch(`/admin/block-reasons/${reasonId}/details-templates`);
            const data = await response.json();
            
            if (response.ok) {
                return { success: true, templates: data.templates };
            } else {
                return { success: false, error: data.error || 'Fehler beim Laden der Details-Vorlagen' };
            }
        } catch (error) {
            return { success: false, error: 'Fehler beim Laden der Details-Vorlagen' };
        }
    },

    async createDetailsTemplate(reasonId, templateData) {
        try {
            const response = await fetch(`/admin/block-reasons/${reasonId}/details-templates`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(templateData)
            });
            
            const data = await response.json();
            return { success: response.ok, data, error: response.ok ? null : data.error };
        } catch (error) {
            return { success: false, error: 'Fehler beim Erstellen der Details-Vorlage' };
        }
    },

    async deleteDetailsTemplate(templateId) {
        try {
            const response = await fetch(`/admin/details-templates/${templateId}`, {
                method: 'DELETE'
            });
            
            const data = await response.json();
            return { success: response.ok, data, error: response.ok ? null : data.error };
        } catch (error) {
            return { success: false, error: 'Fehler beim Löschen der Details-Vorlage' };
        }
    }
};

// Blocks API
export const blocksAPI = {
    async load(params = {}) {
        try {
            const queryParams = new URLSearchParams(params);
            const response = await fetch(`/admin/blocks?${queryParams.toString()}`);
            const data = await response.json();
            
            if (response.ok) {
                return { success: true, blocks: data.blocks };
            } else {
                return { success: false, error: data.error || 'Fehler beim Laden der Sperrungen' };
            }
        } catch (error) {
            return { success: false, error: 'Fehler beim Laden der Sperrungen' };
        }
    },

    async loadSingle(blockId) {
        try {
            const response = await fetch(`/admin/blocks/${blockId}`);
            const data = await response.json();
            
            if (response.ok) {
                return { success: true, block: data.block };
            } else {
                return { success: false, error: data.error || 'Fehler beim Laden der Sperrung' };
            }
        } catch (error) {
            return { success: false, error: 'Fehler beim Laden der Sperrung' };
        }
    },

    async createMultiCourt(blockData) {
        try {
            const response = await fetch('/admin/blocks/multi-court', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(blockData)
            });
            
            const data = await response.json();
            return { success: response.ok, data, error: response.ok ? null : data.error };
        } catch (error) {
            return { success: false, error: 'Fehler beim Erstellen der Sperrung' };
        }
    },

    async updateMultiCourt(blockId, blockData) {
        try {
            const response = await fetch(`/admin/blocks/multi-court-update/${blockId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(blockData)
            });
            
            const data = await response.json();
            return { success: response.ok, data, error: response.ok ? null : data.error };
        } catch (error) {
            return { success: false, error: 'Fehler beim Aktualisieren der Sperrung' };
        }
    },

    async updateBatch(batchId, blockData) {
        try {
            const response = await fetch(`/admin/blocks/batch/${batchId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(blockData)
            });
            
            const data = await response.json();
            return { success: response.ok, data, error: response.ok ? null : data.error };
        } catch (error) {
            return { success: false, error: 'Fehler beim Aktualisieren der Sperrung' };
        }
    },

    async deleteBatch(batchId) {
        try {
            const response = await fetch(`/admin/blocks/batch/${batchId}`, {
                method: 'DELETE'
            });
            
            const data = await response.json();
            return { success: response.ok, data, error: response.ok ? null : data.error };
        } catch (error) {
            return { success: false, error: 'Fehler beim Löschen der Sperrung' };
        }
    },

    async deleteMultiCourt(blockId) {
        try {
            const response = await fetch(`/admin/blocks/multi-court-delete/${blockId}`, {
                method: 'DELETE'
            });
            
            const data = await response.json();
            return { success: response.ok, data, error: response.ok ? null : data.error };
        } catch (error) {
            return { success: false, error: 'Fehler beim Löschen der Sperrung' };
        }
    },

    async bulkDelete(blockIds) {
        try {
            const response = await fetch('/admin/blocks/bulk-delete', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ block_ids: blockIds })
            });
            
            const data = await response.json();
            return { success: response.ok, data, error: response.ok ? null : data.error };
        } catch (error) {
            return { success: false, error: 'Fehler beim Löschen der Sperrungen' };
        }
    },

    async bulkEdit(blockIds, editData) {
        try {
            const response = await fetch('/admin/blocks/bulk-edit', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ block_ids: blockIds, ...editData })
            });
            
            const data = await response.json();
            return { success: response.ok, data, error: response.ok ? null : data.error };
        } catch (error) {
            return { success: false, error: 'Fehler beim Bearbeiten der Sperrungen' };
        }
    },

    async getConflictPreview(blockData) {
        try {
            const response = await fetch('/admin/blocks/conflict-preview', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(blockData)
            });
            
            const data = await response.json();
            return { success: response.ok, data, error: response.ok ? null : data.error };
        } catch (error) {
            return { success: false, error: 'Fehler beim Laden der Konflikt-Vorschau' };
        }
    },

    async loadAuditLog() {
        try {
            const response = await fetch('/admin/blocks/audit-log');
            const data = await response.json();
            
            if (response.ok) {
                return { success: true, logs: data.logs };
            } else {
                return { success: false, error: data.error || 'Fehler beim Laden des Audit-Logs' };
            }
        } catch (error) {
            return { success: false, error: 'Fehler beim Laden des Audit-Logs' };
        }
    }
};

// Series API
export const seriesAPI = {
    async create(seriesData) {
        try {
            const response = await fetch('/admin/blocks/series', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(seriesData)
            });
            
            const data = await response.json();
            return { success: response.ok, data, error: response.ok ? null : data.error };
        } catch (error) {
            return { success: false, error: 'Fehler beim Erstellen der Serie' };
        }
    },

    async load() {
        try {
            const response = await fetch('/admin/blocks/series');
            const data = await response.json();
            
            if (response.ok) {
                return { success: true, series: data.series };
            } else {
                return { success: false, error: data.error || 'Fehler beim Laden der Serien' };
            }
        } catch (error) {
            return { success: false, error: 'Fehler beim Laden der Serien' };
        }
    },

    async update(seriesId, updateData) {
        try {
            const url = updateData.edit_type === 'single' 
                ? `/admin/blocks/series/${seriesId}/instance`
                : `/admin/blocks/series/${seriesId}`;
                
            const response = await fetch(url, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(updateData)
            });
            
            const data = await response.json();
            return { success: response.ok, data, error: response.ok ? null : data.error };
        } catch (error) {
            return { success: false, error: 'Fehler beim Aktualisieren der Serie' };
        }
    },

    async delete(seriesId, deleteData) {
        try {
            const response = await fetch(`/admin/blocks/series/${seriesId}`, {
                method: 'DELETE',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(deleteData)
            });
            
            const data = await response.json();
            return { success: response.ok, data, error: response.ok ? null : data.error };
        } catch (error) {
            return { success: false, error: 'Fehler beim Löschen der Serie' };
        }
    }
};