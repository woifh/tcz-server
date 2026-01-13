/**
 * Member Search Module
 * Provides search functionality for finding and adding members to favourites
 */

let searchTimeout = null;
const DEBOUNCE_DELAY = 300; // milliseconds

/**
 * Debounced search function
 * @param {string} query - Search query
 */
function debounceSearch(query) {
    // Clear existing timeout
    if (searchTimeout) {
        clearTimeout(searchTimeout);
    }
    
    // Set new timeout
    searchTimeout = setTimeout(() => {
        searchMembers(query);
    }, DEBOUNCE_DELAY);
}

/**
 * Search for members via API
 * @param {string} query - Search query
 */
async function searchMembers(query) {
    const resultsContainer = document.getElementById('search-results');
    const loadingSpinner = document.getElementById('search-loading');
    
    console.log('Searching for:', query);
    
    // Show loading indicator
    loadingSpinner.classList.remove('hidden');
    
    try {
        const url = `/members/search?q=${encodeURIComponent(query)}`;
        console.log('Fetching:', url);
        const response = await fetch(url);
        const data = await response.json();
        
        console.log('Response status:', response.status);
        console.log('Response data:', data);
        
        // Hide loading indicator
        loadingSpinner.classList.add('hidden');
        
        if (response.ok) {
            renderSearchResults(data.results);
        } else {
            // Display error message
            resultsContainer.innerHTML = `
                <div class="text-red-600 p-4 text-center">
                    ${data.error || 'Fehler bei der Suche'}
                </div>
            `;
        }
    } catch (error) {
        console.error('Search error:', error);
        // Hide loading indicator
        loadingSpinner.classList.add('hidden');
        
        // Display network error
        resultsContainer.innerHTML = `
            <div class="text-red-600 p-4 text-center">
                Netzwerkfehler. Bitte überprüfen Sie Ihre Verbindung.
            </div>
        `;
    }
}

/**
 * Render search results in the DOM
 * @param {Array} results - Array of member objects
 */
function renderSearchResults(results) {
    const resultsContainer = document.getElementById('search-results');
    const resultsCount = document.getElementById('search-results-count');
    
    // Reset highlight index
    currentHighlightIndex = -1;
    
    if (results.length === 0) {
        // Empty state
        resultsContainer.innerHTML = `
            <div class="text-gray-500 p-4 text-center">
                Keine Mitglieder gefunden
            </div>
        `;
        
        // Announce to screen readers
        if (resultsCount) {
            resultsCount.textContent = 'Keine Mitglieder gefunden';
        }
        return;
    }
    
    // Announce result count to screen readers
    if (resultsCount) {
        resultsCount.textContent = `${results.length} ${results.length === 1 ? 'Mitglied gefunden' : 'Mitglieder gefunden'}`;
    }
    
    // Render results
    resultsContainer.innerHTML = results.map(member => `
        <div class="flex justify-between items-center p-3 border border-gray-200 rounded hover:bg-gray-100" role="option" aria-label="${escapeHtml(member.name)}, ${escapeHtml(member.email)}">
            <div>
                <div class="font-semibold">${escapeHtml(member.name)}</div>
                <div class="text-sm text-gray-600">${escapeHtml(member.email)}</div>
            </div>
            <button 
                onclick="addToFavourites(${member.id})" 
                class="bg-green-600 text-white py-1 px-4 rounded hover:bg-green-700 text-sm"
                data-member-id="${member.id}"
                aria-label="${escapeHtml(member.name)} zu Favoriten hinzufügen"
            >
                Hinzufügen
            </button>
        </div>
    `).join('');
}

/**
 * Clear search results
 */
function clearSearchResults() {
    const resultsContainer = document.getElementById('search-results');
    resultsContainer.innerHTML = '';
}

/**
 * Add member to favourites
 * @param {number} memberId - ID of member to add
 */
async function addToFavourites(memberId) {
    const currentUserId = window.currentUserId;
    
    try {
        const response = await fetch(`/members/${currentUserId}/favourites`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ favourite_id: memberId })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Show success message
            showSuccessMessage('Favorit erfolgreich hinzugefügt!');
            
            // Remove member from search results
            const searchInput = document.getElementById('member-search-input');
            const currentQuery = searchInput.value;
            if (currentQuery) {
                searchMembers(currentQuery);
            }
            
            // Update favourites list
            if (typeof loadFavourites === 'function') {
                loadFavourites();
            }
            
            // Return focus to search input
            setTimeout(() => {
                searchInput.focus();
            }, 100);
        } else {
            // Display error message
            showErrorMessage(data.error || 'Fehler beim Hinzufügen');
        }
    } catch (error) {
        showErrorMessage('Netzwerkfehler. Bitte versuchen Sie es erneut.');
    }
}

