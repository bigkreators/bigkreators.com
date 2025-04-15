// File: static/js/wiki-editor/mode-toggle.js
/**
 * Wiki Mode Toggle Component
 * 
 * This file provides functionality for toggling between wiki markup
 * and HTML editing/viewing modes.
 */

/**
 * Add mode toggle to the page if needed
 */
export function addModeToggle() {
    // Check if the page URL contains mode parameter
    const urlParams = new URLSearchParams(window.location.search);
    const currentMode = urlParams.get('mode') || 'wiki';
    
    // Find places to insert the mode toggle
    const insertPoints = [
        document.querySelector('.article-header'),
        document.querySelector('h1').parentNode,
        document.querySelector('form')
    ];
    
    let insertPoint = null;
    for (const point of insertPoints) {
        if (point) {
            insertPoint = point;
            break;
        }
    }
    
    if (!insertPoint) return;
    
    // Check if mode toggle already exists
    if (document.querySelector('.mode-toggle')) return;
    
    // Create the toggle element
    const toggleContainer = document.createElement('div');
    toggleContainer.className = 'mode-toggle';
    toggleContainer.innerHTML = `
        <button class="mode-toggle-button ${currentMode === 'wiki' ? 'active' : ''}" data-mode="wiki">Wiki Mode</button>
        <button class="mode-toggle-button ${currentMode === 'html' ? 'active' : ''}" data-mode="html">HTML Mode</button>
    `;
    
    // Add notice if in wiki mode
    if (currentMode === 'wiki') {
        const notice = document.createElement('div');
        notice.className = 'wiki-notice';
        notice.innerHTML = `
            <p><span class="wiki-icon">ℹ️</span> You are using the new Wiki markup editor. <a href="?mode=html">Switch to HTML mode</a> if you prefer.</p>
        `;
        insertPoint.appendChild(notice);
    }
    
    // Insert after the first child of the insert point
    const firstChild = insertPoint.firstChild;
    if (firstChild) {
        insertPoint.insertBefore(toggleContainer, firstChild.nextSibling);
    } else {
        insertPoint.appendChild(toggleContainer);
    }
    
    // Add event listeners
    setupModeToggleHandlers(toggleContainer);
}

/**
 * Set up event handlers for the mode toggle
 * @param {HTMLElement} toggleContainer - The toggle container element
 */
function setupModeToggleHandlers(toggleContainer) {
    const buttons = toggleContainer.querySelectorAll('.mode-toggle-button');
    
    buttons.forEach(button => {
        button.addEventListener('click', function() {
            const mode = this.getAttribute('data-mode');
            
            // Don't do anything if already active
            if (this.classList.contains('active')) return;
            
            // Update URL with the new mode
            const url = new URL(window.location.href);
            url.searchParams.set('mode', mode);
            
            // Navigate to new URL
            window.location.href = url.toString();
        });
    });
}

export default {
    addModeToggle
};
