/**
 * Enhanced Admin Panel JavaScript
 * Handles all advanced block management functionality
 */

// German text constants for enhanced admin features
const GERMAN_TEXT = {
    // Reason management
    MANAGE_BLOCK_REASON: 'Sperrungsgrund verwalten',
    DETAILS: 'Details',
    REASON_IN_USE: 'Grund wird verwendet',
    HISTORICAL_DATA_PRESERVED: 'Historische Daten bleiben erhalten',
    
    // Calendar and filtering
    CALENDAR_VIEW: 'Kalenderansicht',
    MONTHLY_VIEW: 'Monatliche Ansicht',
    CONFLICT_PREVIEW: 'Konflikt-Vorschau',
    AFFECTED_RESERVATIONS: 'Betroffene Buchungen'
};

let blockReasons = [];
let currentCalendarDate = new Date();
let calendarBlocks = [];
let currentFilters = {};
let filterUpdateTimeout = null;

// Initialize admin panel
function initializeAdminPanel() {
    loadBlockReasons();
    setupEventListeners();
    
    // Set default dates
    const today = new Date().toISOString().split('T')[0];
    const nextWeek = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
    
    // Set default date for multi-court form
    const multiDateInput = document.getElementById('multi-date');
    if (multiDateInput) {
        multiDateInput.value = today;
    }
    
    // Ensure end time field is enabled
    const endTimeInput = document.getElementById('multi-end');
    if (endTimeInput) {
        endTimeInput.disabled = false;
    }
    
    // Initialize calendar view
    initializeCalendarView();
    
    // Load upcoming blocks automatically
    loadUpcomingBlocks();
    
    // Handle edit mode if edit block data is available
    if (window.editBlockData) {
        populateEditForm(window.editBlockData);
    }
}

// Initialize calendar view
function initializeCalendarView() {
    currentCalendarDate = new Date();
    renderCalendarView();
}

// Setup event listeners
function setupEventListeners() {
    // Multi-court form (now the only form)
    const multiCourtForm = document.getElementById('multi-court-form');
    if (multiCourtForm) {
        multiCourtForm.addEventListener('submit', handleMultiCourtSubmit);
    }
    
    // Reason form
    const reasonForm = document.getElementById('reason-form');
    if (reasonForm) {
        reasonForm.addEventListener('submit', handleReasonSubmit);
    }
    
    // Court selection buttons
    const selectAllBtn = document.getElementById('select-all-courts');
    const clearAllBtn = document.getElementById('clear-all-courts');
    
    if (selectAllBtn) {
        selectAllBtn.addEventListener('click', () => {
            document.querySelectorAll('input[name="multi-courts"]').forEach(cb => cb.checked = true);
            validateForm();
        });
    }
    
    if (clearAllBtn) {
        clearAllBtn.addEventListener('click', () => {
            document.querySelectorAll('input[name="multi-courts"]').forEach(cb => cb.checked = false);
            validateForm();
        });
    }
    
    // Form validation
    setupFormValidation();
}

// Setup form validation
function setupFormValidation() {
    const courtCheckboxes = document.querySelectorAll('input[name="multi-courts"]');
    const startTimeInput = document.getElementById('multi-start');
    const endTimeInput = document.getElementById('multi-end');
    const reasonSelect = document.getElementById('multi-reason');
    const dateInput = document.getElementById('multi-date');
    const submitBtn = document.getElementById('create-block-btn');
    
    // Court selection validation
    courtCheckboxes.forEach(cb => {
        cb.addEventListener('change', validateForm);
    });
    
    // Time validation
    if (startTimeInput && endTimeInput) {
        startTimeInput.addEventListener('change', () => {
            validateTimeRange();
            validateForm();
        });
        
        endTimeInput.addEventListener('change', () => {
            validateTimeRange();
            validateForm();
        });
    }
    
    // Other field validation
    if (reasonSelect) {
        reasonSelect.addEventListener('change', validateForm);
    }
    
    if (dateInput) {
        dateInput.addEventListener('change', validateForm);
    }
    
    // Initial validation
    validateForm();
}

// Validate time range
function validateTimeRange() {
    const startTimeInput = document.getElementById('multi-start');
    const endTimeInput = document.getElementById('multi-end');
    const timeError = document.getElementById('time-error');
    
    if (startTimeInput && endTimeInput && startTimeInput.value && endTimeInput.value) {
        const isValid = endTimeInput.value > startTimeInput.value;
        
        if (timeError) {
            if (isValid) {
                timeError.classList.add('hidden');
                endTimeInput.classList.remove('border-red-300');
                endTimeInput.classList.add('border-gray-300');
            } else {
                timeError.classList.remove('hidden');
                endTimeInput.classList.add('border-red-300');
                endTimeInput.classList.remove('border-gray-300');
            }
        }
        
        return isValid;
    }
    return true;
}

// Validate entire form
function validateForm() {
    const courtCheckboxes = document.querySelectorAll('input[name="multi-courts"]');
    const dateInput = document.getElementById('multi-date');
    const startTimeInput = document.getElementById('multi-start');
    const endTimeInput = document.getElementById('multi-end');
    const reasonSelect = document.getElementById('multi-reason');
    const submitBtn = document.getElementById('create-block-btn');
    const courtHint = document.getElementById('court-selection-hint');
    
    const hasSelectedCourts = Array.from(courtCheckboxes).some(cb => cb.checked);
    const hasDate = dateInput && dateInput.value;
    const hasStartTime = startTimeInput && startTimeInput.value;
    const hasEndTime = endTimeInput && endTimeInput.value;
    const hasReason = reasonSelect && reasonSelect.value;
    const timeRangeValid = validateTimeRange();
    
    // Show/hide court selection hint
    if (courtHint) {
        if (hasSelectedCourts) {
            courtHint.classList.add('hidden');
        } else {
            courtHint.classList.remove('hidden');
        }
    }
    
    // Enable/disable submit button
    const isFormValid = hasSelectedCourts && hasDate && hasStartTime && hasEndTime && hasReason && timeRangeValid;
    
    if (submitBtn) {
        submitBtn.disabled = !isFormValid;
    }
    
    return isFormValid;
}

// Tab management
function showTab(tabName) {
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
    document.getElementById('content-' + tabName).classList.remove('hidden');
    
    // Add active styling to selected tab
    const activeTab = document.getElementById('tab-' + tabName);
    activeTab.classList.remove('border-transparent', 'text-gray-500');
    activeTab.classList.add('border-green-600', 'text-green-600');
    
    // Load content for specific tabs
    if (tabName === 'calendar') {
        renderCalendarView();
    } else if (tabName === 'reasons') {
        loadReasonList();
    }
}

