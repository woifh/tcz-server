/**
 * Block Filtering System
 * Handles filtering and searching of blocks
 */

import { blocksAPI } from '../core/admin-api.js';
import { showToast, dataUtils, storageUtils } from '../core/admin-utils.js';
import { stateManager } from '../core/admin-state.js';
import { CONFIG } from '../core/admin-constants.js';
import { getToday, toBerlinDateString } from '../../../utils/date-utils.js';

export class BlockFilters {
    constructor() {
        this.setupEventListeners();
        this.loadSavedFilters();
    }

    setupEventListeners() {
        // Filter inputs
        const filterInputs = document.querySelectorAll('.filter-input');
        filterInputs.forEach((input) => {
            const debouncedHandler = dataUtils.debounce(() => {
                this.updateFilters();
            }, CONFIG.DEBOUNCE_DELAY);

            input.addEventListener('input', debouncedHandler);
            input.addEventListener('change', debouncedHandler);
        });

        // Clear filters button
        const clearFiltersBtn = document.getElementById('clear-filters-btn');
        if (clearFiltersBtn) {
            clearFiltersBtn.addEventListener('click', () => this.clearAllFilters());
        }

        // Save filters button
        const saveFiltersBtn = document.getElementById('save-filters-btn');
        if (saveFiltersBtn) {
            saveFiltersBtn.addEventListener('click', () => this.saveCurrentFilters());
        }

        // Date range presets
        const datePresets = document.querySelectorAll('.date-preset-btn');
        datePresets.forEach((btn) => {
            btn.addEventListener('click', (e) => {
                const preset = e.target.dataset.preset;
                this.applyDatePreset(preset);
            });
        });
    }

    updateFilters() {
        const filters = this.collectFilterValues();
        stateManager.setCurrentFilters(filters);

        // Update URL parameters
        this.updateUrlParams(filters);

        // Apply filters
        this.applyFilters(filters);

        // Update filter indicators
        this.updateFilterIndicators(filters);
    }

    collectFilterValues() {
        const filters = {};

        // Date range
        const startDate = document.getElementById('filter-start-date')?.value;
        const endDate = document.getElementById('filter-end-date')?.value;

        if (startDate) filters.date_range_start = startDate;
        if (endDate) filters.date_range_end = endDate;

        // Time range
        const startTime = document.getElementById('filter-start-time')?.value;
        const endTime = document.getElementById('filter-end-time')?.value;

        if (startTime) filters.start_time = startTime;
        if (endTime) filters.end_time = endTime;

        // Courts
        const selectedCourts = Array.from(
            document.querySelectorAll('input[name="filter-courts"]:checked')
        ).map((cb) => cb.value);
        if (selectedCourts.length > 0) {
            filters.courts = selectedCourts;
        }

        // Reasons
        const selectedReasons = Array.from(
            document.querySelectorAll('input[name="filter-reasons"]:checked')
        ).map((cb) => cb.value);
        if (selectedReasons.length > 0) {
            filters.reasons = selectedReasons;
        }

        // Search text
        const searchText = document.getElementById('filter-search')?.value;
        if (searchText && searchText.trim()) {
            filters.search = searchText.trim();
        }

        // Status filters
        const showPast = document.getElementById('filter-show-past')?.checked;
        const showFuture = document.getElementById('filter-show-future')?.checked;
        const showActive = document.getElementById('filter-show-active')?.checked;

        if (showPast !== undefined) filters.show_past = showPast;
        if (showFuture !== undefined) filters.show_future = showFuture;
        if (showActive !== undefined) filters.show_active = showActive;

        return filters;
    }

    async applyFilters(filters) {
        try {
            // Show loading indicator
            this.showLoadingIndicator(true);

            // Load filtered blocks
            const result = await blocksAPI.load(filters);

            if (result.success) {
                // Update the blocks display
                if (window.renderBlocksList) {
                    window.renderBlocksList(result.blocks);
                }

                // Update statistics
                this.updateFilterStatistics(result.blocks, filters);
            } else {
                showToast(result.error || 'Fehler beim Laden der gefilterten Sperrungen', 'error');
            }
        } catch (error) {
            console.error('Error applying filters:', error);
            showToast('Fehler beim Anwenden der Filter', 'error');
        } finally {
            this.showLoadingIndicator(false);
        }
    }

