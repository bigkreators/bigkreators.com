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
    
    // Validate form parameter
    if (!form) {
        console.error('Wiki Editor initialization failed: form parameter is required');
        return;
    }
    
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
    if (!toolbar) {
        console.log('Creating new toolbar');
        // Create new toolbar
        toolbar = createEditorToolbar();
        // Explicitly set display style to ensure it's visible
        toolbar.style.display = 'flex';
        editorContainer.insertBefore(toolbar, contentTextarea);
    } else {
        console.log('Found existing toolbar');
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
    
    // Set up the form submission handler to transform the content
    form.addEventListener('submit', function(e) {
        // CRITICAL: Prevent default form submission to avoid page reload
        e.preventDefault();
        
        // Transform the article content by adding the short description
        transformContent(form);
        
        // Handle the actual API submission
        handleFormSubmission(form);
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
 * Handle the actual form submission after content transformation
 * @param {HTMLElement} form - The form element
 */
function handleFormSubmission(form) {
    // Get the token
    const token = localStorage.getItem('token');
    if (!token) {
        alert('You must be logged in to create articles.');
        return;
    }
    
    // Get form values
    const articleTitle = form.querySelector('#article-title')?.value;
    const articleSummary = form.querySelector('#article-summary')?.value;
    const articleContent = form.querySelector('#article-content')?.value;
    const categoriesInput = form.querySelector('#article-categories')?.value || '';
    const tagsInput = form.querySelector('#article-tags')?.value || '';
    const editComment = form.querySelector('#edit-comment')?.value;
    
    // Process categories and tags
    const categories = categoriesInput.split(',')
        .map(item => item.trim())
        .filter(item => item.length > 0);
        
    const tags = tagsInput.split(',')
        .map(item => item.trim())
        .filter(item => item.length > 0);
    
    // Validate required fields
    if (!articleTitle || !articleSummary || !articleContent) {
        alert('Please fill in all required fields.');
        return;
    }
    
    if (!editComment) {
        alert('Please provide a summary of your changes.');
        return;
    }
    
    // Show loading state
    const submitButton = form.querySelector('[type="submit"]');
    const originalText = submitButton.textContent;
    submitButton.textContent = 'Creating Article...';
    submitButton.disabled = true;
    
    // Prepare the data
    const articleData = {
        title: articleTitle,
        summary: articleSummary,
        content: articleContent,
        categories: categories,
        tags: tags,
        editComment: editComment
    };
    
    // Submit via API
    fetch('/api/articles', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(articleData)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        // Success! Clear autosave and redirect
        const formId = form.id || 'wiki-editor-form';
        const autosaveKey = `wiki-autosave-${formId}`;
        localStorage.removeItem(autosaveKey);
        
        // Show success message
        alert('Article created successfully!');
        
        // Redirect to the new article
        if (data.slug) {
            window.location.href = `/articles/${data.slug}`;
        } else {
            window.location.href = '/articles';
        }
    })
    .catch(error => {
        console.error('Error creating article:', error);
        alert('Failed to create article. Please try again.');
        
        // Reset button state
        submitButton.textContent = originalText;
        submitButton.disabled = false;
    });
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
            saveIndicator.style.cssText = 'position:fixed;top:10px;right:10px;background:#28a745;color:white;padding:5px 10px;border-radius:3px;z-index:1000;';
            document.body.appendChild(saveIndicator);
            
            setTimeout(() => {
                if (document.body.contains(saveIndicator)) {
                    document.body.removeChild(saveIndicator);
                }
            }, 2000);
        }, 2000); // Auto-save after 2 seconds of inactivity
    });
}

/**
 * Helper function to format time ago
 * @param {Date} date - The date to format
 * @returns {string} - Formatted time string
 */
function formatTimeAgo(date) {
    const now = new Date();
    const diffInMinutes = Math.floor((now - date) / (1000 * 60));
    
    if (diffInMinutes < 1) return 'just now';
    if (diffInMinutes === 1) return '1 minute ago';
    if (diffInMinutes < 60) return `${diffInMinutes} minutes ago`;
    
    const diffInHours = Math.floor(diffInMinutes / 60);
    if (diffInHours === 1) return '1 hour ago';
    if (diffInHours < 24) return `${diffInHours} hours ago`;
    
    return date.toLocaleDateString();
}
