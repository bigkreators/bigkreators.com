// static/js/wiki-editor/wiki-mode-toggle.js
/**
 * Wiki Mode Toggle Functionality
 * 
 * This file provides mode toggle functionality for switching between
 * wiki markup and HTML editing/viewing modes.
 */

(function() {
    // Execute when the DOM is fully loaded
    document.addEventListener('DOMContentLoaded', function() {
        console.log('Wiki Mode Toggle script loaded');
        
        // Find existing mode toggle or create a new one
        setupModeToggle();
        
        // Handle any clicks on mode toggle buttons
        document.addEventListener('click', function(e) {
            if (e.target && e.target.classList.contains('mode-toggle-button')) {
                handleModeToggle(e.target);
            }
        });
    });

    /**
     * Set up the mode toggle component if needed
     */
    function setupModeToggle() {
        // Check if toggle already exists
        const existingToggle = document.querySelector('.mode-toggle');
        if (existingToggle) {
            return; // Toggle already exists, no need to create one
        }

        // Try to find appropriate places to insert the toggle
        const possibleMountPoints = [
            document.querySelector('h1'), // After main heading
            document.querySelector('.article-header'), // After article header
            document.querySelector('form') // At the top of the form
        ];

        // Get current mode from URL or default to 'wiki'
        const urlParams = new URLSearchParams(window.location.search);
        const currentMode = urlParams.get('mode') || 'wiki';
        
        // Find first valid mount point
        const mountPoint = possibleMountPoints.find(el => el !== null);
        if (!mountPoint) return; // No suitable place to add the toggle
        
        // Create toggle container
        const toggleContainer = document.createElement('div');
        toggleContainer.className = 'mode-toggle';
        toggleContainer.innerHTML = `
            <button class="mode-toggle-button ${currentMode === 'wiki' ? 'active' : ''}" data-mode="wiki">Wiki Mode</button>
            <button class="mode-toggle-button ${currentMode === 'html' ? 'active' : ''}" data-mode="html">HTML Mode</button>
        `;
        
        // Insert after the mount point
        mountPoint.parentNode.insertBefore(toggleContainer, mountPoint.nextSibling);
        
        // Add notice for wiki mode
        if (currentMode === 'wiki') {
            const notice = document.createElement('div');
            notice.className = 'wiki-notice';
            notice.innerHTML = `
                <p><span class="wiki-icon">ℹ️</span> You are using the wiki markup editor. <a href="?mode=html">Switch to HTML mode</a> if you prefer.</p>
            `;
            toggleContainer.parentNode.insertBefore(notice, toggleContainer.nextSibling);
        }
    }

    /**
     * Handle clicks on mode toggle buttons
     * @param {HTMLElement} button - The clicked button
     */
    function handleModeToggle(button) {
        const mode = button.getAttribute('data-mode');
        
        // Don't do anything if the button is already active
        if (button.classList.contains('active')) {
            return;
        }
        
        // Update URL with the new mode
        const url = new URL(window.location.href);
        url.searchParams.set('mode', mode);
        window.location.href = url.toString();
    }

    /**
     * Add mode toggle to DOM
     * @param {string} mode - Current mode (wiki or html)
     */
    function addModeToggle(mode) {
        const container = document.createElement('div');
        container.className = 'mode-toggle';
        container.innerHTML = `
            <button class="mode-toggle-button ${mode === 'wiki' ? 'active' : ''}" data-mode="wiki">Wiki Mode</button>
            <button class="mode-toggle-button ${mode === 'html' ? 'active' : ''}" data-mode="html">HTML Mode</button>
        `;
        return container;
    }

    // Expose public API
    window.wikiModeToggle = {
        setup: setupModeToggle,
        addToggle: addModeToggle
    };
})();
