// static/js/wiki-editor-init.js

import { initializeWikiEditor } from './core.js';
import { initializeBackendConnection } from './wiki-editor-backend-integration.js';

document.addEventListener('DOMContentLoaded', function() {
    console.log('Wiki Editor Initialization Script loaded');
    
    // Check if we're in wiki mode or html mode
    const urlParams = new URLSearchParams(window.location.search);
    const currentMode = urlParams.get('mode') || 'wiki';
    
    if (currentMode === 'wiki') {
        // Initialize backend connection
        initializeBackendConnection();
        
        // Find wiki editor containers
        const supportedForms = [
            'create-article-form',
            'edit-article-form',
            'propose-edit-form',
            'talk-page-form',
            'quick-edit-form'
        ];
        
        // Initialize wiki editor on all supported forms
        for (const formId of supportedForms) {
            const form = document.getElementById(formId);
            if (form) {
                console.log(`Initializing wiki editor on ${formId}`);
                initializeWikiEditor(form);
            }
        }
        
        // Add the mode toggle buttons if not already present
        addModeToggle();
    } else {
        // In HTML mode, ensure the HTML editor is initialized
        initializeHtmlEditor();
    }
});

// Add mode toggle buttons to switch between Wiki and HTML modes
function addModeToggle() {
    const toggleContainer = document.querySelector('.mode-toggle');
    if (toggleContainer) return; // Already exists
    
    // Create the toggle element
    const newToggle = document.createElement('div');
    newToggle.className = 'mode-toggle';
    newToggle.innerHTML = `
        <button class="mode-toggle-button active" data-mode="wiki">Wiki Mode</button>
        <button class="mode-toggle-button" data-mode="html">HTML Mode</button>
    `;
    
    // Find where to insert it - after the heading
    const heading = document.querySelector('h1');
    if (heading) {
        heading.parentNode.insertBefore(newToggle, heading.nextSibling);
        
        // Add click handlers
        const buttons = newToggle.querySelectorAll('.mode-toggle-button');
        buttons.forEach(button => {
            button.addEventListener('click', function() {
                const mode = this.getAttribute('data-mode');
                if (this.classList.contains('active')) return;
                
                const url = new URL(window.location.href);
                url.searchParams.set('mode', mode);
                window.location.href = url.toString();
            });
        });
    }
}

// Initialize HTML editor (like Summernote) if in HTML mode
function initializeHtmlEditor() {
    if (typeof $ !== 'undefined' && $.fn.summernote) {
        $('#article-content').summernote({
            height: 400,
            toolbar: [
                ['style', ['style']],
                ['font', ['bold', 'italic', 'underline', 'clear']],
                ['fontname', ['fontname']],
                ['color', ['color']],
                ['para', ['ul', 'ol', 'paragraph']],
                ['table', ['table']],
                ['insert', ['link', 'picture']],
                ['view', ['fullscreen', 'codeview', 'help']]
            ]
        });
    }
    
    // Also add the mode toggle
    addModeToggle();
}