// Populate form with edit data
function populateEditForm(blockData) {
    // Wait for reasons to be loaded before populating
    const populateWhenReady = () => {
        if (blockReasons.length === 0) {
            setTimeout(populateWhenReady, 100);
            return;
        }
        
        // Populate form fields
        document.getElementById('multi-date').value = blockData.date;
        document.getElementById('multi-start').value = blockData.start_time;
        document.getElementById('multi-end').value = blockData.end_time;
        document.getElementById('multi-reason').value = blockData.reason_id;
        document.getElementById('multi-details').value = blockData.details;
        
        // Select all courts that are part of this block group
        blockData.court_ids.forEach(courtId => {
            const courtCheckbox = document.querySelector(`input[name="multi-courts"][value="${courtId}"]`);
            if (courtCheckbox) {
                courtCheckbox.checked = true;
            }
        });
        
        // Update the court selection hint to show edit mode info
        const courtHint = document.getElementById('court-selection-hint');
        if (courtHint) {
            if (blockData.court_ids.length === 1) {
                courtHint.innerHTML = '<p class="text-sm text-blue-600">ℹ️ Bearbeitung einer Einzelplatz-Sperrung</p>';
            } else {
                courtHint.innerHTML = `<p class="text-sm text-blue-600">ℹ️ Bearbeitung einer Mehrplatz-Sperrung (${blockData.court_ids.length} Plätze)</p>`;
            }
            courtHint.classList.remove('hidden');
        }
        
        // Validate form to enable submit button
        validateForm();
    };
    
    populateWhenReady();
}

// Load block reasons
async function loadBlockReasons() {
    try {
        const response = await fetch('/admin/block-reasons');
        const data = await response.json();
        
        if (response.ok) {
            blockReasons = data.reasons;
            populateReasonSelects();
        } else {
            showToast(data.error || 'Fehler beim Laden der Sperrungsgründe', 'error');
        }
    } catch (error) {
        showToast('Fehler beim Laden der Sperrungsgründe', 'error');
    }
}

// Populate reason select elements
function populateReasonSelects() {
    const selects = ['block-reason', 'multi-reason', 'filter-reasons'];
    
    selects.forEach(selectId => {
        const select = document.getElementById(selectId);
        if (select) {
            select.innerHTML = '';
            blockReasons.forEach(reason => {
                const option = document.createElement('option');
                option.value = reason.id;
                option.textContent = reason.name;
                select.appendChild(option);
            });
        }
    });
}

