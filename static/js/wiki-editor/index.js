// File: static/js/wiki-editor/index.js
/**
 * Wiki Editor Public API
 * 
 * This file serves as the public API for the wiki editor,
 * exporting the main functionality for use by other modules.
 */

// Fix: Add type="module" to script tag when including this file
// Or ensure it's loaded with proper MIME type

// Import and re-export core functionality
const initializeWikiEditor = function(form) {
    console.log('Initializing Wiki Editor on form:', form.id || 'unnamed form');
    
    // Find the content textarea
    const contentTextarea = form.querySelector('#article-content');
    if (!contentTextarea) {
        console.error('Wiki Editor initialization failed: #article-content not found');
        return;
    }
    
    // Create toolbar if needed
    let editorContainer = contentTextarea.closest('.wiki-editor-container');
    if (!editorContainer) {
        // Wrap textarea in container
        editorContainer = document.createElement('div');
        editorContainer.className = 'wiki-editor-container';
        contentTextarea.parentNode.insertBefore(editorContainer, contentTextarea);
        editorContainer.appendChild(contentTextarea);
    }
    
    // Create toolbar if it doesn't exist
    let toolbar = editorContainer.querySelector('.wiki-editor-toolbar');
    if (!toolbar) {
        toolbar = document.createElement('div');
        toolbar.className = 'wiki-editor-toolbar';
        
        // Add common formatting buttons
        toolbar.innerHTML = `
            <div class="wiki-toolbar-group">
                <button type="button" class="wiki-toolbar-btn" title="Bold (Ctrl+B)" data-action="bold">
                    <span class="wiki-icon wiki-icon-bold"></span>
                </button>
                <button type="button" class="wiki-toolbar-btn" title="Italic (Ctrl+I)" data-action="italic">
                    <span class="wiki-icon wiki-icon-italic"></span>
                </button>
                <button type="button" class="wiki-toolbar-btn" title="Heading" data-action="heading">
                    <span class="wiki-icon wiki-icon-heading"></span>
                </button>
                <button type="button" class="wiki-toolbar-btn" title="Link (Ctrl+K)" data-action="link">
                    <span class="wiki-icon wiki-icon-link"></span>
                </button>
            </div>
            <div class="wiki-toolbar-group">
                <button type="button" class="wiki-toolbar-btn" title="Bulleted List" data-action="bulletList">
                    <span class="wiki-icon wiki-icon-list-ul"></span>
                </button>
                <button type="button" class="wiki-toolbar-btn" title="Numbered List" data-action="numberedList">
                    <span class="wiki-icon wiki-icon-list-ol"></span>
                </button>
            </div>
            <div class="wiki-toolbar-group">
                <button type="button" class="wiki-toolbar-btn" title="Preview" data-action="preview">
                    <span class="wiki-icon wiki-icon-preview"></span>
                </button>
            </div>
        `;
        
        editorContainer.insertBefore(toolbar, contentTextarea);
        
        // Set up basic event handlers for toolbar buttons
        setupBasicToolbarHandlers(toolbar, contentTextarea);
    }
    
    // Add line numbers
    addLineNumbers(contentTextarea);
    
    // Find or create preview area
    let previewArea = form.querySelector('.wiki-preview-area');
    if (!previewArea) {
        previewArea = document.createElement('div');
        previewArea.className = 'wiki-preview-area';
        previewArea.style.display = 'none';
        editorContainer.parentNode.insertBefore(previewArea, editorContainer.nextSibling);
    }
    
    // Set up preview button handler
    const previewButton = document.getElementById('preview-button');
    if (previewButton) {
        previewButton.addEventListener('click', function() {
            togglePreview(form, previewButton);
        });
    }
    
    console.log('Wiki Editor initialized successfully');
};

// Basic toolbar handlers
function setupBasicToolbarHandlers(toolbar, textarea) {
    toolbar.addEventListener('click', function(e) {
        const button = e.target.closest('.wiki-toolbar-btn');
        if (!button) return;
        
        const action = button.getAttribute('data-action');
        if (!action) return;
        
        e.preventDefault();
        
        switch (action) {
            case 'bold':
                wrapSelectedText(textarea, "'''", "'''");
                break;
            case 'italic':
                wrapSelectedText(textarea, "''", "''");
                break;
            case 'heading':
                const level = prompt('Heading level (1-6):', '2');
                const equals = '='.repeat(parseInt(level) || 2);
                wrapSelectedText(textarea, equals + ' ', ' ' + equals);
                break;
            case 'link':
                const linkText = textarea.value.substring(textarea.selectionStart, textarea.selectionEnd);
                const target = prompt('Link target:', linkText);
                if (target) {
                    wrapSelectedText(textarea, '[[' + target + (target !== linkText ? '|' : ''), ']]');
                }
                break;
            case 'bulletList':
                prependToLines(textarea, '* ');
                break;
            case 'numberedList':
                prependToLines(textarea, '# ');
                break;
            case 'preview':
                const form = textarea.closest('form');
                if (form) {
                    const previewBtn = form.querySelector('#preview-button');
                    if (previewBtn) {
                        previewBtn.click();
                    } else {
                        togglePreview(form);
                    }
                }
                break;
        }
    });
}

