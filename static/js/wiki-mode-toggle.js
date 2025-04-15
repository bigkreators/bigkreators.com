// File: static/js/wiki-mode-toggle.js
/**
 * Wiki Mode Toggle Component
 * 
 * This file provides functionality for toggling between wiki markup
 * and HTML editing/viewing modes.
 */

document.addEventListener('DOMContentLoaded', function() {
    // Find all mode toggle containers
    const toggleContainers = document.querySelectorAll('.mode-toggle');
    
    toggleContainers.forEach(container => {
        const buttons = container.querySelectorAll('.mode-toggle-button');
        
        // Set up event listeners for toggle buttons
        buttons.forEach(button => {
            button.addEventListener('click', function() {
                // Get the mode from the button
                const mode = this.getAttribute('data-mode');
                
                // If already active, do nothing
                if (this.classList.contains('active')) {
                    return;
                }
                
                // Update active state
                buttons.forEach(btn => btn.classList.remove('active'));
                this.classList.add('active');
                
                // Get current URL and update query parameter
                const url = new URL(window.location.href);
                url.searchParams.set('mode', mode);
                
                // Navigate to the new URL
                window.location.href = url.toString();
            });
        });
        
        // Set active state based on current URL
        const currentUrl = new URL(window.location.href);
        const currentMode = currentUrl.searchParams.get('mode') || 'wiki';
        
        buttons.forEach(button => {
            if (button.getAttribute('data-mode') === currentMode) {
                button.classList.add('active');
            }
        });
    });
});
