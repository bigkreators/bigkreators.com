// File: static/js/wiki-editor/index.js (Updated)
/**
 * Wiki Editor Module
 * Provides wiki markup editing with toolbar and preview functionality
 */

import { parseWikiMarkup } from './utils/wiki-parser.js';
import { insertAtCursor, wrapSelection, getSelectedText } from './utils/text-utils.js';
import { addShortDescription } from './utils/content-utils.js';

/**
 * Initialize the wiki editor on a form
 * @param {HTMLElement} form - The form element containing the editor
 */
export function initializeWikiEditor(form) {
    console.log('Initializing Wiki Editor on form:', form.id);
    
    const container = form.querySelector('.wiki-editor-container');
    if (!container) {
        console.warn('Wiki editor container not found');
        return;
    }
    
    setupToolbar(form);
    setupPreview(form);
    setupAutoSave(form);
    
    console.log('Wiki Editor initialized successfully');
}

/**
 * Set up the wiki editor toolbar
 * @param {HTMLElement} form - The form element
 */
function setupToolbar(form) {
    const toolbarContainer = form.querySelector('.wiki-editor-toolbar');
    if (!toolbarContainer) return;
    
    // Create toolbar HTML
    toolbarContainer.innerHTML = `
        <div class="toolbar-section">
            <button type="button" class="toolbar-btn" data-action="bold" title="Bold">
                <span class="wiki-icon wiki-icon-bold"></span>
            </button>
            <button type="button" class="toolbar-btn" data-action="italic" title="Italic">
                <span class="wiki-icon wiki-icon-italic"></span>
            </button>
            <button type="button" class="toolbar-btn" data-action="underline" title="Underline">
                <span class="wiki-icon wiki-icon-underline"></span>
            </button>
            <button type="button" class="toolbar-btn" data-action="strikethrough" title="Strikethrough">
                <span class="wiki-icon wiki-icon-strikethrough"></span>
            </button>
        </div>
        
        <div class="toolbar-section">
            <button type="button" class="toolbar-btn" data-action="heading" title="Heading">H</button>
            <button type="button" class="toolbar-btn" data-action="link" title="Link">
                <span class="wiki-icon wiki-icon-link"></span>
            </button>
            <button type="button" class="toolbar-btn" data-action="list" title="List">
                <span class="wiki-icon wiki-icon-list"></span>
            </button>
            <button type="button" class="toolbar-btn" data-action="code" title="Code">
                <span class="wiki-icon wiki-icon-code"></span>
            </button>
        </div>
        
        <div class="toolbar-section">
            <button type="button" class="toolbar-btn" data-action="indent" title="Indent">
                <span class="wiki-icon wiki-icon-indent"></span>
            </button>
            <button type="button" class="toolbar-btn" data-action="outdent" title="Outdent">
                <span class="wiki-icon wiki-icon-outdent"></span>
            </button>
        </div>
    `;
    
    // Add event listeners
    const textarea = form.querySelector('#article-content');
    toolbarContainer.addEventListener('click', function(e) {
        const button = e.target.closest('.toolbar-btn');
        if (!button) return;
        
        e.preventDefault();
        const action = button.dataset.action;
        handleToolbarAction(action, textarea);
    });
}

/**
 * Handle toolbar button actions
 * @param {string} action - The action to perform
 * @param {HTMLTextAreaElement} textarea - The target textarea
 */
function handleToolbarAction(action, textarea) {
    if (!textarea) return;
    
    textarea.focus();
    
    switch (action) {
        case 'bold':
            wrapSelection(textarea, "'''", "'''");
            break;
        case 'italic':
            wrapSelection(textarea, "''", "''");
            break;
        case 'underline':
            wrapSelection(textarea, '<u>', '</u>');
            break;
        case 'strikethrough':
            wrapSelection(textarea, '<s>', '</s>');
            break;
        case 'heading':
            const selectedText = getSelectedText(textarea);
            const headingText = selectedText || 'Heading';
            wrapSelection(textarea, `== ${headingText} ==`, '');
            break;
        case 'link':
            const linkText = getSelectedText(textarea) || 'Link text';
            const linkUrl = prompt('Enter URL:') || 'https://example.com';
            wrapSelection(textarea, `[${linkUrl} ${linkText}]`, '');
            break;
        case 'list':
            wrapSelection(textarea, '* ', '');
            break;
        case 'code':
            wrapSelection(textarea, '<code>', '</code>');
            break;
        case 'indent':
            wrapSelection(textarea, ':', '');
            break;
        case 'outdent':
            // Remove leading colons from current line
            const pos = textarea.selectionStart;
            const lines = textarea.value.split('\n');
            let currentLineIndex = 0;
            let charCount = 0;
            
            for (let i = 0; i < lines.length; i++) {
                if (charCount + lines[i].length >= pos) {
                    currentLineIndex = i;
                    break;
                }
                charCount += lines[i].length + 1; // +1 for newline
            }
            
            if (lines[currentLineIndex].startsWith(':')) {
                lines[currentLineIndex] = lines[currentLineIndex].substring(1);
                textarea.value = lines.join('\n');
            }
            break;
    }
}

/**
 * Set up preview functionality
 * @param {HTMLElement} form - The form element
 */
function setupPreview(form) {
    const previewButton = form.querySelector('#preview-button');
    const previewArea = form.querySelector('.wiki-preview-area');
    const contentTextarea = form.querySelector('#article-content');
    
    if (!previewButton || !previewArea || !contentTextarea) return;
    
    let isPreviewMode = false;
    
    previewButton.addEventListener('click', function(e) {
        e.preventDefault();
        
        if (!isPreviewMode) {
            // Show preview
            showWikiPreview(contentTextarea.value, previewArea);
            previewArea.style.display = 'block';
            contentTextarea.style.display = 'none';
            previewButton.textContent = 'Hide Preview';
            isPreviewMode = true;
        } else {
            // Hide preview
            previewArea.style.display = 'none';
            contentTextarea.style.display = 'block';
            previewButton.textContent = 'Show Preview';
            isPreviewMode = false;
        }
    });
}

/**
 * Show wiki preview
 * @param {string} content - The wiki content to preview
 * @param {HTMLElement} previewArea - The preview container
 */
function showWikiPreview(content, previewArea) {
    if (!content.trim()) {
        previewArea.innerHTML = '<p><em>No content to preview</em></p>';
        return;
    }
    
    try {
        const parsedContent = parseWikiMarkup(content);
        previewArea.innerHTML = `
            <div class="preview-header">
                <strong>Preview:</strong>
            </div>
            <div class="preview-content">
                ${parsedContent}
            </div>
        `;
    } catch (error) {
        console.error('Error parsing wiki content:', error);
        previewArea.innerHTML = `
            <div class="preview-error">
                <strong>Preview Error:</strong> Could not parse wiki markup
            </div>
        `;
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
                // Only show autosave notice if content is different AND there's no content in the editor
                if (!contentTextarea.value.trim()) {
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
            }
        } catch (e) {
            console.error('Error parsing autosave data:', e);
            localStorage.removeItem(autosaveKey);
        }
    }
    
    // Set up autosave - REMOVED the visual indicator completely
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
            
            // Save to localStorage silently - no visual indicator
            localStorage.setItem(autosaveKey, JSON.stringify(data));
            
            // Log for debugging (can be removed in production)
            console.log('Content autosaved silently');
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