    updateFilterIndicators(filters) {
        const activeFiltersCount = Object.keys(filters).length;
        const filterIndicator = document.getElementById('active-filters-count');

        if (filterIndicator) {
            if (activeFiltersCount > 0) {
                filterIndicator.textContent = activeFiltersCount;
                filterIndicator.style.display = 'inline';
            } else {
                filterIndicator.style.display = 'none';
            }
        }

        // Update clear filters button
        const clearBtn = document.getElementById('clear-filters-btn');
        if (clearBtn) {
            clearBtn.disabled = activeFiltersCount === 0;
        }
    }

    updateFilterStatistics(blocks, filters) {
        const statsContainer = document.getElementById('filter-statistics');
        if (!statsContainer) return;

        const totalBlocks = blocks.length;
        const uniqueBatches = new Set(blocks.map((b) => b.batch_id)).size;
        const uniqueCourts = new Set(blocks.map((b) => b.court_name)).size;

        // Calculate date range
        let dateRangeText = '';
        if (filters.date_range_start && filters.date_range_end) {
            dateRangeText = `vom ${filters.date_range_start} bis ${filters.date_range_end}`;
        } else if (filters.date_range_start) {
            dateRangeText = `ab ${filters.date_range_start}`;
        } else if (filters.date_range_end) {
            dateRangeText = `bis ${filters.date_range_end}`;
        }

        statsContainer.innerHTML = `
            <div class="small text-muted">
                <strong>${totalBlocks}</strong> Sperrung(en) in <strong>${uniqueBatches}</strong> Batch(es) 
                auf <strong>${uniqueCourts}</strong> Platz/Plätzen ${dateRangeText}
            </div>
        `;
    }

    applyDatePreset(preset) {
        const today = new Date();
        let startDate, endDate;

        switch (preset) {
            case 'today':
                startDate = endDate = getToday();
                break;
            case 'tomorrow': {
                const tomorrow = new Date(today);
                tomorrow.setDate(tomorrow.getDate() + 1);
                startDate = endDate = toBerlinDateString(tomorrow);
                break;
            }
            case 'this-week': {
                const startOfWeek = new Date(today);
                startOfWeek.setDate(today.getDate() - today.getDay() + 1); // Monday
                const endOfWeek = new Date(startOfWeek);
                endOfWeek.setDate(startOfWeek.getDate() + 6); // Sunday
                startDate = toBerlinDateString(startOfWeek);
                endDate = toBerlinDateString(endOfWeek);
                break;
            }
            case 'next-week': {
                const nextWeekStart = new Date(today);
                nextWeekStart.setDate(today.getDate() + (8 - today.getDay())); // Next Monday
                const nextWeekEnd = new Date(nextWeekStart);
                nextWeekEnd.setDate(nextWeekStart.getDate() + 6); // Next Sunday
                startDate = toBerlinDateString(nextWeekStart);
                endDate = toBerlinDateString(nextWeekEnd);
                break;
            }
            case 'this-month':
                startDate = toBerlinDateString(new Date(today.getFullYear(), today.getMonth(), 1));
                endDate = toBerlinDateString(
                    new Date(today.getFullYear(), today.getMonth() + 1, 0)
                );
                break;
            case 'next-month':
                startDate = toBerlinDateString(
                    new Date(today.getFullYear(), today.getMonth() + 1, 1)
                );
                endDate = toBerlinDateString(
                    new Date(today.getFullYear(), today.getMonth() + 2, 0)
                );
                break;
        }

        // Update date inputs
        const startDateInput = document.getElementById('filter-start-date');
        const endDateInput = document.getElementById('filter-end-date');

        if (startDateInput) startDateInput.value = startDate;
        if (endDateInput) endDateInput.value = endDate;

        // Trigger filter update
        this.updateFilters();
    }

    clearAllFilters() {
        // Clear all filter inputs
        const filterInputs = document.querySelectorAll('.filter-input');
        filterInputs.forEach((input) => {
            if (input.type === 'checkbox') {
                input.checked = false;
            } else {
                input.value = '';
            }
        });

        // Clear state
        stateManager.clearFilters();

        // Update URL
        this.updateUrlParams({});

        // Reload without filters
        if (window.loadUpcomingBlocks) {
            window.loadUpcomingBlocks();
        }

        // Update indicators
        this.updateFilterIndicators({});

        showToast('Filter zurückgesetzt', 'info');
    }

