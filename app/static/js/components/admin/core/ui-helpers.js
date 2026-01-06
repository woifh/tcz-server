/**
 * UI Helper Functions
 * Handles tab management, modals, and other UI utilities
 */

/**
 * Tab management
 */
export function showTab(tabName) {
    // Hide all tab contents
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.add('hidden');
    });

    // Remove active styling from all tabs
    document.querySelectorAll('.tab-button').forEach(button => {
        button.classList.remove('border-green-600', 'text-green-600');
        button.classList.add('border-transparent', 'text-gray-500');
    });

    // Show selected tab content
    const tabContent = document.getElementById('content-' + tabName);
    if (tabContent) {
        tabContent.classList.remove('hidden');
    }

    // Add active styling to selected tab
    const activeTab = document.getElementById('tab-' + tabName);
    if (activeTab) {
        activeTab.classList.remove('border-transparent', 'text-gray-500');
        activeTab.classList.add('border-green-600', 'text-green-600');
    }

    // Load content for specific tabs
    if (tabName === 'calendar' && window.calendarView) {
        window.calendarView.renderCalendarView();
    } else if (tabName === 'reasons' && window.reasonForm) {
        window.reasonForm.loadReasonList();
    }
}

/**
 * Modal utilities
 */
export const modalUtils = {
    /**
     * Create a generic modal
     */
    createModal(id, title, content, buttons = []) {
        const modal = document.createElement('div');
        modal.id = id;
        modal.className = 'fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50';

        const buttonHtml = buttons.map(btn => `
            <button
                onclick="${btn.onclick}"
                class="${btn.className || 'bg-gray-600 text-white py-2 px-4 rounded hover:bg-gray-700'}">
                ${btn.label}
            </button>
        `).join('');

        modal.innerHTML = `
            <div class="bg-white rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto">
                <div class="flex items-center justify-between mb-4">
                    <h3 class="text-lg font-semibold">${title}</h3>
                    <button onclick="document.getElementById('${id}').remove()" class="text-gray-500 hover:text-gray-700">
                        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                        </svg>
                    </button>
                </div>
                <div class="modal-content">
                    ${content}
                </div>
                ${buttons.length > 0 ? `
                    <div class="flex gap-2 mt-6">
                        ${buttonHtml}
                    </div>
                ` : ''}
            </div>
        `;

        return modal;
    },

    /**
     * Show a modal
     */
    showModal(modal) {
        document.body.appendChild(modal);
    },

    /**
     * Close a modal by ID
     */
    closeModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.remove();
        }
    },

    /**
     * Show a confirmation dialog
     */
    showConfirmation(title, message, onConfirm, onCancel = null) {
        const modalId = 'confirmation-modal-' + Date.now();

        const modal = this.createModal(
            modalId,
            title,
            `<p class="text-gray-700">${message}</p>`,
            [
                {
                    label: 'Bestätigen',
                    className: 'bg-green-600 text-white py-2 px-4 rounded hover:bg-green-700',
                    onclick: `window.modalUtils.closeModal('${modalId}'); (${onConfirm.toString()})()`
                },
                {
                    label: 'Abbrechen',
                    className: 'bg-gray-600 text-white py-2 px-4 rounded hover:bg-gray-700',
                    onclick: `window.modalUtils.closeModal('${modalId}'); ${onCancel ? `(${onCancel.toString()})()` : ''}`
                }
            ]
        );

        this.showModal(modal);
    }
};

/**
 * Color utilities for block reasons
 */
export function getReasonColor(reasonName) {
    const colorMap = {
        'Wartung': '#f59e0b',      // amber
        'Maintenance': '#f59e0b',   // amber
        'Regen': '#6b7280',        // gray
        'Weather': '#6b7280',      // gray
        'Turnier': '#10b981',      // emerald
        'Tournament': '#10b981',   // emerald
        'Meisterschaft': '#8b5cf6', // violet
        'Championship': '#8b5cf6', // violet
        'Tenniskurs': '#3b82f6',   // blue
        'Tennis Course': '#3b82f6', // blue
        'Platzreparatur': '#f97316', // orange
        'Court Repair': '#f97316'   // orange
    };

    return colorMap[reasonName] || '#6b7280'; // default gray
}

/**
 * Loading state utilities
 */
export const loadingUtils = {
    /**
     * Show loading spinner in a container
     */
    showLoading(containerId, message = 'Lädt...') {
        const container = document.getElementById(containerId);
        if (!container) return;

        container.innerHTML = `
            <div class="text-center py-4">
                <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-green-600"></div>
                <p class="mt-2 text-gray-600">${message}</p>
            </div>
        `;
    },

    /**
     * Show error message in a container
     */
    showError(containerId, message) {
        const container = document.getElementById(containerId);
        if (!container) return;

        container.innerHTML = `
            <div class="text-center py-4">
                <p class="text-red-600">${message}</p>
            </div>
        `;
    },

    /**
     * Show empty state in a container
     */
    showEmpty(containerId, message = 'Keine Daten gefunden') {
        const container = document.getElementById(containerId);
        if (!container) return;

        container.innerHTML = `
            <div class="text-center py-4">
                <p class="text-gray-600">${message}</p>
            </div>
        `;
    }
};

/**
 * Keyboard shortcuts helper
 */
export class KeyboardShortcuts {
    constructor() {
        this.shortcuts = new Map();
        this.setupListener();
    }

    setupListener() {
        document.addEventListener('keydown', (e) => {
            const key = this.getKeyCombo(e);
            const handler = this.shortcuts.get(key);

            if (handler) {
                e.preventDefault();
                handler(e);
            }
        });
    }

    getKeyCombo(event) {
        const parts = [];
        if (event.ctrlKey) parts.push('ctrl');
        if (event.altKey) parts.push('alt');
        if (event.shiftKey) parts.push('shift');
        if (event.metaKey) parts.push('meta');
        parts.push(event.key.toLowerCase());
        return parts.join('+');
    }

    register(keyCombo, handler) {
        this.shortcuts.set(keyCombo.toLowerCase(), handler);
    }

    unregister(keyCombo) {
        this.shortcuts.delete(keyCombo.toLowerCase());
    }
}

// Export singleton instances
export const keyboardShortcuts = new KeyboardShortcuts();

// Make modalUtils globally available
if (typeof window !== 'undefined') {
    window.modalUtils = modalUtils;
}
