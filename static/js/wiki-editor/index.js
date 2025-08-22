// File: static/js/wiki-editor/index.js

/**
 * Core Wiki Editor Implementation
 * 
 * This file contains the main initialization and core functionality
 * for the wiki editor component.
 */

// Import core dependencies
import { createEditorToolbar, setupToolbarHandlers } from './toolbar.js';
import { addLineNumbers } from './line-numbers.js';
import { showWikiPreview } from './enhanced-preview.js';
import { addKeyboardShortcuts } from './keyboard.js';
import { addShortDescription } from './utils/transform-wiki.js';
import { getServerPreview } from './wiki-editor-backend-integration.js';

/**
 * Initialize the Wiki Editor on a form
 * @param {HTMLElement} form - The form element containing the editor
 */
export function initializeWikiEditor(form) {
    console.log('Wiki Editor initialization starting...');
    
    // Check if this is the create-article form - if so, don't initialize wiki editor
    if (form && form.id === 'create-article-form') {
        console.log('Skipping wiki editor initialization for create-article-form (uses Summernote)');
        return;
    }
    
    // Find the content textarea
    const contentTextarea = form.querySelector('#article-content');
    if (!contentTextarea) {
        console.error('Wiki Editor initialization failed: #article-content not found');
        return;
    }
    
    console.log('Found textarea element:', contentTextarea);
    
    // If Summernote is initialized, destroy it first
    if (typeof $ !== 'undefined' && $.fn.summernote) {
        try {
            $(contentTextarea).summernote('destroy');
            console.log('Summernote editor destroyed');
        } catch (e) {
            console.error('Error destroying Summernote:', e);
        }
    }

    // Find or create editor container
    let editorContainer = contentTextarea.closest('.wiki-editor-container');
    if (!editorContainer) {
        console.log('Creating new editor container');
        // Wrap textarea in container
        editorContainer = document.createElement('div');
        editorContainer.className = 'wiki-editor-container';
        contentTextarea.parentNode.insertBefore(editorContainer, contentTextarea);
        editorContainer.appendChild(contentTextarea);
    } else {
        console.log('Found existing editor container');
    }

    // Create toolbar if it doesn't exist
    let toolbar = editorContainer.querySelector('.wiki-editor-toolbar');
    if (!toolbar) {
        console.log('Creating new toolbar');
        // Create new toolbar
        toolbar = createEditorToolbar();
        // Explicitly set display style to ensure it's visible
        toolbar.style.display = 'flex';
        editorContainer.insertBefore(toolbar, contentTextarea);
    }

    // Create or identify preview area
    let previewArea = form.querySelector('.wiki-preview-area');
    if (!previewArea) {
        console.log('Creating new preview area');
        // Create one if it doesn't exist
        previewArea = document.createElement('div');
        previewArea.className = 'wiki-preview-area';
        previewArea.style.display = 'none';
        editorContainer.parentNode.insertBefore(previewArea, editorContainer.nextSibling);
    } else {
        console.log('Found existing preview area');
    }

    // Ensure the editor CSS is loaded
    ensureEditorStyles();
    
    // Set up the form submission handler ONLY for wiki forms, not create-article
    if (form.id !== 'create-article-form') {
        form.addEventListener('submit', function(e) {
            // Transform the article content by adding the short description
            transformContent(form);
        });
    }
    
    // Add line numbers
    addLineNumbers(contentTextarea);
    
    // Add preview button to form actions if not already present
    const formActions = form.querySelector('.form-actions');
    if (formActions) {
        // Check if preview button already exists
        if (!formActions.querySelector('#preview-button')) {
            // Create preview button
            const previewButton = document.createElement('button');
            previewButton.type = 'button';
            previewButton.id = 'preview-button';
            previewButton.className = 'preview-button';
            previewButton.textContent = 'Show Preview';
            
            // Insert after the save button
            const saveButton = formActions.querySelector('[type="submit"]');
            if (saveButton && saveButton.nextSibling) {
                formActions.insertBefore(previewButton, saveButton.nextSibling);
            } else {
                formActions.appendChild(previewButton);
            }
            
            // Add click handler
            previewButton.addEventListener('click', function(e) {
                e.preventDefault(); // Prevent form submission
                showWikiPreview(form);
            });
        } else {
            // Preview button exists, make sure it has a click handler
            const previewButton = formActions.querySelector('#preview-button');
            // Remove existing event listeners
            const newPreviewButton = previewButton.cloneNode(true);
            previewButton.parentNode.replaceChild(newPreviewButton, previewButton);
            
            // Add new click handler
            newPreviewButton.addEventListener('click', function(e) {
                e.preventDefault(); // Prevent form submission
                showWikiPreview(form);
            });
        }
    }
    
    // Set up event handlers for toolbar buttons
    console.log('Setting up toolbar handlers with textarea:', contentTextarea);
    setupToolbarHandlers(toolbar, contentTextarea, previewArea);
    
    // Add keyboard shortcuts
    addKeyboardShortcuts(contentTextarea);
    
    // Add AutoSave functionality
    setupAutoSave(form);
    
    console.log('Wiki Editor initialized successfully');
}

