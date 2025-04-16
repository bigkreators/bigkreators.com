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
    
    if (toggleContainers.length === 0) {
        // If no toggle containers found, try to inject one
        createModeToggle();
    }
    
    // Initialize existing toggles
    initializeToggles(toggleContainers);
    
    // Function to create and inject mode toggle if not present
    function createModeToggle() {
        // Check for common insertion points
        const insertPoints = [
            document.querySelector('.article-header'),
            document.querySelector('h1')?.parentNode,
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
        
        // Get current mode from URL
        const urlParams = new URLSearchParams(window.location.search);
        const currentMode = urlParams.get('mode') || 'wiki';
        
        // Create toggle container
        const toggleContainer = document.createElement('div');
        toggleContainer.className = 'mode-toggle';
        toggleContainer.innerHTML = `
            <button class="mode-toggle-button ${currentMode === 'wiki' ? 'active' : ''}" data-mode="wiki">Wiki Mode</button>
            <button class="mode-toggle-button ${currentMode === 'html' ? 'active' : ''}" data-mode="html">HTML Mode</button>
        `;
        
        // Insert after the first element
        const firstChild = insertPoint.firstChild;
        if (firstChild) {
            insertPoint.insertBefore(toggleContainer, firstChild.nextSibling);
        } else {
            insertPoint.appendChild(toggleContainer);
        }
        
        // Initialize the newly created toggle
        initializeToggles([toggleContainer]);
        
        // Add notice if in wiki mode
        if (currentMode === 'wiki') {
            const notice = document.createElement('div');
            notice.className = 'wiki-notice';
            notice.innerHTML = `
                <p><span class="wiki-icon">ℹ️</span> You are using the wiki markup editor. <a href="?mode=html">Switch to HTML mode</a> if you prefer.</p>
            `;
            insertPoint.appendChild(notice);
        }
    }
    
    // Initialize toggle buttons
    function initializeToggles(containers) {
        containers.forEach(container => {
            const buttons = container.querySelectorAll('.mode-toggle-button');
            
            // Set up event listeners for toggle buttons
            buttons.forEach(button => {
                // Remove existing event listeners by cloning
                const newButton = button.cloneNode(true);
                button.parentNode.replaceChild(newButton, button);
                
                newButton.addEventListener('click', function() {
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
                } else {
                    button.classList.remove('active');
                }
            });
        });
    }
});