    saveCurrentFilters() {
        const filters = stateManager.getCurrentFilters();
        const success = storageUtils.set(CONFIG.STORAGE_KEYS.FILTERS, filters);

        if (success) {
            showToast('Filter gespeichert', 'success');
        } else {
            showToast('Fehler beim Speichern der Filter', 'error');
        }
    }

    loadSavedFilters() {
        const savedFilters = storageUtils.get(CONFIG.STORAGE_KEYS.FILTERS, {});

        if (Object.keys(savedFilters).length > 0) {
            this.applyFilterValues(savedFilters);
            stateManager.setCurrentFilters(savedFilters);
        }
    }

    applyFilterValues(filters) {
        // Apply date range
        if (filters.date_range_start) {
            const input = document.getElementById('filter-start-date');
            if (input) input.value = filters.date_range_start;
        }

        if (filters.date_range_end) {
            const input = document.getElementById('filter-end-date');
            if (input) input.value = filters.date_range_end;
        }

        // Apply time range
        if (filters.start_time) {
            const input = document.getElementById('filter-start-time');
            if (input) input.value = filters.start_time;
        }

        if (filters.end_time) {
            const input = document.getElementById('filter-end-time');
            if (input) input.value = filters.end_time;
        }

        // Apply court filters
        if (filters.courts) {
            filters.courts.forEach((courtId) => {
                const checkbox = document.querySelector(
                    `input[name="filter-courts"][value="${courtId}"]`
                );
                if (checkbox) checkbox.checked = true;
            });
        }

        // Apply reason filters
        if (filters.reasons) {
            filters.reasons.forEach((reasonId) => {
                const checkbox = document.querySelector(
                    `input[name="filter-reasons"][value="${reasonId}"]`
                );
                if (checkbox) checkbox.checked = true;
            });
        }

        // Apply search text
        if (filters.search) {
            const input = document.getElementById('filter-search');
            if (input) input.value = filters.search;
        }

        // Apply status filters
        if (filters.show_past !== undefined) {
            const checkbox = document.getElementById('filter-show-past');
            if (checkbox) checkbox.checked = filters.show_past;
        }

        if (filters.show_future !== undefined) {
            const checkbox = document.getElementById('filter-show-future');
            if (checkbox) checkbox.checked = filters.show_future;
        }

        if (filters.show_active !== undefined) {
            const checkbox = document.getElementById('filter-show-active');
            if (checkbox) checkbox.checked = filters.show_active;
        }
    }

    updateUrlParams(filters) {
        const url = new URL(window.location);

        // Clear existing filter params
        const filterParams = [
            'date_range_start',
            'date_range_end',
            'start_time',
            'end_time',
            'courts',
            'reasons',
            'search',
            'show_past',
            'show_future',
            'show_active',
        ];
        filterParams.forEach((param) => url.searchParams.delete(param));

        // Add current filter params
        Object.keys(filters).forEach((key) => {
            const value = filters[key];
            if (Array.isArray(value)) {
                value.forEach((v) => url.searchParams.append(key, v));
            } else {
                url.searchParams.set(key, value);
            }
        });

        // Update URL without page reload
        window.history.replaceState({}, '', url);
    }

    showLoadingIndicator(show) {
        const indicator = document.getElementById('blocks-loading-indicator');
        if (indicator) {
            indicator.style.display = show ? 'block' : 'none';
        }

        const blocksList = document.getElementById('blocks-list');
        if (blocksList) {
            blocksList.style.opacity = show ? '0.5' : '1';
        }
    }

    // Initialize filters from URL parameters
    initializeFromUrl() {
        const url = new URL(window.location);
        const filters = {};

        // Extract filter parameters from URL
        const filterParams = [
            'date_range_start',
            'date_range_end',
            'start_time',
            'end_time',
            'search',
            'show_past',
            'show_future',
            'show_active',
        ];

        filterParams.forEach((param) => {
            const value = url.searchParams.get(param);
            if (value) {
                if (param.startsWith('show_')) {
                    filters[param] = value === 'true';
                } else {
                    filters[param] = value;
                }
            }
        });

        // Handle array parameters
        const courts = url.searchParams.getAll('courts');
        if (courts.length > 0) filters.courts = courts;

        const reasons = url.searchParams.getAll('reasons');
        if (reasons.length > 0) filters.reasons = reasons;

        if (Object.keys(filters).length > 0) {
            this.applyFilterValues(filters);
            stateManager.setCurrentFilters(filters);
            this.updateFilterIndicators(filters);
        }
    }
}

// Export singleton instance
export const blockFilters = new BlockFilters();
