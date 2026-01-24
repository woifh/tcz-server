/**
 * Admin Panel Utility Functions
 * Common utility functions used across admin components
 */

import { getToday, toBerlinDateString } from '../../../utils/date-utils.js';

// Toast notification system
export function showToast(message, type = 'info', duration = 5000) {
    // Remove existing toasts
    const existingToasts = document.querySelectorAll('.toast');
    existingToasts.forEach((toast) => toast.remove());

    // Create toast element
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
        <div class="toast-content">
            <span class="toast-message">${message}</span>
            <button class="toast-close" onclick="this.parentElement.parentElement.remove()">&times;</button>
        </div>
    `;

    // Add to page
    document.body.appendChild(toast);

    // Auto-remove after duration
    setTimeout(() => {
        if (toast.parentElement) {
            toast.remove();
        }
    }, duration);
}

// Date and time utilities
export const dateUtils = {
    formatDate(date) {
        if (typeof date === 'string') {
            date = new Date(date);
        }
        return date.toLocaleDateString('de-DE');
    },

    formatTime(time) {
        if (typeof time === 'string' && time.includes(':')) {
            return time.substring(0, 5); // Remove seconds if present
        }
        return time;
    },

    formatDateTime(dateTime) {
        if (typeof dateTime === 'string') {
            dateTime = new Date(dateTime);
        }
        return `${this.formatDate(dateTime)} ${this.formatTime(dateTime.toTimeString())}`;
    },

    getTodayString() {
        return getToday();
    },

    getDatePlusDays(days) {
        const date = new Date();
        date.setDate(date.getDate() + days);
        return toBerlinDateString(date);
    },

    isValidTimeRange(startTime, endTime) {
        if (!startTime || !endTime) return false;

        const start = new Date(`2000-01-01T${startTime}`);
        const end = new Date(`2000-01-01T${endTime}`);

        return start < end;
    },
};

// Form validation utilities
export const formUtils = {
    validateRequired(value) {
        return value && value.toString().trim() !== '';
    },

    validateEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    },

    validateTimeRange(startTime, endTime) {
        return dateUtils.isValidTimeRange(startTime, endTime);
    },

    getFormData(formElement) {
        const formData = new FormData(formElement);
        const data = {};

        for (const [key, value] of formData.entries()) {
            if (data[key]) {
                // Handle multiple values (like checkboxes)
                if (Array.isArray(data[key])) {
                    data[key].push(value);
                } else {
                    data[key] = [data[key], value];
                }
            } else {
                data[key] = value;
            }
        }

        return data;
    },

    clearForm(formElement) {
        formElement.reset();

        // Clear any custom validation states
        const inputs = formElement.querySelectorAll('input, select, textarea');
        inputs.forEach((input) => {
            input.classList.remove('is-invalid', 'is-valid');
        });
    },

    setFieldError(fieldName, message) {
        const field =
            document.getElementById(fieldName) || document.querySelector(`[name="${fieldName}"]`);
        if (field) {
            field.classList.add('is-invalid');

            // Add or update error message
            let errorDiv = field.parentElement.querySelector('.invalid-feedback');
            if (!errorDiv) {
                errorDiv = document.createElement('div');
                errorDiv.className = 'invalid-feedback';
                field.parentElement.appendChild(errorDiv);
            }
            errorDiv.textContent = message;
        }
    },

    clearFieldError(fieldName) {
        const field =
            document.getElementById(fieldName) || document.querySelector(`[name="${fieldName}"]`);
        if (field) {
            field.classList.remove('is-invalid');

            const errorDiv = field.parentElement.querySelector('.invalid-feedback');
            if (errorDiv) {
                errorDiv.remove();
            }
        }
    },
};

// DOM utilities
export const domUtils = {
    createElement(tag, className = '', innerHTML = '') {
        const element = document.createElement(tag);
        if (className) element.className = className;
        if (innerHTML) element.innerHTML = innerHTML;
        return element;
    },

    show(element) {
        if (typeof element === 'string') {
            element = document.getElementById(element);
        }
        if (element) {
            element.style.display = '';
            element.classList.remove('d-none');
        }
    },

    hide(element) {
        if (typeof element === 'string') {
            element = document.getElementById(element);
        }
        if (element) {
            element.style.display = 'none';
            element.classList.add('d-none');
        }
    },

    toggle(element) {
        if (typeof element === 'string') {
            element = document.getElementById(element);
        }
        if (element) {
            if (element.style.display === 'none' || element.classList.contains('d-none')) {
                this.show(element);
            } else {
                this.hide(element);
            }
        }
    },

    addClass(element, className) {
        if (typeof element === 'string') {
            element = document.getElementById(element);
        }
        if (element) {
            element.classList.add(className);
        }
    },

    removeClass(element, className) {
        if (typeof element === 'string') {
            element = document.getElementById(element);
        }
        if (element) {
            element.classList.remove(className);
        }
    },

    hasClass(element, className) {
        if (typeof element === 'string') {
            element = document.getElementById(element);
        }
        return element ? element.classList.contains(className) : false;
    },
};

// Array and object utilities
export const dataUtils = {
    groupBy(array, key) {
        return array.reduce((groups, item) => {
            const group = item[key];
            if (!groups[group]) {
                groups[group] = [];
            }
            groups[group].push(item);
            return groups;
        }, {});
    },

    sortBy(array, key, direction = 'asc') {
        return array.sort((a, b) => {
            const aVal = a[key];
            const bVal = b[key];

            if (direction === 'desc') {
                return bVal > aVal ? 1 : bVal < aVal ? -1 : 0;
            } else {
                return aVal > bVal ? 1 : aVal < bVal ? -1 : 0;
            }
        });
    },

    filterBy(array, filters) {
        return array.filter((item) => {
            return Object.keys(filters).every((key) => {
                const filterValue = filters[key];
                const itemValue = item[key];

                if (filterValue === null || filterValue === undefined || filterValue === '') {
                    return true; // No filter applied
                }

                if (Array.isArray(filterValue)) {
                    return filterValue.includes(itemValue);
                }

                if (typeof filterValue === 'string') {
                    return itemValue.toString().toLowerCase().includes(filterValue.toLowerCase());
                }

                return itemValue === filterValue;
            });
        });
    },

    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    deepClone(obj) {
        return JSON.parse(JSON.stringify(obj));
    },
};

// Local storage utilities
export const storageUtils = {
    set(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
            return true;
        } catch (error) {
            console.error('Error saving to localStorage:', error);
            return false;
        }
    },

    get(key, defaultValue = null) {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : defaultValue;
        } catch (error) {
            console.error('Error reading from localStorage:', error);
            return defaultValue;
        }
    },

    remove(key) {
        try {
            localStorage.removeItem(key);
            return true;
        } catch (error) {
            console.error('Error removing from localStorage:', error);
            return false;
        }
    },

    clear() {
        try {
            localStorage.clear();
            return true;
        } catch (error) {
            console.error('Error clearing localStorage:', error);
            return false;
        }
    },
};

// Event handling utilities
export const eventUtils = {
    on(element, event, handler, options = {}) {
        if (typeof element === 'string') {
            element = document.getElementById(element);
        }
        if (element) {
            element.addEventListener(event, handler, options);
        }
    },

    off(element, event, handler) {
        if (typeof element === 'string') {
            element = document.getElementById(element);
        }
        if (element) {
            element.removeEventListener(event, handler);
        }
    },

    once(element, event, handler) {
        this.on(element, event, handler, { once: true });
    },

    delegate(parent, selector, event, handler) {
        if (typeof parent === 'string') {
            parent = document.getElementById(parent);
        }
        if (parent) {
            parent.addEventListener(event, (e) => {
                if (e.target.matches(selector)) {
                    handler.call(e.target, e);
                }
            });
        }
    },
};
