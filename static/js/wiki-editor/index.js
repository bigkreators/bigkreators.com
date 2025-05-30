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
    // Find the content textarea
    const contentTextarea = form.querySelector('#article-content');
    if (!contentTextarea) {
        console.error('Wiki Editor initialization failed: #article-content not found');
        return;
    }
    
    console.log('Found textarea element:', contentTextarea);
    
    // If Summernote is initialized, destroy it
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
    console.log('Creating new toolbar');
    // Create new toolbar
    toolbar = createEditorToolbar();
    // Explicitly set display style to ensure it's visible
     toolbar.style.display = 'flex';
     editorContainer.insertBefore(toolbar, contentTextarea);


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
    
    // Set up the form submission handler to transform the content
    form.addEventListener('submit', function(e) {
        // Transform the article content by adding the short description
        transformContent(form);
    });
    
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
    
    // Use the addShortDescription utility
    const newContent = addShortDescription(content, summary);
    if (newContent !== content) {
        contentTextarea.value = newContent;
        console.log('Added short description to content');
    }
}

/**
 * Set up autosave functionality
 * @param {HTMLElement} form - The form element
 */
function setupAutoSave(form) {
    const contentTextarea = form.querySelector('#article-content');
    if (!contentTextarea) return;
    
    const formId = form.id || 'wiki-editor-form';
    const autosaveKey = `wiki-autosave-${formId}`;
    
    // Check for existing autosave data
    const savedData = localStorage.getItem(autosaveKey);
    if (savedData) {
        try {
            const data = JSON.parse(savedData);
            
            // If the data is less than 24 hours old, offer to restore
            const saveTime = new Date(data.timestamp);
            const now = new Date();
            const hoursDiff = (now - saveTime) / (1000 * 60 * 60);
            
            if (hoursDiff < 24 && data.content && data.content !== contentTextarea.value) {
                // Create autosave notice
                const notice = document.createElement('div');
                notice.className = 'wiki-autosave-notice';
                notice.innerHTML = `
                    <p>
                        <strong>Autosaved content found</strong> from ${formatTimeAgo(saveTime)}.
                        <button type="button" id="restore-autosave">Restore</button>
                        <button type="button" id="discard-autosave">Discard</button>
                    </p>
                `;
                
                // Insert before the editor container
                const editorContainer = contentTextarea.closest('.wiki-editor-container');
                editorContainer.parentNode.insertBefore(notice, editorContainer);
                
                // Add restore functionality
                document.getElementById('restore-autosave').addEventListener('click', function() {
                    contentTextarea.value = data.content;
                    
                    // Fill other fields if available
                    if (data.title) {
                        const titleInput = form.querySelector('#article-title');
                        if (titleInput) titleInput.value = data.title;
                    }
                    
                    if (data.summary) {
                        const summaryTextarea = form.querySelector('#article-summary');
                        if (summaryTextarea) summaryTextarea.value = data.summary;
                    }
                    
                    // Remove notice
                    notice.remove();
                });
                
                // Add discard functionality
                document.getElementById('discard-autosave').addEventListener('click', function() {
                    localStorage.removeItem(autosaveKey);
                    notice.remove();
                });
            }
        } catch (e) {
            console.error('Error parsing autosave data:', e);
            localStorage.removeItem(autosaveKey);
        }
    }
    
    // Set up autosave
    let autosaveTimeout = null;
    contentTextarea.addEventListener('input', function() {
        clearTimeout(autosaveTimeout);
        autosaveTimeout = setTimeout(function() {
            // Get form data
            const data = {
                content: contentTextarea.value,
                timestamp: new Date().toISOString()
            };
            
            // Add title and summary if available
            const titleInput = form.querySelector('#article-title');
            if (titleInput) data.title = titleInput.value;
            
            const summaryTextarea = form.querySelector('#article-summary');
            if (summaryTextarea) data.summary = summaryTextarea.value;
            
            // Save to localStorage
            localStorage.setItem(autosaveKey, JSON.stringify(data));
            
            // Visual indicator (optional)
            const saveIndicator = document.createElement('div');
            saveIndicator.className = 'autosave-indicator';
            saveIndicator.textContent = 'Autosaved';
            document.body.appendChild(saveIndicator);
            
            setTimeout(() => {
                saveIndicator.style.opacity = '0';
                setTimeout(() => saveIndicator.remove(), 500);
            }, 1500);
        }, 2000); // Autosave after 2 seconds of inactivity
    });
    
    // Clear autosave on successful form submission
    form.addEventListener('submit', function() {
        // We'll clear after submission is successful, in the form's own submit handler
        const originalContent = contentTextarea.value;
        
        // Set up a check to run later
        setTimeout(function() {
            // If the content has changed, the form was likely submitted successfully
            if (contentTextarea.value !== originalContent || !document.contains(contentTextarea)) {
                localStorage.removeItem(autosaveKey);
            }
        }, 1000);
    });
}

/**
 * Format time ago for autosave
 * @param {Date} date - The date to format
 * @returns {string} Formatted time ago
 */
function formatTimeAgo(date) {
    const now = new Date();
    const diffMs = now - date;
    const diffSec = Math.round(diffMs / 1000);
    const diffMin = Math.round(diffSec / 60);
    const diffHour = Math.round(diffMin / 60);
    
    if (diffSec < 60) {
        return `${diffSec} seconds ago`;
    } else if (diffMin < 60) {
        return `${diffMin} minute${diffMin === 1 ? '' : 's'} ago`;
    } else {
        return `${diffHour} hour${diffHour === 1 ? '' : 's'} ago`;
    }
}

// Export functions
export { showWikiPreview };
