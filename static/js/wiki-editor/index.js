/**
 * Wiki Editor Entry Point
 * 
 * This is the main entry point for the wiki editor functionality.
 * It imports and exports all editor components for easy use.
 */

// Import core components
import { initializeWikiEditor } from './core.js';

// Import utility modules
import { 
    addLineNumbers,
    transformWikiMarkup
} from './utils.js';

// Import text manipulation utilities
import {
    insertWikiMarkup,
    wrapSelectedText,
    prependToSelectedLines,
    removeIndent,
    escapeRegExp
} from './text-manipulation.js';

// Import toolbar components
import {
    createEditorToolbar,
    setupToolbarHandlers,
    removeWikiLinks
} from './toolbar.js';

// Import dialog components
import {
    openHeadingDialog,
    openLinkDialog,
    openCitationDialog,
    openReferenceDialog,
    openTableDialog,
    openTemplateGallery,
    openSearchReplaceDialog,
    createCitationDialog,
    createReferenceDialog,
    createTableDialog,
    createTemplateGallery,
    createSearchReplaceDialog
} from './dialogs.js';

// Import preview functionality
import {
    addPreviewButton,
    previewContent
} from './preview.js';

// Import keyboard shortcuts
import { addKeyboardShortcuts } from './keyboard.js';

// Initialize the editor when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize wiki editor on appropriate pages
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

// Export all components for external use
export {
    initializeWikiEditor,
    addLineNumbers,
    transformWikiMarkup,
    insertWikiMarkup,
    wrapSelectedText,
    prependToSelectedLines,
    removeIndent,
    createEditorToolbar,
    setupToolbarHandlers,
    removeWikiLinks,
    openHeadingDialog,
    openLinkDialog,
    openCitationDialog,
    openReferenceDialog,
    openTableDialog,
    openTemplateGallery,
    openSearchReplaceDialog,
    addPreviewButton,
    previewContent,
    addKeyboardShortcuts
};
