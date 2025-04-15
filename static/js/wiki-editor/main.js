// File: static/js/wiki-editor/main.js
/**
 * Main Entry Point for Wiki Editor
 * 
 * This file serves as the entry point for the wiki editor functionality,
 * importing and initializing all necessary components.
 */

import { initializeWikiEditor } from './core.js';
import { registerEditorComponents } from './component-registry.js';

// Initialize editor components on page load
document.addEventListener('DOMContentLoaded', function() {
    // Register all editor components
    registerEditorComponents();
    
    // Initialize wiki editor on appropriate forms
    const editForms = [
        'create-article-form',
        'edit-article-form',
        'propose-edit-form',
        'talk-page-form',
        'quick-edit-form'
    ];
    
    editForms.forEach(formId => {
        const form = document.getElementById(formId);
        if (form) {
            initializeWikiEditor(form);
        }
    });
});

export default {
    initializeWikiEditor,
    registerEditorComponents
};