/**
 * Show success message
 * @param {string} message - Success message
 */
function showSuccessMessage(message) {
    const resultsContainer = document.getElementById('search-results');
    const successDiv = document.createElement('div');
    successDiv.className = 'bg-green-100 text-green-800 p-3 rounded mb-2';
    successDiv.textContent = message;
    resultsContainer.insertBefore(successDiv, resultsContainer.firstChild);
    
    // Remove after 3 seconds
    setTimeout(() => {
        successDiv.remove();
    }, 3000);
}

/**
 * Show error message
 * @param {string} message - Error message
 */
function showErrorMessage(message) {
    const resultsContainer = document.getElementById('search-results');
    const errorDiv = document.createElement('div');
    errorDiv.className = 'bg-red-100 text-red-800 p-3 rounded mb-2';
    errorDiv.textContent = message;
    resultsContainer.insertBefore(errorDiv, resultsContainer.firstChild);
    
    // Remove after 5 seconds
    setTimeout(() => {
        errorDiv.remove();
    }, 5000);
}

/**
 * Escape HTML to prevent XSS
 * @param {string} text - Text to escape
 * @returns {string} Escaped text
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Initialize search functionality
 */
function initMemberSearch() {
    const searchInput = document.getElementById('member-search-input');
    const clearBtn = document.getElementById('search-clear-btn');
    
    if (!searchInput) return;
    
    // Input event listener with debouncing
    searchInput.addEventListener('input', function(e) {
        const query = e.target.value.trim();
        
        // Show/hide clear button
        if (query) {
            clearBtn.classList.remove('hidden');
            debounceSearch(query);
        } else {
            clearBtn.classList.add('hidden');
            clearSearchResults();
        }
    });
    
    // Clear button event listener
    clearBtn.addEventListener('click', function() {
        searchInput.value = '';
        clearBtn.classList.add('hidden');
        clearSearchResults();
        searchInput.focus();
    });
    
    // Keyboard navigation
    searchInput.addEventListener('keydown', handleKeyboardNavigation);
    
    // Focus on input when search form is shown
    searchInput.focus();
}

let currentHighlightIndex = -1;

/**
 * Handle keyboard navigation in search results
 * @param {KeyboardEvent} e - Keyboard event
 */
function handleKeyboardNavigation(e) {
    const resultsContainer = document.getElementById('search-results');
    const results = resultsContainer.querySelectorAll('[role="option"]');
    
    if (results.length === 0) return;
    
    switch(e.key) {
        case 'ArrowDown':
            e.preventDefault();
            currentHighlightIndex = Math.min(currentHighlightIndex + 1, results.length - 1);
            highlightResult(results, currentHighlightIndex);
            break;
            
        case 'ArrowUp':
            e.preventDefault();
            currentHighlightIndex = Math.max(currentHighlightIndex - 1, 0);
            highlightResult(results, currentHighlightIndex);
            break;
            
        case 'Enter':
            e.preventDefault();
            if (currentHighlightIndex >= 0 && currentHighlightIndex < results.length) {
                const addButton = results[currentHighlightIndex].querySelector('button[data-member-id]');
                if (addButton) {
                    const memberId = addButton.getAttribute('data-member-id');
                    addToFavourites(memberId);
                }
            }
            break;
    }
}

/**
 * Highlight a search result
 * @param {NodeList} results - List of result elements
 * @param {number} index - Index to highlight
 */
function highlightResult(results, index) {
    // Remove highlight from all results
    results.forEach((result, i) => {
        if (i === index) {
            result.classList.add('bg-blue-100', 'border-blue-500');
            result.classList.remove('hover:bg-gray-100');
            result.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
        } else {
            result.classList.remove('bg-blue-100', 'border-blue-500');
            result.classList.add('hover:bg-gray-100');
        }
    });
}

// Export functions for use in HTML
window.debounceSearch = debounceSearch;
window.searchMembers = searchMembers;
window.renderSearchResults = renderSearchResults;
window.clearSearchResults = clearSearchResults;
window.addToFavourites = addToFavourites;
window.initMemberSearch = initMemberSearch;
