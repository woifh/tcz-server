/**
 * Enhanced Admin Panel JavaScript
 * Handles all advanced block management functionality
 */

// German text constants for enhanced admin features
const GERMAN_TEXT = {
    // Recurring block features
    RECURRING_BLOCK: 'Wiederkehrende Sperrung',
    EDIT_SERIES: 'Serie bearbeiten',
    EDIT_SINGLE_INSTANCE: 'Einzelne Instanz bearbeiten',
    ALL_FUTURE_INSTANCES: 'Alle zukünftigen Instanzen',
    DELETE_ENTIRE_SERIES: 'Gesamte Serie löschen',
    
    // Template features
    BLOCK_TEMPLATE: 'Sperrungsvorlage',
    APPLY_TEMPLATE: 'Vorlage anwenden',
    SAVE_TEMPLATE: 'Vorlage speichern',
    
    // Reason management
    MANAGE_BLOCK_REASON: 'Sperrungsgrund verwalten',
    SUB_REASON: 'Untergrund',
    REASON_IN_USE: 'Grund wird verwendet',
    HISTORICAL_DATA_PRESERVED: 'Historische Daten bleiben erhalten',
    
    // Calendar and filtering
    CALENDAR_VIEW: 'Kalenderansicht',
    MONTHLY_VIEW: 'Monatliche Ansicht',
    CONFLICT_PREVIEW: 'Konflikt-Vorschau',
    AFFECTED_RESERVATIONS: 'Betroffene Buchungen'
};

let blockReasons = [];
let blockTemplates = [];
let selectedBlocks = [];
let currentCalendarDate = new Date();
let calendarBlocks = [];
let currentFilters = {};
let filterUpdateTimeout = null;

// Initialize admin panel
function initializeAdminPanel() {
    loadBlockReasons();
    loadBlockTemplates();
    setupEventListeners();
    
    // Set default dates
    const today = new Date().toISOString().split('T')[0];
    const nextWeek = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
    
    document.getElementById('block-date').value = today;
    document.getElementById('multi-date').value = today;
    document.getElementById('series-start-date').value = today;
    document.getElementById('series-end-date').value = nextWeek;
    document.getElementById('filter-date-start').value = today;
    document.getElementById('filter-date-end').value = nextWeek;
    
    // Initialize calendar view
    initializeCalendarView();
    
    // Load saved filters
    loadSavedFilters();
    
    // Setup dynamic filtering
    setupDynamicFiltering();
}

// Load block templates
async function loadBlockTemplates() {
    try {
        const response = await fetch('/admin/block-templates');
        const data = await response.json();
        
        if (response.ok) {
            blockTemplates = data.templates;
        } else {
            showToast(data.error || 'Fehler beim Laden der Vorlagen', 'error');
        }
    } catch (error) {
        showToast('Fehler beim Laden der Vorlagen', 'error');
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
    
    // Series form
    const seriesForm = document.getElementById('series-form');
    if (seriesForm) {
        seriesForm.addEventListener('submit', handleSeriesSubmit);
    }
    
    // Template form
    const templateForm = document.getElementById('template-form');
    if (templateForm) {
        templateForm.addEventListener('submit', handleTemplateSubmit);
    }
    
    // Reason form
    const reasonForm = document.getElementById('reason-form');
    if (reasonForm) {
        reasonForm.addEventListener('submit', handleReasonSubmit);
    }
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
    } else if (tabName === 'recurring') {
        loadSeriesList();
    } else if (tabName === 'templates') {
        loadTemplateList();
    } else if (tabName === 'reasons') {
        loadReasonList();
    }
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
    const selects = [
        'block-reason', 'multi-reason', 'series-reason', 
        'template-reason', 'filter-reasons'
    ];
    
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
    
    const selectedCourts = Array.from(document.querySelectorAll('input[name="multi-courts"]:checked'))
        .map(cb => parseInt(cb.value));
    
    if (selectedCourts.length === 0) {
        showToast('Bitte mindestens einen Platz auswählen', 'error');
        return;
    }
    
    const blockData = {
        court_ids: selectedCourts,
        date: document.getElementById('multi-date').value,
        start_time: document.getElementById('multi-start').value,
        end_time: document.getElementById('multi-end').value,
        reason_id: parseInt(document.getElementById('multi-reason').value),
        sub_reason: document.getElementById('multi-sub-reason').value
    };
    
    try {
        const response = await fetch('/admin/blocks/multi-court', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(blockData)
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showToast(data.message);
            e.target.reset();
            applyFilters(); // Refresh the list
        } else {
            showToast(data.error || 'Unbekannter Fehler', 'error');
        }
    } catch (error) {
        showToast('Fehler beim Erstellen der Mehrplatz-Sperrung', 'error');
    }
}

// Handle series form submission
async function handleSeriesSubmit(e) {
    e.preventDefault();
    
    const selectedCourts = Array.from(document.querySelectorAll('input[name="series-courts"]:checked'))
        .map(cb => parseInt(cb.value));
    
    if (selectedCourts.length === 0) {
        showToast('Bitte mindestens einen Platz auswählen', 'error');
        return;
    }
    
    const seriesName = document.getElementById('series-name').value.trim();
    if (!seriesName) {
        showToast('Bitte einen Seriennamen eingeben', 'error');
        return;
    }
    
    const startDate = document.getElementById('series-start-date').value;
    const endDate = document.getElementById('series-end-date').value;
    
    if (new Date(startDate) >= new Date(endDate)) {
        showToast('Enddatum muss nach dem Startdatum liegen', 'error');
        return;
    }
    
    const recurrencePattern = document.getElementById('series-pattern').value;
    let recurrenceDays = [];
    
    if (recurrencePattern === 'weekly') {
        recurrenceDays = Array.from(document.querySelectorAll('input[name="recurrence-days"]:checked'))
            .map(cb => parseInt(cb.value));
        
        if (recurrenceDays.length === 0) {
            showToast('Bitte mindestens einen Wochentag auswählen', 'error');
            return;
        }
    }
    
    const seriesData = {
        series_name: seriesName,
        court_ids: selectedCourts,
        start_date: startDate,
        end_date: endDate,
        start_time: document.getElementById('series-start-time').value,
        end_time: document.getElementById('series-end-time').value,
        recurrence_pattern: recurrencePattern,
        recurrence_days: recurrenceDays,
        reason_id: parseInt(document.getElementById('series-reason').value),
        sub_reason: document.getElementById('series-sub-reason').value
    };
    
    // Show loading state
    const submitButton = e.target.querySelector('button[type="submit"]');
    const originalText = submitButton.textContent;
    submitButton.textContent = 'Erstelle Serie...';
    submitButton.disabled = true;
    
    try {
        const response = await fetch('/admin/blocks/series', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(seriesData)
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showToast(data.message);
            e.target.reset();
            document.getElementById('recurrence-days-container').classList.add('hidden');
            loadSeriesList(); // Refresh the series list
        } else {
            showToast(data.error || 'Unbekannter Fehler', 'error');
        }
    } catch (error) {
        showToast('Fehler beim Erstellen der Serie', 'error');
    } finally {
        // Restore button state
        submitButton.textContent = originalText;
        submitButton.disabled = false;
    }
}