/**
 * Ensure that the editor styles are loaded
 */
function ensureEditorStyles() {
    // Check if the CSS link already exists
    if (!document.getElementById('wiki-editor-toolbar-styles')) {
        // Create link to external CSS file
        const link = document.createElement('link');
        link.id = 'wiki-editor-toolbar-styles';
        link.rel = 'stylesheet';
        link.href = '/static/css/wiki-editor-toolbar.css';
        document.head.appendChild(link);
        
        console.log('Wiki Editor toolbar styles loaded');
    }
}

/**
 * Transform content before form submission (add short description)
 * @param {HTMLElement} form - The form element
 */
function transformContent(form) {
    const summaryInput = form.querySelector('#article-summary');
    if (summaryInput) {
        const summary = summaryInput.value;
        if (summary) {
            addShortDescription(form, summary);
        }
    }
}

/**
 * Set up auto-save functionality
 * @param {HTMLElement} form - The form element
 */
function setupAutoSave(form) {
    const contentTextarea = form.querySelector('#article-content');
    if (!contentTextarea) return;
    
    let autoSaveTimeout;
    const AUTOSAVE_DELAY = 30000; // 30 seconds
    
    function autoSave() {
        const content = contentTextarea.value;
        const articleId = form.dataset.articleId || window.location.pathname.split('/').pop();
        
        if (content && articleId) {
            localStorage.setItem(`autosave_${articleId}`, JSON.stringify({
                content: content,
                timestamp: Date.now()
            }));
            console.log('Content auto-saved');
        }
    }
    
    function scheduleAutoSave() {
        clearTimeout(autoSaveTimeout);
        autoSaveTimeout = setTimeout(autoSave, AUTOSAVE_DELAY);
    }
    
    // Set up auto-save on content changes
    contentTextarea.addEventListener('input', scheduleAutoSave);
    
    // Load auto-saved content if available
    const articleId = form.dataset.articleId || window.location.pathname.split('/').pop();
    const saved = localStorage.getItem(`autosave_${articleId}`);
    
    if (saved) {
        try {
            const savedData = JSON.parse(saved);
            const savedTime = new Date(savedData.timestamp);
            const now = new Date();
            const timeDiff = now - savedTime;
            
            // If auto-save is less than 24 hours old, offer to restore
            if (timeDiff < 24 * 60 * 60 * 1000) {
                if (confirm(`Auto-saved content from ${savedTime.toLocaleString()} found. Restore it?`)) {
                    contentTextarea.value = savedData.content;
                }
            }
        } catch (e) {
            console.error('Error loading auto-saved content:', e);
        }
    }
}

/**
 * Clear auto-save data for an article
 * @param {string} articleId - The article ID
 */
export function clearAutoSave(articleId) {
    localStorage.removeItem(`autosave_${articleId}`);
}

/**
 * Check if the wiki editor should be enabled for a form
 * @param {HTMLElement} form - The form element
 * @returns {boolean} Whether to enable wiki editor
 */
export function shouldEnableWikiEditor(form) {
    // Don't enable for create-article form (uses Summernote)
    if (form && form.id === 'create-article-form') {
        return false;
    }
    
    // Enable for edit forms and proposal forms
    const enabledFormIds = ['edit-article-form', 'propose-edit-form', 'quick-edit-form'];
    return enabledFormIds.includes(form.id);
}

/**
 * Initialize wiki editor conditionally based on form type
 * @param {HTMLElement} form - The form element
 */
export function conditionallyInitializeWikiEditor(form) {
    if (shouldEnableWikiEditor(form)) {
        initializeWikiEditor(form);
    } else {
        console.log(`Wiki editor not initialized for form: ${form.id}`);
    }
}
