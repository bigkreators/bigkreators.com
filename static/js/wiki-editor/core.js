// File: static/js/wiki-editor/core.js
/**
 * Core Wiki Editor Implementation
 * 
 * This file contains the main initialization and core functionality
 * for the wiki editor component.
 */

// Import core dependencies
import { createEditorToolbar, setupToolbarHandlers } from './toolbar.js';
import { addPreviewButton } from './preview.js';
import { addKeyboardShortcuts } from './keyboard.js';

/**
 * Initialize the Wiki Editor on a form
 * @param {HTMLElement} form - The form element containing the editor
 */
export function initializeWikiEditor(form) {
    // Find the content textarea
    const contentTextarea = form.querySelector('#article-content');
    if (!contentTextarea) {
        console.error('Wiki Editor initialization failed: #article-content not found');
        return;
    }
    
    console.log('Initializing Wiki Editor on', contentTextarea);
    
    // If Summernote is initialized, destroy it
    if (typeof $ !== 'undefined' && $.fn.summernote) {
        try {
            $(contentTextarea).summernote('destroy');
            console.log('Summernote editor destroyed');
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
    
    // Add the preview area after the editor container (hidden initially)
    const previewArea = form.querySelector('.wiki-preview-area');
    if (!previewArea) {
        console.error('Wiki Preview area not found');
    }
    
    // Set up the form submission handler to transform the content
    form.addEventListener('submit', function(e) {
        // Transform the article content by adding the short description
        transformContent(form);
        
        // The actual submission is handled by the form's existing event handler
    });
    
    // Add show preview button to form actions if not already present
    addPreviewButton(form);
    
    // Set up event handlers for toolbar buttons
    setupToolbarHandlers(toolbar, contentTextarea, previewArea);
    
    // Add keyboard shortcuts
    addKeyboardShortcuts(contentTextarea);
    
    console.log('Wiki Editor initialized successfully');
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
        console.log('Added short description to content');
    }
}
