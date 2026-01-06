/**
 * Admin Panel Constants
 * German text constants and configuration for admin features
 */

// German text constants for enhanced admin features
export const GERMAN_TEXT = {
    // Recurring block features
    RECURRING_BLOCK: 'Wiederkehrende Sperrung',
    EDIT_SERIES: 'Serie bearbeiten',
    EDIT_SINGLE_INSTANCE: 'Einzelne Instanz bearbeiten',
    ALL_FUTURE_INSTANCES: 'Alle zukünftigen Instanzen',
    DELETE_ENTIRE_SERIES: 'Gesamte Serie löschen',
    
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

// Configuration constants
export const CONFIG = {
    DEBOUNCE_DELAY: 300,
    DEFAULT_DATE_RANGE_DAYS: 7,
    STORAGE_KEYS: {
        FILTERS: 'adminBlockFilters',
        PREFERENCES: 'adminPreferences'
    }
};
