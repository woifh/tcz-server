/**
 * Admin Panel State Management
 * Centralized state management for admin panel
 */

// Global state variables
export const state = {
    blockReasons: [],
    selectedBlocks: [],
    currentCalendarDate: new Date(),
    calendarBlocks: [],
    currentFilters: {},
    filterUpdateTimeout: null,
};

// State management functions
export const stateManager = {
    // Block reasons
    setBlockReasons(reasons) {
        state.blockReasons = reasons;
    },

    getBlockReasons() {
        return state.blockReasons;
    },

    // Selected blocks
    setSelectedBlocks(blocks) {
        state.selectedBlocks = blocks;
    },

    getSelectedBlocks() {
        return state.selectedBlocks;
    },

    addSelectedBlock(block) {
        if (!state.selectedBlocks.find((b) => b.id === block.id)) {
            state.selectedBlocks.push(block);
        }
    },

    removeSelectedBlock(blockId) {
        state.selectedBlocks = state.selectedBlocks.filter((b) => b.id !== blockId);
    },

    clearSelectedBlocks() {
        state.selectedBlocks = [];
    },

    // Calendar
    setCalendarDate(date) {
        state.currentCalendarDate = date;
    },

    getCalendarDate() {
        return state.currentCalendarDate;
    },

    setCalendarBlocks(blocks) {
        state.calendarBlocks = blocks;
    },

    getCalendarBlocks() {
        return state.calendarBlocks;
    },

    // Filters
    setCurrentFilters(filters) {
        state.currentFilters = filters;
    },

    getCurrentFilters() {
        return state.currentFilters;
    },

    updateFilter(key, value) {
        state.currentFilters[key] = value;
    },

    clearFilters() {
        state.currentFilters = {};
    },

    // Filter timeout
    setFilterTimeout(timeout) {
        if (state.filterUpdateTimeout) {
            clearTimeout(state.filterUpdateTimeout);
        }
        state.filterUpdateTimeout = timeout;
    },

    clearFilterTimeout() {
        if (state.filterUpdateTimeout) {
            clearTimeout(state.filterUpdateTimeout);
            state.filterUpdateTimeout = null;
        }
    },
};
