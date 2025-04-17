// File: static/js/wiki-editor/index.js
/**
 * Wiki Editor Public API
 * 
 * This file serves as the public API for the wiki editor,
 * exporting the main functionality for use by other modules.
 */

// Import and re-export core functionality
import { initializeWikiEditor } from './core.js';
import { registerEditorComponents } from './component-registry.js';
import { addModeToggle } from './wiki-mode-toggle.js';
import { addLineNumbers } from './line-numbers.js';
import { showWikiPreview } from './enhanced-preview.js';
import { 
    extractShortDescription,
    addShortDescription,
    getServerPreview 
} from './utils/transform-wiki.js';

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('Wiki Editor: DOM loaded');
    
    // Register editor components
    registerEditorComponents();
    
    // Initialize wiki editor on supported forms
    const supportedForms = [
        'create-article-form',
        'edit-article-form', 
        'propose-edit-form',
        'talk-page-form',
        'quick-edit-form'
    ];
    
    supportedForms.forEach(formId => {
        const form = document.getElementById(formId);
        if (form) {
            console.log('Initializing wiki editor on form:', formId);
            // Ensure the form is fully loaded
            setTimeout(() => {
                initializeWikiEditor(form);
            }, 100); // Small delay to ensure DOM is ready
        }
    });
    
    // Also look for wiki-editor-container class to initialize
    document.querySelectorAll('.wiki-editor-container').forEach(container => {
        const form = container.closest('form');
        if (form && !form.classList.contains('wiki-editor-initialized')) {
            console.log('Initializing wiki editor on container:', container);
            form.classList.add('wiki-editor-initialized');
            setTimeout(() => {
                initializeWikiEditor(form);
            }, 100);
        }
    });
    
    // Add mode toggle where needed
    addModeToggle();
    
    // Initialize line numbers on all wiki mode pages
    const urlParams = new URLSearchParams(window.location.search);
    const currentMode = urlParams.get('mode') || 'wiki';
    
    if (currentMode === 'wiki') {
        const contentTextareas = document.querySelectorAll('#article-content');
        contentTextareas.forEach(textarea => {
            addLineNumbers(textarea);
        });
    }
});

// Export public API
export {
    initializeWikiEditor,
    registerEditorComponents,
    addModeToggle,
    addLineNumbers,
    showWikiPreview,
    extractShortDescription,
    addShortDescription,
    getServerPreview
};