// Handle multi-court form submission
async function handleMultiCourtSubmit(e) {
    e.preventDefault();
    
    const submitBtn = document.getElementById('create-block-btn');
    const originalText = submitBtn.textContent;
    const form = document.getElementById('multi-court-form');
    const isEditMode = form.dataset.editMode === 'true';
    const blockId = form.dataset.blockId;
    const relatedBlockIds = form.dataset.relatedBlockIds ? form.dataset.relatedBlockIds.split(',').map(id => parseInt(id)) : [];
    
    // Show loading state
    submitBtn.disabled = true;
    submitBtn.textContent = isEditMode ? 'Wird aktualisiert...' : 'Wird erstellt...';
    
    const selectedCourts = Array.from(document.querySelectorAll('input[name="multi-courts"]:checked'))
        .map(cb => parseInt(cb.value));
    
    if (selectedCourts.length === 0) {
        showToast('Bitte mindestens einen Platz auswählen', 'error');
        submitBtn.disabled = false;
        submitBtn.textContent = originalText;
        return;
    }
    
    const blockData = {
        date: document.getElementById('multi-date').value,
        start_time: document.getElementById('multi-start').value,
        end_time: document.getElementById('multi-end').value,
        reason_id: parseInt(document.getElementById('multi-reason').value),
        details: document.getElementById('multi-details').value
    };
    
    // For create mode, add court_ids
    if (!isEditMode) {
        blockData.court_ids = selectedCourts;
    } else {
        // For edit mode, add the related block IDs and new court selection
        blockData.court_ids = selectedCourts;
        blockData.related_block_ids = relatedBlockIds;
    }
    
    try {
        let response;
        
        if (isEditMode) {
            // Update existing block group
            response = await fetch(`/admin/blocks/batch/${blockId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(blockData)
            });
        } else {
            // Create new block
            response = await fetch('/admin/blocks/multi-court', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(blockData)
            });
        }
        
        const data = await response.json();
        
        if (response.ok) {
            showToast(isEditMode ? 'Sperrung erfolgreich aktualisiert!' : 'Sperrung erfolgreich erstellt!', 'success');
            
            if (isEditMode) {
                // Redirect back to main court blocking page after successful edit
                setTimeout(() => {
                    window.location.href = '/admin/court-blocking';
                }, 1500);
            } else {
                // Reset form but keep some values for convenience
                const courtCheckboxes = document.querySelectorAll('input[name="multi-courts"]');
                courtCheckboxes.forEach(cb => cb.checked = false);
                document.getElementById('multi-details').value = '';
                
                // Refresh the list if loadUpcomingBlocks function exists
                if (typeof loadUpcomingBlocks === 'function') {
                    loadUpcomingBlocks();
                }
            }
        } else {
            if (data.error && data.error.includes('Konflikt')) {
                showToast('Konflikt erkannt: ' + data.error, 'warning');
            } else {
                showToast(data.error || `Unbekannter Fehler beim ${isEditMode ? 'Aktualisieren' : 'Erstellen'} der Sperrung`, 'error');
            }
        }
    } catch (error) {
        console.error('Error with block operation:', error);
        showToast(`Fehler beim ${isEditMode ? 'Aktualisieren' : 'Erstellen'} der Sperrung`, 'error');
    } finally {
        // Restore button state
        submitBtn.disabled = false;
        submitBtn.textContent = originalText;
        
        // Re-validate form to update button state
        validateForm();
    }
}

// Handle reason form submission
async function handleReasonSubmit(e) {
    e.preventDefault();
    
    const reasonData = {
        name: document.getElementById('reason-name').value
    };
    
    try {
        const response = await fetch('/admin/block-reasons', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(reasonData)
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showToast(data.message);
            e.target.reset();
            loadBlockReasons(); // Refresh reasons
            loadReasonList(); // Refresh the reason list
        } else {
            showToast(data.error || 'Unbekannter Fehler', 'error');
        }
    } catch (error) {
        showToast('Fehler beim Erstellen des Sperrungsgrundes', 'error');
    }
}

// Preview conflicts
async function previewConflicts() {
    const conflictData = {
        court_ids: [parseInt(document.getElementById('block-court').value)],
        date: document.getElementById('block-date').value,
        start_time: document.getElementById('block-start').value,
        end_time: document.getElementById('block-end').value
    };
    
    try {
        const response = await fetch('/admin/blocks/conflict-preview', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(conflictData)
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showConflictModal(data.conflicts);
        } else {
            showToast(data.error || 'Fehler bei der Konfliktprüfung', 'error');
        }
    } catch (error) {
        showToast('Fehler bei der Konfliktprüfung', 'error');
    }
}

// Show conflict modal
function showConflictModal(conflicts) {
    const modal = document.getElementById('conflict-modal');
    const content = document.getElementById('conflict-content');
    
    if (conflicts.length === 0) {
        content.innerHTML = '<p class="text-green-600">Keine Konflikte gefunden. Die Sperrung kann erstellt werden.</p>';
    } else {
        let html = `<p class="text-red-600 mb-4">Warnung: ${conflicts.length} ${GERMAN_TEXT.AFFECTED_RESERVATIONS} würden storniert werden:</p>`;
        html += '<div class="space-y-2">';
        
        conflicts.forEach(conflict => {
            html += `
                <div class="border border-red-200 rounded p-3 bg-red-50">
                    <p><strong>Platz ${conflict.court_number}</strong> - ${conflict.date} ${conflict.start_time}-${conflict.end_time}</p>
                    <p>Gebucht für: ${conflict.booked_for} von ${conflict.booked_by}</p>
                </div>
            `;
        });
        
        html += '</div>';
        content.innerHTML = html;
    }
    
    modal.classList.remove('hidden');
}

// Close conflict modal
function closeConflictModal() {
    document.getElementById('conflict-modal').classList.add('hidden');
}

// Apply filters to block list
async function applyFilters() {
    const filters = {
        date_range_start: document.getElementById('filter-date-start').value,
        date_range_end: document.getElementById('filter-date-end').value,
        court_ids: Array.from(document.getElementById('filter-courts').selectedOptions).map(o => o.value),
        reason_ids: Array.from(document.getElementById('filter-reasons').selectedOptions).map(o => o.value)
    };
    
    // Store current filters
    currentFilters = filters;
    saveFiltersToStorage();
    
    // Build query string
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
        if (Array.isArray(value)) {
            value.forEach(v => {
                if (v) params.append(key, v);
            });
        } else if (value) {
            params.append(key, value);
        }
    });
    
    // Show loading state
    const blocksList = document.getElementById('blocks-list');
    blocksList.innerHTML = '<div class="text-center py-4"><div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-green-600"></div><p class="mt-2 text-gray-600">Lade Sperrungen...</p></div>';
    
    try {
        const response = await fetch(`/admin/blocks?${params.toString()}`);
        const data = await response.json();
        
        if (response.ok) {
            displayBlockList(data.blocks);
            updateFilterSummary(data.blocks.length, filters);
        } else {
            blocksList.innerHTML = `<p class="text-red-600">Fehler: ${data.error || 'Fehler beim Laden der Sperrungen'}</p>`;
        }
    } catch (error) {
        blocksList.innerHTML = '<p class="text-red-600">Fehler beim Laden der Sperrungen</p>';
    }
}

// Update filter summary
function updateFilterSummary(count, filters) {
    const summaryContainer = document.getElementById('filter-summary');
    if (!summaryContainer) return;
    
    let summaryText = `${count} Sperrung(en) gefunden`;
    
    const activeFilters = [];
    if (filters.date_range_start && filters.date_range_end) {
        activeFilters.push(`Zeitraum: ${formatGermanDate(filters.date_range_start)} - ${formatGermanDate(filters.date_range_end)}`);
    }
    if (filters.court_ids.length > 0) {
        activeFilters.push(`Plätze: ${filters.court_ids.join(', ')}`);
    }
    if (filters.reason_ids.length > 0) {
        const reasonNames = filters.reason_ids.map(id => {
            const reason = blockReasons.find(r => r.id == id);
            return reason ? reason.name : id;
        });
        activeFilters.push(`Gründe: ${reasonNames.join(', ')}`);
    }
    
    if (activeFilters.length > 0) {
        summaryText += ` | ${activeFilters.join(' | ')}`;
    }
    
    summaryContainer.innerHTML = `<p class="text-sm text-gray-600 mb-2">${summaryText}</p>`;
}

// Setup dynamic filtering
function setupDynamicFiltering() {
    const filterElements = [
        'filter-date-start',
        'filter-date-end',
        'filter-courts',
        'filter-reasons'
    ];
    
    filterElements.forEach(elementId => {
        const element = document.getElementById(elementId);
        if (element) {
            element.addEventListener('change', debounceFilterUpdate);
        }
    });
    
}

// Debounced filter update
function debounceFilterUpdate() {
    clearTimeout(filterUpdateTimeout);
    filterUpdateTimeout = setTimeout(() => {
        applyFilters();
    }, 500); // 500ms delay
}

// Save filters to localStorage
function saveFiltersToStorage() {
    try {
        localStorage.setItem('adminBlockFilters', JSON.stringify(currentFilters));
    } catch (error) {
        // Ignore localStorage errors
    }
}

// Load saved filters
function loadSavedFilters() {
    try {
        const savedFilters = localStorage.getItem('adminBlockFilters');
        if (savedFilters) {
            const filters = JSON.parse(savedFilters);
            
            // Apply saved filters to form elements
            if (filters.date_range_start) {
                document.getElementById('filter-date-start').value = filters.date_range_start;
            }
            if (filters.date_range_end) {
                document.getElementById('filter-date-end').value = filters.date_range_end;
            }
            if (filters.court_ids) {
                const courtSelect = document.getElementById('filter-courts');
                Array.from(courtSelect.options).forEach(option => {
                    option.selected = filters.court_ids.includes(option.value);
                });
            }
            if (filters.reason_ids) {
                const reasonSelect = document.getElementById('filter-reasons');
                Array.from(reasonSelect.options).forEach(option => {
                    option.selected = filters.reason_ids.includes(option.value);
                });
            }
            
            currentFilters = filters;
        }
    } catch (error) {
        // Ignore localStorage errors
    }
}

// Advanced filter modal
function showAdvancedFilters() {
    let html = `
        <div id="advanced-filter-modal" class="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
            <div class="bg-white rounded-lg p-6 max-w-4xl w-full mx-4 max-h-[80vh] overflow-y-auto">
                <div class="flex items-center justify-between mb-4">
                    <h3 class="text-lg font-semibold">Erweiterte Filter</h3>
                    <button onclick="closeAdvancedFilters()" class="text-gray-500 hover:text-gray-700">
                        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                        </svg>
                    </button>
                </div>
                
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    <!-- Date Range -->
                    <div class="space-y-4">
                        <h4 class="font-semibold">Zeitraum</h4>
                        <div>
                            <label class="block text-sm font-medium mb-1">Von</label>
                            <input type="date" id="adv-filter-date-start" class="w-full border border-gray-300 rounded px-3 py-2">
                        </div>
                        <div>
                            <label class="block text-sm font-medium mb-1">Bis</label>
                            <input type="date" id="adv-filter-date-end" class="w-full border border-gray-300 rounded px-3 py-2">
                        </div>
                        <div class="flex gap-2">
                            <button onclick="setDateRange('today')" class="text-xs bg-gray-200 px-2 py-1 rounded">Heute</button>
                            <button onclick="setDateRange('week')" class="text-xs bg-gray-200 px-2 py-1 rounded">Diese Woche</button>
                            <button onclick="setDateRange('month')" class="text-xs bg-gray-200 px-2 py-1 rounded">Dieser Monat</button>
                        </div>
                    </div>
                    
                    <!-- Courts -->
                    <div class="space-y-4">
                        <h4 class="font-semibold">Plätze</h4>
                        <div class="space-y-2">
                            <label class="flex items-center">
                                <input type="checkbox" name="adv-courts" value="1" class="mr-2"> Platz 1
                            </label>
                            <label class="flex items-center">
                                <input type="checkbox" name="adv-courts" value="2" class="mr-2"> Platz 2
                            </label>
                            <label class="flex items-center">
                                <input type="checkbox" name="adv-courts" value="3" class="mr-2"> Platz 3
                            </label>
                            <label class="flex items-center">
                                <input type="checkbox" name="adv-courts" value="4" class="mr-2"> Platz 4
                            </label>
                            <label class="flex items-center">
                                <input type="checkbox" name="adv-courts" value="5" class="mr-2"> Platz 5
                            </label>
                            <label class="flex items-center">
                                <input type="checkbox" name="adv-courts" value="6" class="mr-2"> Platz 6
                            </label>
                        </div>
                        <div class="flex gap-2">
                            <button onclick="selectAllCourts(true)" class="text-xs bg-gray-200 px-2 py-1 rounded">Alle</button>
                            <button onclick="selectAllCourts(false)" class="text-xs bg-gray-200 px-2 py-1 rounded">Keine</button>
                        </div>
                    </div>
                    
                    <!-- Reasons -->
                    <div class="space-y-4">
                        <h4 class="font-semibold">Gründe</h4>
                        <div>
                            <label class="block text-sm font-medium mb-1">Sperrungsgründe</label>
                            <select id="adv-filter-reasons" multiple class="w-full border border-gray-300 rounded px-3 py-2" size="4">
                                <!-- Will be populated by JavaScript -->
                            </select>
                        </div>
                    </div>
                </div>
                
                <div class="mt-6 flex gap-2">
                    <button onclick="applyAdvancedFilters()" class="bg-green-600 text-white py-2 px-6 rounded hover:bg-green-700">
                        Filter anwenden
                    </button>
                    <button onclick="resetAdvancedFilters()" class="bg-gray-600 text-white py-2 px-6 rounded hover:bg-gray-700">
                        Zurücksetzen
                    </button>
                    <button onclick="closeAdvancedFilters()" class="bg-gray-600 text-white py-2 px-6 rounded hover:bg-gray-700">
                        Schließen
                    </button>
                </div>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', html);
    
    // Populate reasons
    const reasonSelect = document.getElementById('adv-filter-reasons');
    blockReasons.forEach(reason => {
        const option = document.createElement('option');
        option.value = reason.id;
        option.textContent = reason.name;
        reasonSelect.appendChild(option);
    });
    
    // Load current filter values
    loadCurrentFiltersToAdvanced();
}

// Close advanced filters modal
function closeAdvancedFilters() {
    const modal = document.getElementById('advanced-filter-modal');
    if (modal) {
        modal.remove();
    }
}

// Set date range shortcuts
function setDateRange(range) {
    const today = new Date();
    let startDate, endDate;
    
    switch (range) {
        case 'today':
            startDate = endDate = today;
            break;
        case 'week':
            startDate = new Date(today);
            startDate.setDate(today.getDate() - today.getDay() + 1); // Monday
            endDate = new Date(startDate);
            endDate.setDate(startDate.getDate() + 6); // Sunday
            break;
        case 'month':
            startDate = new Date(today.getFullYear(), today.getMonth(), 1);
            endDate = new Date(today.getFullYear(), today.getMonth() + 1, 0);
            break;
    }
    
    document.getElementById('adv-filter-date-start').value = startDate.toISOString().split('T')[0];
    document.getElementById('adv-filter-date-end').value = endDate.toISOString().split('T')[0];
}

// Select all courts
function selectAllCourts(select) {
    document.querySelectorAll('input[name="adv-courts"]').forEach(cb => {
        cb.checked = select;
    });
}

// Load current filters to advanced modal
function loadCurrentFiltersToAdvanced() {
    if (currentFilters.date_range_start) {
        document.getElementById('adv-filter-date-start').value = currentFilters.date_range_start;
    }
    if (currentFilters.date_range_end) {
        document.getElementById('adv-filter-date-end').value = currentFilters.date_range_end;
    }
    if (currentFilters.court_ids) {
        currentFilters.court_ids.forEach(courtId => {
            const checkbox = document.querySelector(`input[name="adv-courts"][value="${courtId}"]`);
            if (checkbox) checkbox.checked = true;
        });
    }
    if (currentFilters.reason_ids) {
        const reasonSelect = document.getElementById('adv-filter-reasons');
        Array.from(reasonSelect.options).forEach(option => {
            option.selected = currentFilters.reason_ids.includes(option.value);
        });
    }
}

// Apply advanced filters
function applyAdvancedFilters() {
    // Get values from advanced modal
    const filters = {
        date_range_start: document.getElementById('adv-filter-date-start').value,
        date_range_end: document.getElementById('adv-filter-date-end').value,
        court_ids: Array.from(document.querySelectorAll('input[name="adv-courts"]:checked')).map(cb => cb.value),
        reason_ids: Array.from(document.getElementById('adv-filter-reasons').selectedOptions).map(o => o.value)
    };
    
    // Update main filter form
    document.getElementById('filter-date-start').value = filters.date_range_start;
    document.getElementById('filter-date-end').value = filters.date_range_end;
    
    const courtSelect = document.getElementById('filter-courts');
    Array.from(courtSelect.options).forEach(option => {
        option.selected = filters.court_ids.includes(option.value);
    });
    
    const reasonSelect = document.getElementById('filter-reasons');
    Array.from(reasonSelect.options).forEach(option => {
        option.selected = filters.reason_ids.includes(option.value);
    });
    
    // Close modal and apply filters
    closeAdvancedFilters();
    applyFilters();
}

// Reset advanced filters
function resetAdvancedFilters() {
    document.getElementById('adv-filter-date-start').value = '';
    document.getElementById('adv-filter-date-end').value = '';
    document.querySelectorAll('input[name="adv-courts"]').forEach(cb => cb.checked = false);
    document.getElementById('adv-filter-reasons').selectedIndex = -1;
}

// Display block list
function displayBlockList(blocks) {
    const container = document.getElementById('blocks-list');
    
    if (!container) return;

    if (blocks.length === 0) {
        container.innerHTML = '<p class="text-gray-600">Keine Sperrungen für die ausgewählten Filter gefunden.</p>';
        return;
    }
    
    const listItems = blocks.map(block => {
        const reasonColor = getReasonColor(block.reason_name);

        return `
            <div class="border border-gray-200 rounded p-4 bg-gray-50 hover:bg-gray-100 transition-colors">
                <div class="flex items-center justify-between">
                    <div class="flex items-center gap-3">
                        <div class="w-4 h-4 rounded" style="background-color: ${reasonColor};" title="${block.reason_name}"></div>
                        <div>
                            <p class="font-semibold">Platz ${block.court_number} - ${block.date} ${block.start_time}-${block.end_time}</p>
                            <p class="text-gray-600">${block.reason_name}${block.details ? ' - ' + block.details : ''}</p>
                            <p class="text-sm text-gray-500">Erstellt von ${block.created_by} am ${new Date(block.created_at).toLocaleDateString('de-DE')}</p>
                        </div>
                    </div>
                    <div class="flex gap-2">
                        <button onclick="editBatch('${block.batch_id}')" class="bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700" title="Bearbeiten">
                            ✏️
                        </button>
                        <button onclick="duplicateBlock(${block.id})" class="bg-yellow-600 text-white px-3 py-1 rounded text-sm hover:bg-yellow-700" title="Duplizieren">
                            📋
                        </button>
                        <button onclick="deleteBatch('${block.batch_id}')" class="bg-red-600 text-white px-3 py-1 rounded text-sm hover:bg-red-700" title="Löschen">
                            🗑️
                        </button>
                    </div>
                </div>
            </div>
        `;
    }).join('');

    container.innerHTML = `<div class="space-y-2">${listItems}</div>`;
}

// Clear filters
function clearFilters() {
    document.getElementById('filter-date-start').value = '';
    document.getElementById('filter-date-end').value = '';
    document.getElementById('filter-courts').selectedIndex = -1;
    document.getElementById('filter-reasons').selectedIndex = -1;
    // Clear stored filters
    currentFilters = {};
    try {
        localStorage.removeItem('adminBlockFilters');
    } catch (error) {
        // Ignore localStorage errors
    }
    
    // Clear results
    document.getElementById('blocks-list').innerHTML = '<p class="text-gray-600">Filter zurückgesetzt. Neue Filter anwenden, um Sperrungen anzuzeigen.</p>';
    
    // Clear filter summary
    const summaryContainer = document.getElementById('filter-summary');
    if (summaryContainer) {
        summaryContainer.innerHTML = '';
    }
}

// Duplicate block
async function duplicateBlock(blockId) {
    try {
        const response = await fetch(`/admin/blocks/${blockId}`);
        const data = await response.json();

        if (!response.ok || !data.block) {
            showToast(data.error || 'Block-Daten nicht gefunden', 'error');
            return;
        }

        const block = data.block;

        document.getElementById('block-court').value = block.court_id;
        document.getElementById('block-date').value = block.date;
        document.getElementById('block-start').value = block.start_time;
        document.getElementById('block-end').value = block.end_time;
        document.getElementById('block-reason').value = block.reason_id;
        document.getElementById('block-details').value = block.details || '';

        showTab('blocks');
        document.getElementById('block-form').scrollIntoView({ behavior: 'smooth' });

        showToast('Block-Daten in Formular geladen', 'info');
    } catch (error) {
        showToast('Fehler beim Laden der Sperrung', 'error');
    }
}

// Delete batch function - deletes entire batch by batch_id
async function deleteBatch(batchId) {
    if (!batchId) {
        showToast('Fehler: Keine Batch-ID gefunden', 'error');
        return;
    }
    
    try {
        // First, get batch details to show proper confirmation message
        const response = await fetch(`/admin/blocks?date_range_start=${new Date().toISOString().split('T')[0]}&date_range_end=${new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]}`);
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
        showBatchDeleteConfirmation(batchId, batchBlocks);
        
    } catch (error) {
        console.error('Error loading batch details:', error);
        showToast('Fehler beim Laden der Sperrungsdetails', 'error');
    }
}

// Show batch delete confirmation modal
function showBatchDeleteConfirmation(batchId, batchBlocks) {
    const isMultiCourt = batchBlocks.length > 1;
    const courtNumbers = batchBlocks.map(b => b.court_number).sort((a, b) => a - b);
    const firstBlock = batchBlocks[0];
    
    const date = new Date(firstBlock.date).toLocaleDateString('de-DE');
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
                <button onclick="confirmBatchDelete('${batchId}')" class="flex-1 bg-red-600 text-white py-2 px-4 rounded hover:bg-red-700">
                    ${isMultiCourt ? `${batchBlocks.length} Sperrungen löschen` : 'Sperrung löschen'}
                </button>
                <button onclick="closeBatchDeleteConfirmation()" class="flex-1 bg-gray-300 text-gray-700 py-2 px-4 rounded hover:bg-gray-400">
                    Abbrechen
                </button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
}

// Close batch delete confirmation modal
function closeBatchDeleteConfirmation() {
    const modal = document.getElementById('batch-delete-modal');
    if (modal) {
        modal.remove();
    }
}

// Confirm and execute batch delete
async function confirmBatchDelete(batchId) {
    closeBatchDeleteConfirmation();
    
    try {
        const response = await fetch(`/admin/blocks/batch/${batchId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showToast(data.message || 'Batch-Sperrung erfolgreich gelöscht', 'success');
            
            // Refresh the blocks list
            if (typeof loadUpcomingBlocks === 'function') {
                loadUpcomingBlocks();
            }
        } else {
            showToast(data.error || 'Fehler beim Löschen der Batch-Sperrung', 'error');
        }
    } catch (error) {
        console.error('Error deleting batch:', error);
        showToast('Fehler beim Löschen der Batch-Sperrung', 'error');
    }
}

// Delete block function - handles both single and multi-court blocks (LEGACY - kept for compatibility)
async function deleteBlock(blockId) {
    try {
        // First, get block details to show proper confirmation message
        const blockResponse = await fetch(`/admin/blocks/${blockId}`);
        if (!blockResponse.ok) {
            showToast('Fehler beim Laden der Sperrungsdetails', 'error');
            return;
        }
        
        const blockData = await blockResponse.json();
        const block = blockData.block;
        
        // Find all related blocks to determine if this is a multi-court block
        const relatedResponse = await fetch(`/admin/blocks?date=${block.date}&start_time=${block.start_time}&end_time=${block.end_time}&reason_id=${block.reason_id}`);
        let relatedBlocks = [];
        
        if (relatedResponse.ok) {
            const relatedData = await relatedResponse.json();
            // Filter blocks that have the same details and were likely created together
            relatedBlocks = relatedData.blocks.filter(b => 
                b.date === block.date &&
                b.start_time === block.start_time &&
                b.end_time === block.end_time &&
                b.reason_id === block.reason_id &&
                b.details === block.details
            );
        }
        
        // Show confirmation modal
        showDeleteConfirmation(blockId, block, relatedBlocks);
        
    } catch (error) {
        console.error('Error preparing delete:', error);
        showToast('Fehler beim Vorbereiten des Löschvorgangs', 'error');
    }
}

// Show delete confirmation modal
function showDeleteConfirmation(blockId, block, relatedBlocks) {
    const isMultiCourt = relatedBlocks.length > 1;
    const courtNumbers = relatedBlocks.map(b => b.court_number).sort((a, b) => a - b);
    
    let title, message, warningText;
    
    if (isMultiCourt) {
        const courtsText = courtNumbers.join(', ');
        title = 'Mehrplatz-Sperrung löschen';
        message = `Plätze ${courtsText}`;
        warningText = `Diese Aktion löscht alle ${relatedBlocks.length} zugehörigen Sperrungen und kann nicht rückgängig gemacht werden.`;
    } else {
        title = 'Sperrung löschen';
        message = `Platz ${block.court_number}`;
        warningText = 'Diese Aktion kann nicht rückgängig gemacht werden.';
    }
    
    const modal = document.createElement('div');
    modal.id = 'delete-confirmation-modal';
    modal.className = 'fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50';
    
    modal.innerHTML = `
        <div class="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <div class="flex items-center justify-between mb-4">
                <h3 class="text-lg font-semibold text-red-600">${title}</h3>
                <button onclick="closeDeleteConfirmation()" class="text-gray-500 hover:text-gray-700">
                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                    </svg>
                </button>
            </div>
            
            <div class="mb-6">
                <div class="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
                    <div class="flex items-center">
                        <svg class="w-5 h-5 text-red-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"></path>
                        </svg>
                        <div>
                            <p class="font-semibold text-red-800">Sperrung löschen</p>
                            <p class="text-red-700">${message}</p>
                        </div>
                    </div>
                </div>
                
                <div class="space-y-2 text-sm text-gray-600">
                    <p><strong>Datum:</strong> ${formatGermanDate(block.date)}</p>
                    <p><strong>Zeit:</strong> ${block.start_time} - ${block.end_time}</p>
                    <p><strong>Grund:</strong> ${block.reason_name}</p>
                    ${block.details ? `<p><strong>Details:</strong> ${block.details}</p>` : ''}
                </div>
                
                <div class="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded">
                    <p class="text-sm text-yellow-800">
                        <strong>Warnung:</strong> ${warningText}
                    </p>
                </div>
            </div>
            
            <div class="flex gap-3">
                <button onclick="confirmDelete(${blockId})" class="flex-1 bg-red-600 text-white py-2 px-4 rounded hover:bg-red-700">
                    ${isMultiCourt ? `${relatedBlocks.length} Sperrungen löschen` : 'Sperrung löschen'}
                </button>
                <button onclick="closeDeleteConfirmation()" class="flex-1 bg-gray-600 text-white py-2 px-4 rounded hover:bg-gray-700">
                    Abbrechen
                </button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
}

// Close delete confirmation modal
function closeDeleteConfirmation() {
    const modal = document.getElementById('delete-confirmation-modal');
    if (modal) {
        modal.remove();
    }
}

// Confirm and execute delete
async function confirmDelete(blockId) {
    closeDeleteConfirmation();
    
    try {
        const response = await fetch(`/admin/blocks/batch/${blockId}`, {
            method: 'DELETE'
        });

        const data = await response.json();
        
        if (response.ok) {
            showToast(data.message, 'success');
            
            // Refresh the blocks list
            if (typeof loadUpcomingBlocks === 'function') {
                loadUpcomingBlocks();
            }
            
            // If we're on a page with filters, refresh those too
            if (typeof applyFilters === 'function') {
                applyFilters();
            }
        } else {
            showToast(data.error || 'Fehler beim Löschen der Sperrung', 'error');
        }
    } catch (error) {
        console.error('Error deleting block:', error);
        showToast('Fehler beim Löschen der Sperrung', 'error');
    }
}

// Helper function to format German date
function formatGermanDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('de-DE');
}

// Load reason list
async function loadReasonList() {
    try {
        const response = await fetch('/admin/block-reasons');
        const data = await response.json();
        
        if (response.ok) {
            displayReasonList(data.reasons);
        } else {
            showToast(data.error || 'Fehler beim Laden der Sperrungsgründe', 'error');
        }
    } catch (error) {
        showToast('Fehler beim Laden der Sperrungsgründe', 'error');
    }
}

// Display reason list with enhanced status indicators
function displayReasonList(reasons) {
    const container = document.getElementById('reason-list');
    
    if (reasons.length === 0) {
        container.innerHTML = '<p class="text-gray-600">Keine Sperrungsgründe vorhanden.</p>';
        return;
    }
    
    let html = '<div class="space-y-4">';
    
    reasons.forEach(reason => {
        const statusBadge = reason.is_active ? 
            '<span class="bg-green-100 text-green-800 text-xs px-2 py-1 rounded">Aktiv</span>' :
            '<span class="bg-gray-100 text-gray-800 text-xs px-2 py-1 rounded">Inaktiv</span>';
        
        const usageWarning = reason.usage_count > 0 ? 
            '<span class="text-yellow-600 text-xs">⚠️ In Verwendung</span>' : 
            '<span class="text-green-600 text-xs">✓ Nicht verwendet</span>';
        
        html += `
            <div class="border border-gray-200 rounded p-4 bg-gray-50 hover:bg-gray-100 transition-colors">
                <div class="flex items-start justify-between">
                    <div class="flex-1">
                        <div class="flex items-center gap-2 mb-2">
                            <h4 class="font-semibold text-lg">${reason.name}</h4>
                            ${statusBadge}
                        </div>
                        <div class="space-y-1 text-sm text-gray-600">
                            <div class="flex items-center gap-4">
                                <span>${GERMAN_TEXT.REASON_IN_USE} in ${reason.usage_count} Sperrung(en)</span>
                                ${usageWarning}
                            </div>
                            <p>Erstellt von ${reason.created_by} am ${new Date(reason.created_at).toLocaleDateString('de-DE')}</p>
                        </div>
                    </div>
                    <div class="flex flex-col gap-2 ml-4">
                        <button onclick="editReasonModal(${reason.id})" 
                                class="bg-green-600 text-white px-3 py-1 rounded text-sm hover:bg-green-700" 
                                title="Grund bearbeiten">
                            ✏️ Bearbeiten
                        </button>
                        <button onclick="deleteReasonWithWarning(${reason.id}, ${reason.usage_count})" 
                                class="bg-red-600 text-white px-3 py-1 rounded text-sm hover:bg-red-700" 
                                title="Grund löschen">
                            🗑️ Löschen
                        </button>
                    </div>
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    container.innerHTML = html;
}

// Enhanced reason editing modal
function editReasonModal(reasonId) {
    // Find the reason data
    const reason = blockReasons.find(r => r.id === reasonId);
    if (!reason) {
        showToast('Grund nicht gefunden', 'error');
        return;
    }
    
    let html = `
        <div id="edit-reason-modal" class="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
            <div class="bg-white rounded-lg p-6 max-w-2xl w-full mx-4">
                <div class="flex items-center justify-between mb-4">
                    <h3 class="text-lg font-semibold">Sperrungsgrund bearbeiten</h3>
                    <button onclick="closeEditReasonModal()" class="text-gray-500 hover:text-gray-700">
                        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                        </svg>
                    </button>
                </div>
                
                <form id="edit-reason-form" class="space-y-4">
                    <div>
                        <label class="block text-gray-700 font-semibold mb-2">Name des Sperrungsgrundes</label>
                        <input type="text" id="edit-reason-name" value="${reason.name}" 
                               class="w-full border border-gray-300 rounded px-3 py-2" required>
                    </div>
                    
                    <div>
                        <label class="block text-gray-700 font-semibold mb-2">Status</label>
                        <div class="flex items-center gap-4">
                            <label class="flex items-center">
                                <input type="radio" name="reason-status" value="true" 
                                       ${reason.is_active ? 'checked' : ''} class="mr-2">
                                <span class="text-green-600">✓ Aktiv</span>
                            </label>
                            <label class="flex items-center">
                                <input type="radio" name="reason-status" value="false" 
                                       ${!reason.is_active ? 'checked' : ''} class="mr-2">
                                <span class="text-gray-600">○ Inaktiv</span>
                            </label>
                        </div>
                        <p class="text-sm text-gray-500 mt-1">
                            Inaktive Gründe können nicht für neue Sperrungen verwendet werden, 
                            bleiben aber in bestehenden Sperrungen erhalten.
                        </p>
                    </div>
                    
                    <div class="bg-blue-50 p-3 rounded">
                        <h4 class="font-semibold text-blue-800 mb-2">Verwendungsstatistik</h4>
                        <div class="text-sm text-blue-700">
                            <p>• Aktuell in ${reason.usage_count} Sperrung(en) verwendet</p>
                            <p>• Erstellt von ${reason.created_by} am ${new Date(reason.created_at).toLocaleDateString('de-DE')}</p>
                            ${reason.usage_count > 0 ? 
                                '<p class="text-yellow-700 mt-2">⚠️ Änderungen betreffen nur zukünftige Sperrungen. Bestehende Sperrungen bleiben unverändert.</p>' : 
                                '<p class="text-green-700 mt-2">✓ Dieser Grund wird derzeit nicht verwendet.</p>'
                            }
                        </div>
                    </div>
                    
                    <div class="flex gap-2">
                        <button type="submit" class="bg-green-600 text-white py-2 px-6 rounded hover:bg-green-700">
                            Änderungen speichern
                        </button>
                        <button type="button" onclick="closeEditReasonModal()" class="bg-gray-600 text-white py-2 px-6 rounded hover:bg-gray-700">
                            Abbrechen
                        </button>
                    </div>
                </form>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', html);
    
    // Setup form submission
    document.getElementById('edit-reason-form').addEventListener('submit', function(e) {
        e.preventDefault();
        updateReasonEnhanced(reasonId);
    });
}

// Close edit reason modal
function closeEditReasonModal() {
    const modal = document.getElementById('edit-reason-modal');
    if (modal) {
        modal.remove();
    }
}

// Enhanced reason update
async function updateReasonEnhanced(reasonId) {
    const name = document.getElementById('edit-reason-name').value.trim();
    const isActive = document.querySelector('input[name="reason-status"]:checked').value === 'true';
    
    if (!name) {
        showToast('Bitte einen Namen eingeben', 'error');
        return;
    }
    
    try {
        const response = await fetch(`/admin/block-reasons/${reasonId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                name: name,
                is_active: isActive
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showToast(data.message);
            closeEditReasonModal();
            loadBlockReasons(); // Refresh reasons
            loadReasonList(); // Refresh the reason list
        } else {
            showToast(data.error || 'Fehler beim Aktualisieren des Sperrungsgrundes', 'error');
        }
    } catch (error) {
        showToast('Fehler beim Aktualisieren des Sperrungsgrundes', 'error');
    }
}

// Enhanced reason deletion with usage warnings
function deleteReasonWithWarning(reasonId, usageCount) {
    const reason = blockReasons.find(r => r.id === reasonId);
    if (!reason) {
        showToast('Grund nicht gefunden', 'error');
        return;
    }
    
    let warningMessage = `Möchten Sie den Sperrungsgrund "${reason.name}" wirklich löschen?`;
    
    if (usageCount > 0) {
        warningMessage += `\n\n⚠️ WARNUNG: Dieser Grund wird derzeit in ${usageCount} Sperrung(en) verwendet.\n\n`;
        warningMessage += `${GERMAN_TEXT.HISTORICAL_DATA_PRESERVED}\n`;
        warningMessage += `Bestehende Sperrungen behalten ihren Grund, aber zukünftige Sperrungen können diesen Grund nicht mehr verwenden.`;
    } else {
        warningMessage += `\n\n✓ Dieser Grund wird derzeit nicht verwendet und kann sicher gelöscht werden.`;
    }
    
    if (confirm(warningMessage)) {
        deleteReasonEnhanced(reasonId);
    }
}

// Enhanced reason deletion
async function deleteReasonEnhanced(reasonId) {
    try {
        const response = await fetch(`/admin/block-reasons/${reasonId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showToast(data.message);
            loadBlockReasons(); // Refresh reasons
            loadReasonList(); // Refresh the reason list
        } else {
            showToast(data.error || 'Fehler beim Löschen des Sperrungsgrundes', 'error');
        }
    } catch (error) {
        showToast('Fehler beim Löschen des Sperrungsgrundes', 'error');
    }
}

// Load audit log
async function loadAuditLog() {
    try {
        const response = await fetch('/admin/blocks/audit-log');
        const data = await response.json();
        
        if (response.ok) {
            // For now, just show a toast - could open a modal with audit log
            showToast(`Audit-Protokoll geladen: ${data.audit_logs.length} Einträge`);
        } else {
            showToast(data.error || 'Fehler beim Laden des Audit-Protokolls', 'error');
        }
    } catch (error) {
        showToast('Fehler beim Laden des Audit-Protokolls', 'error');
    }
}

// Utility function to show toast messages
function showToast(message, type = 'success') {
    // Use existing toast function from utils.js if available
    if (typeof window.showToast === 'function') {
        window.showToast(message, type);
    } else {
        // Fallback alert
        alert(message);
    }
}

// Calendar View Functions

// Render calendar view
function renderCalendarView() {
    const calendarContainer = document.getElementById('calendar-view');
    if (!calendarContainer) return;
    
    const year = currentCalendarDate.getFullYear();
    const month = currentCalendarDate.getMonth();
    
    // Create calendar header
    const monthNames = [
        'Januar', 'Februar', 'März', 'April', 'Mai', 'Juni',
        'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember'
    ];
    
    let html = `
        <div class="calendar-header flex items-center justify-between mb-4">
            <button onclick="navigateCalendar(-1)" class="bg-gray-600 text-white px-3 py-1 rounded hover:bg-gray-700">
                ← Vorheriger Monat
            </button>
            <h3 class="text-xl font-semibold">${monthNames[month]} ${year}</h3>
            <button onclick="navigateCalendar(1)" class="bg-gray-600 text-white px-3 py-1 rounded hover:bg-gray-700">
                Nächster Monat →
            </button>
        </div>
    `;
    
    // Create calendar grid
    html += '<div class="calendar-grid grid grid-cols-7 gap-1 mb-4">';
    
    // Day headers
    const dayNames = ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So'];
    dayNames.forEach(day => {
        html += `<div class="calendar-day-header text-center font-semibold p-2 bg-gray-100">${day}</div>`;
    });
    
    // Get first day of month and number of days
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const daysInMonth = lastDay.getDate();
    const startingDayOfWeek = (firstDay.getDay() + 6) % 7; // Convert Sunday=0 to Monday=0
    
    // Empty cells for days before month starts
    for (let i = 0; i < startingDayOfWeek; i++) {
        html += '<div class="calendar-day-empty p-2"></div>';
    }
    
    // Days of the month
    for (let day = 1; day <= daysInMonth; day++) {
        const date = new Date(year, month, day);
        const dateStr = date.toISOString().split('T')[0];
        const dayBlocks = calendarBlocks.filter(block => block.date === dateStr);
        
        let dayClass = 'calendar-day p-2 border border-gray-200 min-h-[80px] cursor-pointer hover:bg-gray-50';
        let blockIndicators = '';
        
        if (dayBlocks.length > 0) {
            dayClass += ' has-blocks';
            
            // Group blocks by reason for color coding
            const reasonGroups = {};
            dayBlocks.forEach(block => {
                if (!reasonGroups[block.reason_name]) {
                    reasonGroups[block.reason_name] = [];
                }
                reasonGroups[block.reason_name].push(block);
            });
            
            // Create color-coded indicators
            Object.entries(reasonGroups).forEach(([reason, blocks]) => {
                const color = getReasonColor(reason);
                blockIndicators += `
                    <div class="block-indicator text-xs p-1 mb-1 rounded" 
                         style="background-color: ${color}; color: white;"
                         title="${reason}: ${blocks.length} Sperrung(en)">
                        ${reason.substring(0, 8)}${reason.length > 8 ? '...' : ''} (${blocks.length})
                    </div>
                `;
            });
        }
        
        html += `
            <div class="${dayClass}" onclick="showDayDetails('${dateStr}')" data-date="${dateStr}">
                <div class="day-number font-semibold mb-1">${day}</div>
                <div class="block-indicators">
                    ${blockIndicators}
                </div>
            </div>
        `;
    }
    
    html += '</div>';
    
    // Add legend
    html += `
        <div class="calendar-legend">
            <h4 class="font-semibold mb-2">Legende:</h4>
            <div class="flex flex-wrap gap-2">
                ${getReasonLegend()}
            </div>
        </div>
    `;
    
    calendarContainer.innerHTML = html;
    
    // Load blocks for current month
    loadCalendarBlocks();
}

// Navigate calendar months
function navigateCalendar(direction) {
    currentCalendarDate.setMonth(currentCalendarDate.getMonth() + direction);
    renderCalendarView();
}

// Load blocks for calendar view
async function loadCalendarBlocks() {
    const year = currentCalendarDate.getFullYear();
    const month = currentCalendarDate.getMonth();
    
    const startDate = new Date(year, month, 1).toISOString().split('T')[0];
    const endDate = new Date(year, month + 1, 0).toISOString().split('T')[0];
    
    try {
        const response = await fetch(`/admin/blocks?date_range_start=${startDate}&date_range_end=${endDate}`);
        const data = await response.json();
        
        if (response.ok) {
            calendarBlocks = data.blocks;
            updateCalendarDisplay();
        } else {
            showToast(data.error || 'Fehler beim Laden der Kalender-Sperrungen', 'error');
        }
    } catch (error) {
        showToast('Fehler beim Laden der Kalender-Sperrungen', 'error');
    }
}

// Update calendar display with loaded blocks
function updateCalendarDisplay() {
    calendarBlocks.forEach(block => {
        const dayElement = document.querySelector(`[data-date="${block.date}"]`);
        if (dayElement) {
            const indicatorsContainer = dayElement.querySelector('.block-indicators');
            if (indicatorsContainer) {
                // Update indicators (this is handled in renderCalendarView)
                // We could add real-time updates here if needed
            }
        }
    });
}

// Show day details modal
function showDayDetails(dateStr) {
    const dayBlocks = calendarBlocks.filter(block => block.date === dateStr);
    
    if (dayBlocks.length === 0) {
        showToast('Keine Sperrungen für diesen Tag', 'info');
        return;
    }
    
    let html = `
        <div class="day-details-modal fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
            <div class="bg-white rounded-lg p-6 max-w-4xl w-full mx-4 max-h-[80vh] overflow-y-auto">
                <div class="flex items-center justify-between mb-4">
                    <h3 class="text-lg font-semibold">Sperrungen für ${formatGermanDate(dateStr)}</h3>
                    <button onclick="closeDayDetails()" class="text-gray-500 hover:text-gray-700">
                        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                        </svg>
                    </button>
                </div>
                <div class="space-y-3">
    `;
    
    dayBlocks.forEach(block => {
        const color = getReasonColor(block.reason_name);
        
        html += `
            <div class="block-detail-item border rounded p-3" style="border-left: 4px solid ${color};">
                <div class="flex items-center justify-between">
                    <div>
                        <p class="font-semibold">Platz ${block.court_number} - ${block.start_time}-${block.end_time}</p>
                        <p class="text-gray-600">${block.reason_name}${block.details ? ' - ' + block.details : ''}</p>
                        <p class="text-sm text-gray-500">Erstellt von ${block.created_by}</p>
                    </div>
                    <div class="flex gap-2">
                        <button onclick="editBatch('${block.batch_id}')" 
                                class="bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700"
                                title="Bearbeiten">
                            ✏️
                        </button>
                        <button onclick="deleteBatch('${block.batch_id}')" 
                                class="bg-red-600 text-white px-3 py-1 rounded text-sm hover:bg-red-700"
                                title="Löschen">
                            🗑️
                        </button>
                    </div>
                </div>
            </div>
        `;
    });
    
    html += `
                </div>
                <div class="mt-6 flex justify-end">
                    <button onclick="closeDayDetails()" class="bg-gray-600 text-white py-2 px-4 rounded hover:bg-gray-700">
                        Schließen
                    </button>
                </div>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', html);
}

// Close day details modal
function closeDayDetails() {
    const modal = document.querySelector('.day-details-modal');
    if (modal) {
        modal.remove();
    }
}

// Get color for block reason
function getReasonColor(reasonName) {
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

// Get reason legend HTML
function getReasonLegend() {
    const uniqueReasons = [...new Set(calendarBlocks.map(block => block.reason_name))];
    
    return uniqueReasons.map(reason => {
        const color = getReasonColor(reason);
        return `
            <div class="flex items-center gap-1">
                <div class="w-4 h-4 rounded" style="background-color: ${color};"></div>
                <span class="text-sm">${reason}</span>
            </div>
        `;
    }).join('');
}

// Format date in German format
function formatGermanDate(dateStr) {
    const date = new Date(dateStr + 'T00:00:00');
    return date.toLocaleDateString('de-DE', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
}

// Edit block function
function editBlock(blockId) {
    // Legacy function - redirect to batch-based edit
    window.location.href = `/admin/court-blocking/${blockId}`;
}

function editBatch(batchIdentifier) {
    // Navigate to the batch-based edit URL
    window.location.href = `/admin/court-blocking/${batchIdentifier}`;
}

// Load upcoming blocks automatically
async function loadUpcomingBlocks() {
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
        // Get upcoming blocks (from today onwards)
        const today = new Date().toISOString().split('T')[0];
        const nextMonth = new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
        
        const params = new URLSearchParams({
            date_range_start: today,
            date_range_end: nextMonth
        });
        
        const response = await fetch(`/admin/blocks?${params.toString()}`);
        const data = await response.json();
        
        if (response.ok) {
            displayUpcomingBlocks(data.blocks);
        } else {
            blocksList.innerHTML = `
                <div class="p-4 text-center text-red-600">
                    Fehler beim Laden der Sperrungen: ${data.error || 'Unbekannter Fehler'}
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

// Display upcoming blocks in a simple list
function displayUpcomingBlocks(blocks) {
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
    
    // Group blocks by batch (same date, time, reason, details, created_at)
    const groupedBlocks = groupBlocksByBatch(blocks);
    
    let html = '<div class="divide-y divide-gray-200">';
    
    groupedBlocks.forEach(group => {
        const firstBlock = group.blocks[0];
        const date = new Date(firstBlock.date).toLocaleDateString('de-DE');
        const startTime = firstBlock.start_time.slice(0, 5); // Remove seconds
        const endTime = firstBlock.end_time.slice(0, 5); // Remove seconds
        
        // Sort court numbers for consistent display
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
        
        // Determine the batch identifier for edit/delete operations
        const batchIdentifier = firstBlock.batch_id ? `batch_${firstBlock.batch_id}` : `single_${firstBlock.id}`;
        
        html += `
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
                    <button onclick="editBatch('${batchIdentifier}')" class="text-blue-600 hover:text-blue-800 text-sm">
                        Bearbeiten
                    </button>
                    <button onclick="deleteBatch('${firstBlock.batch_id}')" class="text-red-600 hover:text-red-800 text-sm">
                        Löschen
                    </button>
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    blocksList.innerHTML = html;
}

// Group blocks by batch booking using batch_id
function groupBlocksByBatch(blocks) {
    const groups = new Map();
    
    blocks.forEach(block => {
        // Every block now has a batch_id
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
