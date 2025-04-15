/**
 * Core Wiki Editor Implementation for Kryptopedia
 * 
 * This file contains the main initialization and core functionality
 * for the wiki editor component.
 */

// Import dependencies
import { createEditorToolbar, setupToolbarHandlers } from './toolbar.js';
import { addLineNumbers } from './utils.js';
import { addPreviewButton, previewContent } from './preview.js';
import { createCitationDialog, createReferenceDialog, createTableDialog, createTemplateGallery, createSearchReplaceDialog } from './dialogs.js';
import { addKeyboardShortcuts } from './keyboard.js';

/**
 * Initialize the Wiki Editor on a form
 * @param {HTMLElement} form - The form element containing the editor
 */
export function initializeWikiEditor(form) {
    // Find the content textarea
    const contentTextarea = form.querySelector('#article-content');
    if (!contentTextarea) return;
    
    // If Summernote is initialized, destroy it
    if (typeof $ !== 'undefined' && $.fn.summernote) {
        try {
            $(contentTextarea).summernote('destroy');
        } catch (e) {
            console.error('Error destroying Summernote:', e);
        }
    }
    
    // Create the editor toolbar
    const toolbar = createEditorToolbar();
    
    // Create editor container and insert it before the textarea
    const editorContainer = document.createElement('div');
    editorContainer.className = 'wiki-editor-container';
    contentTextarea.parentNode.insertBefore(editorContainer, contentTextarea);
    
    // Move textarea into the container
    editorContainer.appendChild(toolbar);
    editorContainer.appendChild(contentTextarea);
    
    // Add line numbering to textarea
    addLineNumbers(contentTextarea);
    
    // Add the preview area after the editor container (hidden initially)
    const previewArea = document.createElement('div');
    previewArea.className = 'wiki-preview-area';
    previewArea.style.display = 'none';
    editorContainer.parentNode.insertBefore(previewArea, editorContainer.nextSibling);
    
    // Set up the form submission handler to transform the content
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Transform the article content by adding the short description
        transformContent(form);
        
        // Submit the form
        const event = new Event('wiki-editor-submit', {
            bubbles: true,
            cancelable: true
        });
        
        const shouldProceed = form.dispatchEvent(event);
        if (shouldProceed) {
            // If using the original form submission logic
            const originalSubmit = form.getAttribute('data-original-submit');
            if (originalSubmit && window[originalSubmit]) {
                window[originalSubmit]();
            } else {
                form.submit();
            }
        }
    });
    
    // Add show preview button to form actions
    addPreviewButton(form);
    
    // Style the cancel button
    styleCancelButton(form);
    
    // Set up event handlers for toolbar buttons
    setupToolbarHandlers(toolbar, contentTextarea, previewArea);
    
    // Add keyboard shortcuts
    addKeyboardShortcuts(contentTextarea);
    
    // Add the citation and reference dialogs
    createCitationDialog();
    createReferenceDialog();
    
    // Add the table dialog
    createTableDialog();
    
    // Add the template gallery dialog
    createTemplateGallery();
    
    // Create search and replace dialog (once)
    createSearchReplaceDialog();
}

/**
 * Style the cancel button
 * @param {HTMLElement} form - The form element
 */
function styleCancelButton(form) {
    const cancelButton = form.querySelector('.cancel-button');
    if (cancelButton) {
        // Ensure the button has the cancel-button class
        if (!cancelButton.classList.contains('cancel-button')) {
            cancelButton.classList.add('cancel-button');
        }
    }
}

/**
 * Transform the article content before submission
 * @param {HTMLElement} form - The form element containing the editor
 */
function transformContent(form) {
    const contentTextarea = form.querySelector('#article-content');
    const summaryTextarea = form.querySelector('#article-summary');
    
    if (!contentTextarea || !summaryTextarea) return;
    
    // Get content and summary
    let content = contentTextarea.value;
    const summary = summaryTextarea.value.trim();
    
    // Check if content already has a short description
    if (summary && !content.includes('{{Short description|')) {
        // Add short description at the beginning
        content = `{{Short description|${summary}}}\n\n${content}`;
        contentTextarea.value = content;
    }
}

// Initialize wiki editor on appropriate pages when DOM is ready
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
