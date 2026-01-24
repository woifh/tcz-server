/**
 * Admin Panel API Functions
 * All API calls for admin panel functionality
 */

/**
 * Get CSRF token from meta tag
 */
function getCsrfToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute('content') : null;
}

/**
 * Get headers for state-changing requests
 */
function getHeaders() {
    return {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCsrfToken(),
    };
}

// Block Reasons API
export const blockReasonsAPI = {
    async load() {
        try {
            const response = await fetch('/api/admin/block-reasons');
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
            const response = await fetch('/api/admin/block-reasons', {
                method: 'POST',
                headers: getHeaders(),
                body: JSON.stringify(reasonData),
            });

            const data = await response.json();
            return { success: response.ok, data, error: response.ok ? null : data.error };
        } catch (error) {
            return { success: false, error: 'Fehler beim Erstellen des Grundes' };
        }
    },

    async update(reasonId, reasonData) {
        try {
            const response = await fetch(`/api/admin/block-reasons/${reasonId}`, {
                method: 'PUT',
                headers: getHeaders(),
                body: JSON.stringify(reasonData),
            });

            const data = await response.json();
            return { success: response.ok, data, error: response.ok ? null : data.error };
        } catch (error) {
            return { success: false, error: 'Fehler beim Aktualisieren des Grundes' };
        }
    },

    async delete(reasonId) {
        try {
            const response = await fetch(`/api/admin/block-reasons/${reasonId}`, {
                method: 'DELETE',
                headers: { 'X-CSRFToken': getCsrfToken() },
            });

            const data = await response.json();
            return { success: response.ok, data, error: response.ok ? null : data.error };
        } catch (error) {
            return { success: false, error: 'Fehler beim Löschen des Grundes' };
        }
    },
};

// Blocks API
export const blocksAPI = {
    async load(params = {}) {
        try {
            const queryParams = new URLSearchParams(params);
            const response = await fetch(`/api/admin/blocks?${queryParams.toString()}`);
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

    async create(blockData) {
        try {
            const response = await fetch('/api/admin/blocks', {
                method: 'POST',
                headers: getHeaders(),
                body: JSON.stringify(blockData),
            });

            const data = await response.json();
            return { success: response.ok, data, error: response.ok ? null : data.error };
        } catch (error) {
            return { success: false, error: 'Fehler beim Erstellen der Sperrung' };
        }
    },

    async update(batchId, blockData) {
        try {
            const response = await fetch(`/api/admin/blocks/${batchId}`, {
                method: 'PUT',
                headers: getHeaders(),
                body: JSON.stringify(blockData),
            });

            const data = await response.json();
            return { success: response.ok, data, error: response.ok ? null : data.error };
        } catch (error) {
            return { success: false, error: 'Fehler beim Aktualisieren der Sperrung' };
        }
    },

    async delete(batchId) {
        try {
            const response = await fetch(`/api/admin/blocks/${batchId}`, {
                method: 'DELETE',
                headers: { 'X-CSRFToken': getCsrfToken() },
            });

            const data = await response.json();
            return { success: response.ok, data, error: response.ok ? null : data.error };
        } catch (error) {
            return { success: false, error: 'Fehler beim Löschen der Sperrung' };
        }
    },

    async get(batchId) {
        try {
            const response = await fetch(`/api/admin/blocks/${batchId}`);
            const data = await response.json();

            if (response.ok) {
                return { success: true, batch: data };
            } else {
                return { success: false, error: data.error || 'Fehler beim Laden der Sperrung' };
            }
        } catch (error) {
            return { success: false, error: 'Fehler beim Laden der Sperrung' };
        }
    },

    async getConflictPreview(blockData) {
        try {
            const response = await fetch('/api/admin/blocks/conflict-preview', {
                method: 'POST',
                headers: getHeaders(),
                body: JSON.stringify(blockData),
            });

            const data = await response.json();
            return { success: response.ok, data, error: response.ok ? null : data.error };
        } catch (error) {
            return { success: false, error: 'Fehler beim Laden der Konflikt-Vorschau' };
        }
    },

    async loadAuditLog() {
        try {
            const response = await fetch('/api/admin/blocks/audit-log');
            const data = await response.json();

            if (response.ok) {
                return { success: true, logs: data.logs };
            } else {
                return { success: false, error: data.error || 'Fehler beim Laden des Audit-Logs' };
            }
        } catch (error) {
            return { success: false, error: 'Fehler beim Laden des Audit-Logs' };
        }
    },
};

// Series API removed - feature discontinued