// Helper functions
function wrapSelectedText(textarea, before, after) {
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const selectedText = textarea.value.substring(start, end);
    const replacement = before + selectedText + after;
    
    textarea.value = textarea.value.substring(0, start) + replacement + textarea.value.substring(end);
    textarea.focus();
    textarea.setSelectionRange(start + before.length, start + before.length + selectedText.length);
}

function prependToLines(textarea, prefix) {
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const selectedText = textarea.value.substring(start, end);
    const lines = selectedText.split('\n');
    
    const newText = lines.map(line => prefix + line).join('\n');
    textarea.value = textarea.value.substring(0, start) + newText + textarea.value.substring(end);
    textarea.focus();
    textarea.setSelectionRange(start, start + newText.length);
}

function togglePreview(form, button) {
    const previewArea = form.querySelector('.wiki-preview-area');
    const textarea = form.querySelector('#article-content');
    if (!previewArea || !textarea) return;
    
    if (previewArea.style.display === 'none') {
        // Show preview
        const content = textarea.value;
        previewArea.innerHTML = '<div class="preview-loading">Loading preview...</div>';
        previewArea.style.display = 'block';
        
        // Simple client-side preview
        setTimeout(() => {
            let html = content;
            
            // Basic transformations
            html = html.replace(/'''(.*?)'''/g, '<strong>$1</strong>');
            html = html.replace(/''(.*?)''/g, '<em>$1</em>');
            html = html.replace(/====== (.*?) ======/g, '<h6>$1</h6>');
            html = html.replace(/===== (.*?) =====/g, '<h5>$1</h5>');
            html = html.replace(/==== (.*?) ====/g, '<h4>$1</h4>');
            html = html.replace(/=== (.*?) ===/g, '<h3>$1</h3>');
            html = html.replace(/== (.*?) ==/g, '<h2>$1</h2>');
            html = html.replace(/= (.*?) =/g, '<h1>$1</h1>');
            
            // Links
            html = html.replace(/\[\[(.*?)\|(.*?)\]\]/g, '<a href="/articles/$1">$2</a>');
            html = html.replace(/\[\[(.*?)\]\]/g, '<a href="/articles/$1">$1</a>');
            
            previewArea.innerHTML = `<h3>Preview:</h3><div class="wiki-preview-content">${html}</div>`;
            
            if (button) {
                button.textContent = 'Hide Preview';
            }
        }, 300);
    } else {
        // Hide preview
        previewArea.style.display = 'none';
        if (button) {
            button.textContent = 'Show Preview';
        }
    }
}

function addLineNumbers(textarea) {
    // Create line numbers container
    const lineNumbersContainer = document.createElement('div');
    lineNumbersContainer.className = 'wiki-editor-line-numbers';
    
    // Create wrapper
    const wrapper = document.createElement('div');
    wrapper.className = 'wiki-editor-wrapper';
    
    // Insert wrapper and move textarea
    textarea.parentNode.insertBefore(wrapper, textarea);
    wrapper.appendChild(lineNumbersContainer);
    wrapper.appendChild(textarea);
    
    // Update line numbers
    function updateLineNumbers() {
        const lines = textarea.value.split('\n');
        lineNumbersContainer.innerHTML = '';
        
        for (let i = 0; i < lines.length; i++) {
            const lineNumber = document.createElement('div');
            lineNumber.className = 'line-number';
            lineNumber.textContent = i + 1;
            lineNumbersContainer.appendChild(lineNumber);
        }
    }
    
    // Initial update
    updateLineNumbers();
    
    // Update on events
    textarea.addEventListener('input', updateLineNumbers);
    textarea.addEventListener('scroll', function() {
        lineNumbersContainer.scrollTop = textarea.scrollTop;
    });
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Find wiki editors
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        if (form.querySelector('#article-content')) {
            initializeWikiEditor(form);
        }
    });
});

// Export for use by other scripts
window.wikiEditor = {
    initialize: initializeWikiEditor
};