// Handle template form submission
async function handleTemplateSubmit(e) {
    e.preventDefault();
    
    // Use preview functionality instead of direct submission
    createTemplateWithPreview();
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

// Toggle recurrence days visibility
function toggleRecurrenceDays() {
    const pattern = document.getElementById('series-pattern').value;
    const container = document.getElementById('recurrence-days-container');
    
    if (pattern === 'weekly') {
        container.classList.remove('hidden');
    } else {
        container.classList.add('hidden');
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
        reason_ids: Array.from(document.getElementById('filter-reasons').selectedOptions).map(o => o.value),
        block_types: getSelectedBlockTypes()
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

// Get selected block types
function getSelectedBlockTypes() {
    const blockTypes = [];
    if (document.getElementById('filter-single-blocks')?.checked) {
        blockTypes.push('single');
    }
    if (document.getElementById('filter-series-blocks')?.checked) {
        blockTypes.push('series');
    }
    return blockTypes;
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
    if (filters.block_types.length > 0) {
        const typeNames = filters.block_types.map(type => 
            type === 'single' ? 'Einzeln' : 'Serie'
        );
        activeFilters.push(`Typen: ${typeNames.join(', ')}`);
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
    
    // Setup block type checkboxes if they exist
    const blockTypeCheckboxes = document.querySelectorAll('input[name="block-types"]');
    blockTypeCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', debounceFilterUpdate);
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
                    
                    <!-- Reasons and Types -->
                    <div class="space-y-4">
                        <h4 class="font-semibold">Gründe & Typen</h4>
                        <div>
                            <label class="block text-sm font-medium mb-1">Sperrungsgründe</label>
                            <select id="adv-filter-reasons" multiple class="w-full border border-gray-300 rounded px-3 py-2" size="4">
                                <!-- Will be populated by JavaScript -->
                            </select>
                        </div>
                        <div>
                            <label class="block text-sm font-medium mb-1">Sperrungstypen</label>
                            <div class="space-y-1">
                                <label class="flex items-center">
                                    <input type="checkbox" name="adv-block-types" value="single" class="mr-2"> Einzelsperrungen
                                </label>
                                <label class="flex items-center">
                                    <input type="checkbox" name="adv-block-types" value="series" class="mr-2"> Seriensperrungen
                                </label>
                            </div>
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
    if (currentFilters.block_types) {
        currentFilters.block_types.forEach(type => {
            const checkbox = document.querySelector(`input[name="adv-block-types"][value="${type}"]`);
            if (checkbox) checkbox.checked = true;
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
        reason_ids: Array.from(document.getElementById('adv-filter-reasons').selectedOptions).map(o => o.value),
        block_types: Array.from(document.querySelectorAll('input[name="adv-block-types"]:checked')).map(cb => cb.value)
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
    document.querySelectorAll('input[name="adv-block-types"]').forEach(cb => cb.checked = false);
}

// Display block list
function displayBlockList(blocks) {
    const container = document.getElementById('blocks-list');
    
    if (blocks.length === 0) {
        container.innerHTML = '<p class="text-gray-600">Keine Sperrungen für die ausgewählten Filter gefunden.</p>';
        return;
    }
    
    let html = `
        <div class="mb-4 flex items-center justify-between">
            <div class="flex items-center gap-4">
                <label class="flex items-center">
                    <input type="checkbox" id="select-all-blocks" onchange="toggleAllBlocks()" class="mr-2">
                    Alle auswählen (${blocks.length})
                </label>
                <span id="selection-count" class="text-sm text-gray-600">0 ausgewählt</span>
            </div>
            <div class="flex gap-2">
                <button onclick="bulkDeleteSelected()" id="bulk-delete-btn" class="bg-red-600 text-white px-3 py-1 rounded text-sm hover:bg-red-700 disabled:opacity-50" disabled>
                    Ausgewählte löschen
                </button>
                <button onclick="bulkExportSelected()" id="bulk-export-btn" class="bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700 disabled:opacity-50" disabled>
                    Exportieren
                </button>
                <button onclick="showBulkEditModal()" id="bulk-edit-btn" class="bg-green-600 text-white px-3 py-1 rounded text-sm hover:bg-green-700 disabled:opacity-50" disabled>
                    Massenbearbeitung
                </button>
            </div>
        </div>
        <div class="space-y-2">
    `;
    
    blocks.forEach(block => {
        const seriesInfo = block.series_id ? ` (Serie ${block.series_id}${block.is_modified ? ', modifiziert' : ''})` : '';
        const reasonColor = getReasonColor(block.reason_name);
        
        html += `
            <div class="border border-gray-200 rounded p-4 bg-gray-50 hover:bg-gray-100 transition-colors">
                <div class="flex items-center justify-between">
                    <div class="flex items-center">
                        <input type="checkbox" class="block-checkbox mr-3" value="${block.id}" onchange="updateSelectedBlocks()" data-block='${JSON.stringify(block)}'>
                        <div class="flex items-center gap-3">
                            <div class="w-4 h-4 rounded" style="background-color: ${reasonColor};" title="${block.reason_name}"></div>
                            <div>
                                <p class="font-semibold">Platz ${block.court_number} - ${block.date} ${block.start_time}-${block.end_time}</p>
                                <p class="text-gray-600">${block.reason_name}${block.sub_reason ? ' - ' + block.sub_reason : ''}${seriesInfo}</p>
                                <p class="text-sm text-gray-500">Erstellt von ${block.created_by} am ${new Date(block.created_at).toLocaleDateString('de-DE')}</p>
                            </div>
                        </div>
                    </div>
                    <div class="flex gap-2">
                        ${block.series_id ? `
                            <button onclick="editSeries(${block.series_id})" class="bg-purple-600 text-white px-3 py-1 rounded text-sm hover:bg-purple-700" title="Serie bearbeiten">
                                Serie
                            </button>
                        ` : ''}
                        <button onclick="editBlock(${block.id})" class="bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700" title="Bearbeiten">
                            ✏️
                        </button>
                        <button onclick="duplicateBlock(${block.id})" class="bg-yellow-600 text-white px-3 py-1 rounded text-sm hover:bg-yellow-700" title="Duplizieren">
                            📋
                        </button>
                        <button onclick="deleteBlock(${block.id})" class="bg-red-600 text-white px-3 py-1 rounded text-sm hover:bg-red-700" title="Löschen">
                            🗑️
                        </button>
                    </div>
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    container.innerHTML = html;
    
    // Reset selection
    selectedBlocks = [];
    updateBulkActionButtons();
}

// Clear filters
function clearFilters() {
    document.getElementById('filter-date-start').value = '';
    document.getElementById('filter-date-end').value = '';
    document.getElementById('filter-courts').selectedIndex = -1;
    document.getElementById('filter-reasons').selectedIndex = -1;
    
    // Clear block type filters if they exist
    document.querySelectorAll('input[name="block-types"]').forEach(cb => cb.checked = false);
    
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

// Toggle all blocks selection
function toggleAllBlocks() {
    const selectAll = document.getElementById('select-all-blocks');
    const checkboxes = document.querySelectorAll('.block-checkbox');
    
    checkboxes.forEach(cb => {
        cb.checked = selectAll.checked;
    });
    
    updateSelectedBlocks();
}

// Update selected blocks array and UI
function updateSelectedBlocks() {
    const checkboxes = document.querySelectorAll('.block-checkbox:checked');
    selectedBlocks = Array.from(checkboxes).map(cb => {
        return {
            id: parseInt(cb.value),
            data: JSON.parse(cb.dataset.block)
        };
    });
    
    // Update selection count
    const countElement = document.getElementById('selection-count');
    if (countElement) {
        countElement.textContent = `${selectedBlocks.length} ausgewählt`;
    }
    
    // Update select all checkbox
    const selectAllCheckbox = document.getElementById('select-all-blocks');
    const allCheckboxes = document.querySelectorAll('.block-checkbox');
    if (selectAllCheckbox && allCheckboxes.length > 0) {
        selectAllCheckbox.indeterminate = selectedBlocks.length > 0 && selectedBlocks.length < allCheckboxes.length;
        selectAllCheckbox.checked = selectedBlocks.length === allCheckboxes.length;
    }
    
    updateBulkActionButtons();
}

// Update bulk action button states
function updateBulkActionButtons() {
    const hasSelection = selectedBlocks.length > 0;
    
    const bulkDeleteBtn = document.getElementById('bulk-delete-btn');
    const bulkExportBtn = document.getElementById('bulk-export-btn');
    const bulkEditBtn = document.getElementById('bulk-edit-btn');
    
    if (bulkDeleteBtn) bulkDeleteBtn.disabled = !hasSelection;
    if (bulkExportBtn) bulkExportBtn.disabled = !hasSelection;
    if (bulkEditBtn) bulkEditBtn.disabled = !hasSelection;
}

// Enhanced bulk delete with conflict preview
async function bulkDeleteSelected() {
    if (selectedBlocks.length === 0) {
        showToast('Keine Sperrungen ausgewählt', 'error');
        return;
    }
    
    // Show confirmation modal with details
    showBulkDeleteConfirmation();
}

// Show bulk delete confirmation modal
function showBulkDeleteConfirmation() {
    const blockIds = selectedBlocks.map(b => b.id);
    const seriesBlocks = selectedBlocks.filter(b => b.data.series_id);
    const singleBlocks = selectedBlocks.filter(b => !b.data.series_id);
    
    let html = `
        <div id="bulk-delete-modal" class="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
            <div class="bg-white rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto">
                <div class="flex items-center justify-between mb-4">
                    <h3 class="text-lg font-semibold text-red-600">Massenlöschung bestätigen</h3>
                    <button onclick="closeBulkDeleteModal()" class="text-gray-500 hover:text-gray-700">
                        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                        </svg>
                    </button>
                </div>
                
                <div class="space-y-4">
                    <div class="bg-red-50 p-4 rounded-lg">
                        <p class="text-red-800 font-semibold">Sie sind dabei, ${selectedBlocks.length} Sperrung(en) zu löschen:</p>
                        <ul class="mt-2 text-sm text-red-700">
                            <li>• ${singleBlocks.length} Einzelsperrung(en)</li>
                            <li>• ${seriesBlocks.length} Seriensperrung(en)</li>
                        </ul>
                    </div>
                    
                    <div class="max-h-40 overflow-y-auto border border-gray-200 rounded p-3">
                        <h4 class="font-semibold mb-2">Ausgewählte Sperrungen:</h4>
                        <div class="space-y-1 text-sm">
    `;
    
    selectedBlocks.forEach(block => {
        const data = block.data;
        const seriesInfo = data.series_id ? ' (Serie)' : '';
        html += `
            <div class="flex items-center justify-between py-1 border-b border-gray-100">
                <span>Platz ${data.court_number} - ${data.date} ${data.start_time}-${data.end_time}${seriesInfo}</span>
                <span class="text-gray-500">${data.reason_name}</span>
            </div>
        `;
    });
    
    html += `
                        </div>
                    </div>
                    
                    <div class="bg-yellow-50 p-3 rounded">
                        <p class="text-yellow-800 text-sm">
                            <strong>Hinweis:</strong> Diese Aktion kann nicht rückgängig gemacht werden. 
                            Betroffene Buchungen werden automatisch storniert und die Mitglieder benachrichtigt.
                        </p>
                    </div>
                    
                    <div class="flex gap-2">
                        <button onclick="confirmBulkDelete()" class="bg-red-600 text-white py-2 px-6 rounded hover:bg-red-700">
                            ${selectedBlocks.length} Sperrung(en) löschen
                        </button>
                        <button onclick="closeBulkDeleteModal()" class="bg-gray-600 text-white py-2 px-6 rounded hover:bg-gray-700">
                            Abbrechen
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', html);
}

// Close bulk delete modal
function closeBulkDeleteModal() {
    const modal = document.getElementById('bulk-delete-modal');
    if (modal) {
        modal.remove();
    }
}

// Confirm bulk delete
async function confirmBulkDelete() {
    const blockIds = selectedBlocks.map(b => b.id);
    
    try {
        const response = await fetch('/admin/blocks/bulk-delete', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ block_ids: blockIds })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showToast(data.message);
            closeBulkDeleteModal();
            applyFilters(); // Refresh the list
            selectedBlocks = [];
        } else {
            showToast(data.error || 'Fehler beim Löschen', 'error');
        }
    } catch (error) {
        showToast('Fehler beim Löschen der Sperrungen', 'error');
    }
}

// Bulk export functionality
function bulkExportSelected() {
    if (selectedBlocks.length === 0) {
        showToast('Keine Sperrungen ausgewählt', 'error');
        return;
    }
    
    // Create CSV content
    const csvContent = createCSVFromBlocks(selectedBlocks.map(b => b.data));
    
    // Download CSV file
    downloadCSV(csvContent, `sperrungen_export_${new Date().toISOString().split('T')[0]}.csv`);
    
    showToast(`${selectedBlocks.length} Sperrung(en) exportiert`);
}

// Create CSV from blocks
function createCSVFromBlocks(blocks) {
    const headers = ['Datum', 'Platz', 'Von', 'Bis', 'Grund', 'Zusätzlicher Grund', 'Serie', 'Erstellt von', 'Erstellt am'];
    const rows = blocks.map(block => [
        block.date,
        `Platz ${block.court_number}`,
        block.start_time,
        block.end_time,
        block.reason_name,
        block.sub_reason || '',
        block.series_id ? `Serie ${block.series_id}` : '',
        block.created_by,
        new Date(block.created_at).toLocaleDateString('de-DE')
    ]);
    
    const csvContent = [headers, ...rows]
        .map(row => row.map(field => `"${field}"`).join(','))
        .join('\n');
    
    return csvContent;
}

// Download CSV file
function downloadCSV(content, filename) {
    const blob = new Blob([content], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    
    if (link.download !== undefined) {
        const url = URL.createObjectURL(blob);
        link.setAttribute('href', url);
        link.setAttribute('download', filename);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
}

// Duplicate block
function duplicateBlock(blockId) {
    const blockData = selectedBlocks.find(b => b.id === blockId)?.data || 
                     document.querySelector(`input[value="${blockId}"]`)?.dataset.block;
    
    if (!blockData) {
        showToast('Block-Daten nicht gefunden', 'error');
        return;
    }
    
    const block = typeof blockData === 'string' ? JSON.parse(blockData) : blockData;
    
    // Pre-fill form with block data
    document.getElementById('block-court').value = block.court_id;
    document.getElementById('block-date').value = block.date;
    document.getElementById('block-start').value = block.start_time;
    document.getElementById('block-end').value = block.end_time;
    document.getElementById('block-reason').value = block.reason_id;
    document.getElementById('block-sub-reason').value = block.sub_reason || '';
    
    // Switch to blocks tab and scroll to form
    showTab('blocks');
    document.getElementById('block-form').scrollIntoView({ behavior: 'smooth' });
    
    showToast('Block-Daten in Formular geladen', 'info');
}

// Show bulk edit modal
function showBulkEditModal() {
    if (selectedBlocks.length === 0) {
        showToast('Keine Sperrungen ausgewählt', 'error');
        return;
    }
    
    let html = `
        <div id="bulk-edit-modal" class="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
            <div class="bg-white rounded-lg p-6 max-w-2xl w-full mx-4">
                <div class="flex items-center justify-between mb-4">
                    <h3 class="text-lg font-semibold">Massenbearbeitung</h3>
                    <button onclick="closeBulkEditModal()" class="text-gray-500 hover:text-gray-700">
                        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                        </svg>
                    </button>
                </div>
                
                <div class="space-y-4">
                    <div class="bg-blue-50 p-3 rounded">
                        <p class="text-blue-800 text-sm">
                            ${selectedBlocks.length} Sperrung(en) ausgewählt. Nur ausgefüllte Felder werden geändert.
                        </p>
                    </div>
                    
                    <form id="bulk-edit-form">
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                                <label class="block text-gray-700 font-semibold mb-2">
                                    <input type="checkbox" id="change-reason" class="mr-2"> Grund ändern
                                </label>
                                <select id="bulk-edit-reason" class="w-full border border-gray-300 rounded px-3 py-2" disabled>
                                    <!-- Will be populated by JavaScript -->
                                </select>
                            </div>
                            <div>
                                <label class="block text-gray-700 font-semibold mb-2">
                                    <input type="checkbox" id="change-sub-reason" class="mr-2"> Zusätzlichen Grund ändern
                                </label>
                                <input type="text" id="bulk-edit-sub-reason" class="w-full border border-gray-300 rounded px-3 py-2" disabled>
                            </div>
                            <div>
                                <label class="block text-gray-700 font-semibold mb-2">
                                    <input type="checkbox" id="change-time" class="mr-2"> Uhrzeit ändern
                                </label>
                                <div class="flex gap-2">
                                    <input type="time" id="bulk-edit-start-time" class="flex-1 border border-gray-300 rounded px-3 py-2" disabled>
                                    <input type="time" id="bulk-edit-end-time" class="flex-1 border border-gray-300 rounded px-3 py-2" disabled>
                                </div>
                            </div>
                            <div>
                                <label class="block text-gray-700 font-semibold mb-2">
                                    <input type="checkbox" id="change-date" class="mr-2"> Datum verschieben
                                </label>
                                <input type="number" id="bulk-edit-date-offset" class="w-full border border-gray-300 rounded px-3 py-2" placeholder="Tage (+ oder -)" disabled>
                            </div>
                        </div>
                        
                        <div class="mt-6 flex gap-2">
                            <button type="submit" class="bg-green-600 text-white py-2 px-6 rounded hover:bg-green-700">
                                Änderungen anwenden
                            </button>
                            <button type="button" onclick="closeBulkEditModal()" class="bg-gray-600 text-white py-2 px-6 rounded hover:bg-gray-700">
                                Abbrechen
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', html);
    
    // Populate reason select
    const reasonSelect = document.getElementById('bulk-edit-reason');
    blockReasons.forEach(reason => {
        const option = document.createElement('option');
        option.value = reason.id;
        option.textContent = reason.name;
        reasonSelect.appendChild(option);
    });
    
    // Setup checkbox handlers
    setupBulkEditCheckboxes();
    
    // Setup form submission
    document.getElementById('bulk-edit-form').addEventListener('submit', handleBulkEditSubmit);
}

// Setup bulk edit checkboxes
function setupBulkEditCheckboxes() {
    const checkboxes = [
        { checkbox: 'change-reason', field: 'bulk-edit-reason' },
        { checkbox: 'change-sub-reason', field: 'bulk-edit-sub-reason' },
        { checkbox: 'change-time', fields: ['bulk-edit-start-time', 'bulk-edit-end-time'] },
        { checkbox: 'change-date', field: 'bulk-edit-date-offset' }
    ];
    
    checkboxes.forEach(({ checkbox, field, fields }) => {
        const cb = document.getElementById(checkbox);
        const targetFields = fields || [field];
        
        cb.addEventListener('change', function() {
            targetFields.forEach(fieldId => {
                const fieldElement = document.getElementById(fieldId);
                if (fieldElement) {
                    fieldElement.disabled = !this.checked;
                }
            });
        });
    });
}

// Close bulk edit modal
function closeBulkEditModal() {
    const modal = document.getElementById('bulk-edit-modal');
    if (modal) {
        modal.remove();
    }
}

// Handle bulk edit form submission
async function handleBulkEditSubmit(e) {
    e.preventDefault();
    
    const changes = {};
    
    if (document.getElementById('change-reason').checked) {
        changes.reason_id = parseInt(document.getElementById('bulk-edit-reason').value);
    }
    
    if (document.getElementById('change-sub-reason').checked) {
        changes.sub_reason = document.getElementById('bulk-edit-sub-reason').value;
    }
    
    if (document.getElementById('change-time').checked) {
        changes.start_time = document.getElementById('bulk-edit-start-time').value;
        changes.end_time = document.getElementById('bulk-edit-end-time').value;
    }
    
    if (document.getElementById('change-date').checked) {
        changes.date_offset = parseInt(document.getElementById('bulk-edit-date-offset').value);
    }
    
    if (Object.keys(changes).length === 0) {
        showToast('Keine Änderungen ausgewählt', 'error');
        return;
    }
    
    const blockIds = selectedBlocks.map(b => b.id);
    
    try {
        const response = await fetch('/admin/blocks/bulk-edit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ block_ids: blockIds, changes: changes })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showToast(data.message);
            closeBulkEditModal();
            applyFilters(); // Refresh the list
            selectedBlocks = [];
        } else {
            showToast(data.error || 'Fehler bei der Massenbearbeitung', 'error');
        }
    } catch (error) {
        showToast('Fehler bei der Massenbearbeitung', 'error');
    }
}

// Delete single block
async function deleteBlock(blockId) {
    if (!confirm('Möchten Sie diese Sperrung wirklich löschen?')) {
        return;
    }
    
    try {
        const response = await fetch(`/admin/blocks/${blockId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showToast(data.message);
            applyFilters(); // Refresh the list
        } else {
            showToast(data.error || 'Fehler beim Löschen', 'error');
        }
    } catch (error) {
        showToast('Fehler beim Löschen der Sperrung', 'error');
    }
}

// Load series list
async function loadSeriesList() {
    try {
        const response = await fetch('/admin/blocks/series');
        const data = await response.json();
        
        if (response.ok) {
            displaySeriesList(data.series);
        } else {
            document.getElementById('series-list').innerHTML = '<p class="text-gray-600">Fehler beim Laden der Serien.</p>';
        }
    } catch (error) {
        document.getElementById('series-list').innerHTML = '<p class="text-gray-600">Fehler beim Laden der Serien.</p>';
    }
}

// Display series list
function displaySeriesList(series) {
    const container = document.getElementById('series-list');
    
    if (series.length === 0) {
        container.innerHTML = '<p class="text-gray-600">Keine wiederkehrenden Serien vorhanden.</p>';
        return;
    }
    
    let html = '<div class="space-y-4">';
    
    series.forEach(serie => {
        const recurrenceText = getRecurrenceText(serie.recurrence_pattern, serie.recurrence_days);
        const statusBadge = serie.is_active ? 
            '<span class="bg-green-100 text-green-800 text-xs px-2 py-1 rounded">Aktiv</span>' :
            '<span class="bg-gray-100 text-gray-800 text-xs px-2 py-1 rounded">Inaktiv</span>';
        
        html += `
            <div class="border border-gray-200 rounded p-4 bg-gray-50">
                <div class="flex items-start justify-between">
                    <div class="flex-1">
                        <div class="flex items-center gap-2 mb-2">
                            <h4 class="font-semibold text-lg">${serie.name}</h4>
                            ${statusBadge}
                        </div>
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-gray-600">
                            <div>
                                <p><strong>Zeitraum:</strong> ${formatGermanDate(serie.start_date)} - ${formatGermanDate(serie.end_date)}</p>
                                <p><strong>Uhrzeit:</strong> ${serie.start_time} - ${serie.end_time}</p>
                                <p><strong>Wiederholung:</strong> ${recurrenceText}</p>
                            </div>
                            <div>
                                <p><strong>Plätze:</strong> ${serie.court_selection.join(', ')}</p>
                                <p><strong>Grund:</strong> ${serie.reason_name}${serie.sub_reason ? ' - ' + serie.sub_reason : ''}</p>
                                <p><strong>Instanzen:</strong> ${serie.total_instances} (${serie.active_instances} aktiv)</p>
                            </div>
                        </div>
                        <p class="text-xs text-gray-500 mt-2">Erstellt von ${serie.created_by} am ${new Date(serie.created_at).toLocaleDateString('de-DE')}</p>
                    </div>
                    <div class="flex flex-col gap-2 ml-4">
                        <button onclick="editSeriesModal(${serie.id})" 
                                class="bg-purple-600 text-white px-3 py-1 rounded text-sm hover:bg-purple-700">
                            Serie bearbeiten
                        </button>
                        <button onclick="viewSeriesInstances(${serie.id})" 
                                class="bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700">
                            Instanzen anzeigen
                        </button>
                        <button onclick="deleteSeriesModal(${serie.id})" 
                                class="bg-red-600 text-white px-3 py-1 rounded text-sm hover:bg-red-700">
                            Serie löschen
                        </button>
                    </div>
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    container.innerHTML = html;
}

// Get recurrence text in German
function getRecurrenceText(pattern, days) {
    switch (pattern) {
        case 'daily':
            return 'Täglich';
        case 'weekly':
            if (days && days.length > 0) {
                const dayNames = ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag'];
                const selectedDays = days.map(day => dayNames[day]).join(', ');
                return `Wöchentlich (${selectedDays})`;
            }
            return 'Wöchentlich';
        case 'monthly':
            return 'Monatlich';
        default:
            return pattern;
    }
}

// Edit series modal
function editSeriesModal(seriesId) {
    // Create modal for editing series
    let html = `
        <div id="edit-series-modal" class="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
            <div class="bg-white rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto">
                <div class="flex items-center justify-between mb-4">
                    <h3 class="text-lg font-semibold">Serie bearbeiten</h3>
                    <button onclick="closeEditSeriesModal()" class="text-gray-500 hover:text-gray-700">
                        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                        </svg>
                    </button>
                </div>
                
                <div class="space-y-4">
                    <div class="bg-blue-50 p-4 rounded-lg">
                        <h4 class="font-semibold mb-2">Bearbeitungsoptionen:</h4>
                        <div class="space-y-2">
                            <label class="flex items-center">
                                <input type="radio" name="edit-option" value="entire" class="mr-2" checked>
                                Gesamte Serie bearbeiten (alle Instanzen)
                            </label>
                            <label class="flex items-center">
                                <input type="radio" name="edit-option" value="future" class="mr-2">
                                Nur zukünftige Instanzen bearbeiten
                            </label>
                        </div>
                    </div>
                    
                    <div id="future-date-container" class="hidden">
                        <label class="block text-gray-700 font-semibold mb-2">Ab Datum:</label>
                        <input type="date" id="edit-from-date" class="w-full border border-gray-300 rounded px-3 py-2">
                    </div>
                    
                    <form id="edit-series-form">
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                                <label class="block text-gray-700 font-semibold mb-2">Von (Uhrzeit)</label>
                                <input type="time" id="edit-series-start-time" class="w-full border border-gray-300 rounded px-3 py-2">
                            </div>
                            <div>
                                <label class="block text-gray-700 font-semibold mb-2">Bis (Uhrzeit)</label>
                                <input type="time" id="edit-series-end-time" class="w-full border border-gray-300 rounded px-3 py-2">
                            </div>
                            <div>
                                <label class="block text-gray-700 font-semibold mb-2">Grund</label>
                                <select id="edit-series-reason" class="w-full border border-gray-300 rounded px-3 py-2">
                                    <!-- Will be populated by JavaScript -->
                                </select>
                            </div>
                            <div>
                                <label class="block text-gray-700 font-semibold mb-2">Zusätzlicher Grund</label>
                                <input type="text" id="edit-series-sub-reason" class="w-full border border-gray-300 rounded px-3 py-2">
                            </div>
                        </div>
                        
                        <div class="mt-6 flex gap-2">
                            <button type="submit" class="bg-purple-600 text-white py-2 px-6 rounded hover:bg-purple-700">
                                Änderungen speichern
                            </button>
                            <button type="button" onclick="closeEditSeriesModal()" class="bg-gray-600 text-white py-2 px-6 rounded hover:bg-gray-700">
                                Abbrechen
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', html);
    
    // Populate reason select
    const reasonSelect = document.getElementById('edit-series-reason');
    blockReasons.forEach(reason => {
        const option = document.createElement('option');
        option.value = reason.id;
        option.textContent = reason.name;
        reasonSelect.appendChild(option);
    });
    
    // Setup event listeners
    document.querySelectorAll('input[name="edit-option"]').forEach(radio => {
        radio.addEventListener('change', function() {
            const futureContainer = document.getElementById('future-date-container');
            if (this.value === 'future') {
                futureContainer.classList.remove('hidden');
                document.getElementById('edit-from-date').value = new Date().toISOString().split('T')[0];
            } else {
                futureContainer.classList.add('hidden');
            }
        });
    });
    
    document.getElementById('edit-series-form').addEventListener('submit', function(e) {
        e.preventDefault();
        handleEditSeriesSubmit(seriesId);
    });
}

// Close edit series modal
function closeEditSeriesModal() {
    const modal = document.getElementById('edit-series-modal');
    if (modal) {
        modal.remove();
    }
}

// Handle edit series form submission
async function handleEditSeriesSubmit(seriesId) {
    const editOption = document.querySelector('input[name="edit-option"]:checked').value;
    const fromDate = document.getElementById('edit-from-date').value;
    
    const updateData = {
        start_time: document.getElementById('edit-series-start-time').value,
        end_time: document.getElementById('edit-series-end-time').value,
        reason_id: parseInt(document.getElementById('edit-series-reason').value),
        sub_reason: document.getElementById('edit-series-sub-reason').value
    };
    
    let url = `/admin/blocks/series/${seriesId}`;
    if (editOption === 'future') {
        url += `/future?from_date=${fromDate}`;
        updateData.from_date = fromDate;
    }
    
    try {
        const response = await fetch(url, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(updateData)
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showToast(data.message);
            closeEditSeriesModal();
            loadSeriesList(); // Refresh the list
        } else {
            showToast(data.error || 'Fehler beim Bearbeiten der Serie', 'error');
        }
    } catch (error) {
        showToast('Fehler beim Bearbeiten der Serie', 'error');
    }
}

// View series instances
function viewSeriesInstances(seriesId) {
    // This would show all instances of the series
    showToast(`Serie ${seriesId} Instanzen anzeigen - Funktion wird implementiert`, 'info');
}

// Delete series modal
function deleteSeriesModal(seriesId) {
    let html = `
        <div id="delete-series-modal" class="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
            <div class="bg-white rounded-lg p-6 max-w-md w-full mx-4">
                <div class="flex items-center justify-between mb-4">
                    <h3 class="text-lg font-semibold text-red-600">Serie löschen</h3>
                    <button onclick="closeDeleteSeriesModal()" class="text-gray-500 hover:text-gray-700">
                        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                        </svg>
                    </button>
                </div>
                
                <div class="space-y-4">
                    <p class="text-gray-600">Wie möchten Sie die Serie löschen?</p>
                    
                    <div class="space-y-2">
                        <label class="flex items-center">
                            <input type="radio" name="delete-option" value="all" class="mr-2" checked>
                            Gesamte Serie löschen (alle Instanzen)
                        </label>
                        <label class="flex items-center">
                            <input type="radio" name="delete-option" value="future" class="mr-2">
                            Nur zukünftige Instanzen löschen
                        </label>
                        <label class="flex items-center">
                            <input type="radio" name="delete-option" value="single" class="mr-2">
                            Nur eine bestimmte Instanz löschen
                        </label>
                    </div>
                    
                    <div id="delete-date-container" class="hidden">
                        <label class="block text-gray-700 font-semibold mb-2">Ab/An Datum:</label>
                        <input type="date" id="delete-from-date" class="w-full border border-gray-300 rounded px-3 py-2">
                    </div>
                    
                    <div class="bg-red-50 p-3 rounded">
                        <p class="text-red-800 text-sm">
                            <strong>Warnung:</strong> Diese Aktion kann nicht rückgängig gemacht werden.
                        </p>
                    </div>
                    
                    <div class="flex gap-2">
                        <button onclick="confirmDeleteSeries(${seriesId})" class="bg-red-600 text-white py-2 px-4 rounded hover:bg-red-700">
                            Löschen bestätigen
                        </button>
                        <button onclick="closeDeleteSeriesModal()" class="bg-gray-600 text-white py-2 px-4 rounded hover:bg-gray-700">
                            Abbrechen
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', html);
    
    // Setup event listeners
    document.querySelectorAll('input[name="delete-option"]').forEach(radio => {
        radio.addEventListener('change', function() {
            const dateContainer = document.getElementById('delete-date-container');
            if (this.value === 'future' || this.value === 'single') {
                dateContainer.classList.remove('hidden');
                document.getElementById('delete-from-date').value = new Date().toISOString().split('T')[0];
            } else {
                dateContainer.classList.add('hidden');
            }
        });
    });
}

// Close delete series modal
function closeDeleteSeriesModal() {
    const modal = document.getElementById('delete-series-modal');
    if (modal) {
        modal.remove();
    }
}

// Confirm delete series
async function confirmDeleteSeries(seriesId) {
    const deleteOption = document.querySelector('input[name="delete-option"]:checked').value;
    const fromDate = document.getElementById('delete-from-date').value;
    
    const deleteData = { option: deleteOption };
    if (deleteOption === 'future' || deleteOption === 'single') {
        deleteData.from_date = fromDate;
    }
    
    try {
        const response = await fetch(`/admin/blocks/series/${seriesId}`, {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(deleteData)
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showToast(data.message);
            closeDeleteSeriesModal();
            loadSeriesList(); // Refresh the list
        } else {
            showToast(data.error || 'Fehler beim Löschen der Serie', 'error');
        }
    } catch (error) {
        showToast('Fehler beim Löschen der Serie', 'error');
    }
}

// Load template list
async function loadTemplateList() {
    try {
        const response = await fetch('/admin/block-templates');
        const data = await response.json();
        
        if (response.ok) {
            displayTemplateList(data.templates);
        } else {
            showToast(data.error || 'Fehler beim Laden der Vorlagen', 'error');
        }
    } catch (error) {
        showToast('Fehler beim Laden der Vorlagen', 'error');
    }
}

// Display template list
function displayTemplateList(templates) {
    const container = document.getElementById('template-list');
    
    if (templates.length === 0) {
        container.innerHTML = '<p class="text-gray-600">Keine Vorlagen vorhanden.</p>';
        return;
    }
    
    let html = '<div class="space-y-4">';
    
    templates.forEach(template => {
        const courtList = template.court_selection.join(', ');
        const recurrenceText = template.recurrence_pattern ? 
            ` | ${getRecurrenceText(template.recurrence_pattern, template.recurrence_days)}` : '';
        
        html += `
            <div class="border border-gray-200 rounded p-4 bg-gray-50">
                <div class="flex items-center justify-between">
                    <div class="flex-1">
                        <h4 class="font-semibold text-lg mb-2">${template.name}</h4>
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-2 text-sm text-gray-600">
                            <div>
                                <p><strong>Plätze:</strong> ${courtList}</p>
                                <p><strong>Uhrzeit:</strong> ${template.start_time}-${template.end_time}${recurrenceText}</p>
                            </div>
                            <div>
                                <p><strong>Grund:</strong> ${template.reason_name}${template.sub_reason ? ' - ' + template.sub_reason : ''}</p>
                                <p class="text-xs text-gray-500">Erstellt von ${template.created_by}</p>
                            </div>
                        </div>
                    </div>
                    <div class="flex gap-2 ml-4">
                        <button onclick="applyTemplate(${template.id})" 
                                class="bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700"
                                title="Vorlage anwenden">
                            ${GERMAN_TEXT.APPLY_TEMPLATE}
                        </button>
                        <button onclick="editTemplate(${template.id})" 
                                class="bg-green-600 text-white px-3 py-1 rounded text-sm hover:bg-green-700"
                                title="Vorlage bearbeiten">
                            ✏️
                        </button>
                        <button onclick="duplicateTemplate(${template.id})" 
                                class="bg-yellow-600 text-white px-3 py-1 rounded text-sm hover:bg-yellow-700"
                                title="Vorlage duplizieren">
                            📋
                        </button>
                        <button onclick="deleteTemplate(${template.id})" 
                                class="bg-red-600 text-white px-3 py-1 rounded text-sm hover:bg-red-700"
                                title="Vorlage löschen">
                            🗑️
                        </button>
                    </div>
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    container.innerHTML = html;
}

// Duplicate template
function duplicateTemplate(templateId) {
    const template = blockTemplates.find(t => t.id === templateId);
    if (!template) return;
    
    // Pre-fill form with template data but with new name
    document.getElementById('template-name').value = template.name + ' (Kopie)';
    document.getElementById('template-start-time').value = template.start_time;
    document.getElementById('template-end-time').value = template.end_time;
    document.getElementById('template-reason').value = template.reason_id;
    document.getElementById('template-sub-reason').value = template.sub_reason || '';
    
    // Select courts
    document.querySelectorAll('input[name="template-courts"]').forEach(cb => {
        cb.checked = template.court_selection.includes(parseInt(cb.value));
    });
    
    // Scroll to form
    document.getElementById('template-form').scrollIntoView({ behavior: 'smooth' });
    
    showToast(`Vorlage "${template.name}" dupliziert`, 'info');
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
                            ${reason.sub_reason_templates && reason.sub_reason_templates.length > 0 ? 
                                `<p class="text-blue-600">📋 ${reason.sub_reason_templates.length} Untergrund-Vorlage(n)</p>` : 
                                '<p class="text-gray-500">Keine Untergrund-Vorlagen</p>'
                            }
                        </div>
                    </div>
                    <div class="flex flex-col gap-2 ml-4">
                        <button onclick="editReasonModal(${reason.id})" 
                                class="bg-orange-600 text-white px-3 py-1 rounded text-sm hover:bg-orange-700" 
                                title="Grund bearbeiten">
                            ✏️ Bearbeiten
                        </button>
                        <button onclick="manageSubReasonTemplates(${reason.id}, '${reason.name}')" 
                                class="bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700" 
                                title="Untergrund-Vorlagen verwalten">
                            📋 Vorlagen
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

// Apply template
async function applyTemplate(templateId) {
    const today = new Date().toISOString().split('T')[0];
    
    try {
        const response = await fetch(`/admin/block-templates/${templateId}/apply`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ start_date: today })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showToast(data.message);
            // Pre-fill form with template data
            applyTemplateToForm(data.form_data);
            // Switch to blocks tab
            showTab('blocks');
        } else {
            showToast(data.error || 'Fehler beim Anwenden der Vorlage', 'error');
        }
    } catch (error) {
        showToast('Fehler beim Anwenden der Vorlage', 'error');
    }
}

// Apply template data to form
function applyTemplateToForm(formData) {
    if (!formData) return;
    
    // Fill single block form
    if (formData.court_selection && formData.court_selection.length === 1) {
        document.getElementById('block-court').value = formData.court_selection[0];
    }
    
    if (formData.start_time) {
        document.getElementById('block-start').value = formData.start_time;
    }
    
    if (formData.end_time) {
        document.getElementById('block-end').value = formData.end_time;
    }
    
    if (formData.reason_id) {
        document.getElementById('block-reason').value = formData.reason_id;
    }
    
    if (formData.sub_reason) {
        document.getElementById('block-sub-reason').value = formData.sub_reason;
    }
    
    // Fill multi-court form if multiple courts
    if (formData.court_selection && formData.court_selection.length > 1) {
        // Clear existing selections
        document.querySelectorAll('input[name="multi-courts"]').forEach(cb => cb.checked = false);
        
        // Select courts from template
        formData.court_selection.forEach(courtId => {
            const checkbox = document.querySelector(`input[name="multi-courts"][value="${courtId}"]`);
            if (checkbox) checkbox.checked = true;
        });
        
        // Fill other multi-court fields
        if (formData.start_time) {
            document.getElementById('multi-start').value = formData.start_time;
        }
        
        if (formData.end_time) {
            document.getElementById('multi-end').value = formData.end_time;
        }
        
        if (formData.reason_id) {
            document.getElementById('multi-reason').value = formData.reason_id;
        }
        
        if (formData.sub_reason) {
            document.getElementById('multi-sub-reason').value = formData.sub_reason;
        }
    }
}

// Enhanced template creation with preview
function createTemplateWithPreview() {
    const templateName = document.getElementById('template-name').value.trim();
    if (!templateName) {
        showToast('Bitte einen Vorlagennamen eingeben', 'error');
        return;
    }
    
    const selectedCourts = Array.from(document.querySelectorAll('input[name="template-courts"]:checked'))
        .map(cb => parseInt(cb.value));
    
    if (selectedCourts.length === 0) {
        showToast('Bitte mindestens einen Platz auswählen', 'error');
        return;
    }
    
    const templateData = {
        name: templateName,
        court_selection: selectedCourts,
        start_time: document.getElementById('template-start-time').value,
        end_time: document.getElementById('template-end-time').value,
        reason_id: parseInt(document.getElementById('template-reason').value),
        sub_reason: document.getElementById('template-sub-reason').value
    };
    
    // Show preview modal
    showTemplatePreview(templateData);
}

// Show template preview modal
function showTemplatePreview(templateData) {
    const reasonName = blockReasons.find(r => r.id === templateData.reason_id)?.name || 'Unbekannt';
    
    let html = `
        <div id="template-preview-modal" class="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
            <div class="bg-white rounded-lg p-6 max-w-2xl w-full mx-4">
                <div class="flex items-center justify-between mb-4">
                    <h3 class="text-lg font-semibold">Vorlagen-Vorschau</h3>
                    <button onclick="closeTemplatePreview()" class="text-gray-500 hover:text-gray-700">
                        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                        </svg>
                    </button>
                </div>
                
                <div class="space-y-4">
                    <div class="bg-blue-50 p-4 rounded-lg">
                        <h4 class="font-semibold mb-2">${templateData.name}</h4>
                        <div class="grid grid-cols-2 gap-4 text-sm">
                            <div>
                                <p><strong>Plätze:</strong> ${templateData.court_selection.join(', ')}</p>
                                <p><strong>Uhrzeit:</strong> ${templateData.start_time} - ${templateData.end_time}</p>
                            </div>
                            <div>
                                <p><strong>Grund:</strong> ${reasonName}</p>
                                ${templateData.sub_reason ? `<p><strong>Zusätzlicher Grund:</strong> ${templateData.sub_reason}</p>` : ''}
                            </div>
                        </div>
                    </div>
                    
                    <div class="bg-yellow-50 p-3 rounded">
                        <p class="text-yellow-800 text-sm">
                            Diese Vorlage kann später verwendet werden, um schnell Sperrungen mit diesen Einstellungen zu erstellen.
                        </p>
                    </div>
                    
                    <div class="flex gap-2">
                        <button onclick="confirmCreateTemplate()" class="bg-blue-600 text-white py-2 px-6 rounded hover:bg-blue-700">
                            Vorlage erstellen
                        </button>
                        <button onclick="closeTemplatePreview()" class="bg-gray-600 text-white py-2 px-6 rounded hover:bg-gray-700">
                            Abbrechen
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', html);
    
    // Store template data for confirmation
    window.pendingTemplateData = templateData;
}

// Close template preview
function closeTemplatePreview() {
    const modal = document.getElementById('template-preview-modal');
    if (modal) {
        modal.remove();
    }
    window.pendingTemplateData = null;
}

// Confirm create template
async function confirmCreateTemplate() {
    if (!window.pendingTemplateData) return;
    
    try {
        const response = await fetch('/admin/block-templates', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(window.pendingTemplateData)
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showToast(data.message);
            closeTemplatePreview();
            document.getElementById('template-form').reset();
            loadTemplateList(); // Refresh the template list
        } else {
            showToast(data.error || 'Fehler beim Erstellen der Vorlage', 'error');
        }
    } catch (error) {
        showToast('Fehler beim Erstellen der Vorlage', 'error');
    }
}

// Edit template
function editTemplate(templateId) {
    const template = blockTemplates.find(t => t.id === templateId);
    if (!template) return;
    
    // Pre-fill form with template data
    document.getElementById('template-name').value = template.name;
    document.getElementById('template-start-time').value = template.start_time;
    document.getElementById('template-end-time').value = template.end_time;
    document.getElementById('template-reason').value = template.reason_id;
    document.getElementById('template-sub-reason').value = template.sub_reason || '';
    
    // Select courts
    document.querySelectorAll('input[name="template-courts"]').forEach(cb => {
        cb.checked = template.court_selection.includes(parseInt(cb.value));
    });
    
    // Scroll to form
    document.getElementById('template-form').scrollIntoView({ behavior: 'smooth' });
    
    showToast(`Vorlage "${template.name}" in Formular geladen`, 'info');
}

// Delete template
async function deleteTemplate(templateId) {
    if (!confirm('Möchten Sie diese Vorlage wirklich löschen?')) {
        return;
    }
    
    try {
        const response = await fetch(`/admin/block-templates/${templateId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showToast(data.message);
            loadTemplateList(); // Refresh the list
        } else {
            showToast(data.error || 'Fehler beim Löschen der Vorlage', 'error');
        }
    } catch (error) {
        showToast('Fehler beim Löschen der Vorlage', 'error');
    }
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
                        <button type="submit" class="bg-orange-600 text-white py-2 px-6 rounded hover:bg-orange-700">
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

// Sub-reason template management
function manageSubReasonTemplates(reasonId, reasonName) {
    let html = `
        <div id="sub-reason-modal" class="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
            <div class="bg-white rounded-lg p-6 max-w-4xl w-full mx-4 max-h-[80vh] overflow-y-auto">
                <div class="flex items-center justify-between mb-4">
                    <h3 class="text-lg font-semibold">Untergrund-Vorlagen für "${reasonName}"</h3>
                    <button onclick="closeSubReasonModal()" class="text-gray-500 hover:text-gray-700">
                        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                        </svg>
                    </button>
                </div>
                
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <!-- Create new template -->
                    <div class="space-y-4">
                        <h4 class="font-semibold text-blue-600">Neue Vorlage erstellen</h4>
                        <form id="sub-reason-template-form" class="space-y-3">
                            <div>
                                <label class="block text-gray-700 font-medium mb-1">Vorlagenname</label>
                                <input type="text" id="sub-reason-template-name" 
                                       class="w-full border border-gray-300 rounded px-3 py-2" 
                                       placeholder="z.B. Platzpflege, Turniervorbereitung" required>
                            </div>
                            <button type="submit" class="bg-blue-600 text-white py-2 px-4 rounded hover:bg-blue-700">
                                Vorlage hinzufügen
                            </button>
                        </form>
                        
                        <div class="bg-blue-50 p-3 rounded text-sm text-blue-700">
                            <p><strong>Hinweis:</strong> Untergrund-Vorlagen helfen bei der schnellen Auswahl häufig verwendeter Zusatzgründe.</p>
                        </div>
                    </div>
                    
                    <!-- Existing templates -->
                    <div class="space-y-4">
                        <h4 class="font-semibold text-green-600">Vorhandene Vorlagen</h4>
                        <div id="sub-reason-templates-list">
                            <div class="text-center py-4">
                                <div class="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-green-600"></div>
                                <p class="mt-2 text-gray-600">Lade Vorlagen...</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', html);
    
    // Load existing templates
    loadSubReasonTemplates(reasonId);
    
    // Setup form submission
    document.getElementById('sub-reason-template-form').addEventListener('submit', function(e) {
        e.preventDefault();
        createSubReasonTemplate(reasonId);
    });
}

// Close sub-reason modal
function closeSubReasonModal() {
    const modal = document.getElementById('sub-reason-modal');
    if (modal) {
        modal.remove();
    }
}

// Load sub-reason templates
async function loadSubReasonTemplates(reasonId) {
    try {
        const response = await fetch(`/admin/block-reasons/${reasonId}/sub-reason-templates`);
        const data = await response.json();
        
        if (response.ok) {
            displaySubReasonTemplates(data.templates);
        } else {
            document.getElementById('sub-reason-templates-list').innerHTML = 
                '<p class="text-red-600">Fehler beim Laden der Vorlagen</p>';
        }
    } catch (error) {
        document.getElementById('sub-reason-templates-list').innerHTML = 
            '<p class="text-red-600">Fehler beim Laden der Vorlagen</p>';
    }
}

// Display sub-reason templates
function displaySubReasonTemplates(templates) {
    const container = document.getElementById('sub-reason-templates-list');
    
    if (templates.length === 0) {
        container.innerHTML = '<p class="text-gray-600">Keine Vorlagen vorhanden.</p>';
        return;
    }
    
    let html = '<div class="space-y-2">';
    
    templates.forEach(template => {
        html += `
            <div class="flex items-center justify-between p-3 border border-gray-200 rounded bg-gray-50">
                <div>
                    <p class="font-medium">${template.template_name}</p>
                    <p class="text-sm text-gray-500">Erstellt am ${new Date(template.created_at).toLocaleDateString('de-DE')}</p>
                </div>
                <button onclick="deleteSubReasonTemplate(${template.id})" 
                        class="bg-red-600 text-white px-2 py-1 rounded text-sm hover:bg-red-700" 
                        title="Vorlage löschen">
                    🗑️
                </button>
            </div>
        `;
    });
    
    html += '</div>';
    container.innerHTML = html;
}

// Create sub-reason template
async function createSubReasonTemplate(reasonId) {
    const templateName = document.getElementById('sub-reason-template-name').value.trim();
    
    if (!templateName) {
        showToast('Bitte einen Vorlagennamen eingeben', 'error');
        return;
    }
    
    try {
        const response = await fetch(`/admin/block-reasons/${reasonId}/sub-reason-templates`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ template_name: templateName })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showToast(data.message);
            document.getElementById('sub-reason-template-name').value = '';
            loadSubReasonTemplates(reasonId); // Refresh the list
        } else {
            showToast(data.error || 'Fehler beim Erstellen der Vorlage', 'error');
        }
    } catch (error) {
        showToast('Fehler beim Erstellen der Vorlage', 'error');
    }
}

// Delete sub-reason template
async function deleteSubReasonTemplate(templateId) {
    if (!confirm('Möchten Sie diese Untergrund-Vorlage wirklich löschen?')) {
        return;
    }
    
    try {
        const response = await fetch(`/admin/sub-reason-templates/${templateId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showToast(data.message);
            // Find the reason ID to reload templates
            const modal = document.getElementById('sub-reason-modal');
            if (modal) {
                // Extract reason ID from the modal context or reload all templates
                location.reload(); // Simple approach - reload page
            }
        } else {
            showToast(data.error || 'Fehler beim Löschen der Vorlage', 'error');
        }
    } catch (error) {
        showToast('Fehler beim Löschen der Vorlage', 'error');
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
        const seriesInfo = block.series_id ? ` (Serie ${block.series_id}${block.is_modified ? ', modifiziert' : ''})` : '';
        
        html += `
            <div class="block-detail-item border rounded p-3" style="border-left: 4px solid ${color};">
                <div class="flex items-center justify-between">
                    <div>
                        <p class="font-semibold">Platz ${block.court_number} - ${block.start_time}-${block.end_time}</p>
                        <p class="text-gray-600">${block.reason_name}${block.sub_reason ? ' - ' + block.sub_reason : ''}${seriesInfo}</p>
                        <p class="text-sm text-gray-500">Erstellt von ${block.created_by}</p>
                    </div>
                    <div class="flex gap-2">
                        ${block.series_id ? `
                            <button onclick="editSeries(${block.series_id})" 
                                    class="bg-purple-600 text-white px-3 py-1 rounded text-sm hover:bg-purple-700"
                                    title="Serie bearbeiten">
                                Serie
                            </button>
                        ` : ''}
                        <button onclick="editBlock(${block.id})" 
                                class="bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700"
                                title="Bearbeiten">
                            ✏️
                        </button>
                        <button onclick="deleteBlock(${block.id})" 
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
    // This would open an edit modal for the specific block
    showToast(`Block ${blockId} bearbeiten - Funktion wird implementiert`, 'info');
    closeDayDetails();
}