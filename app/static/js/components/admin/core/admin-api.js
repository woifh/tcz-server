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

// Series API removed - feature discontinued
