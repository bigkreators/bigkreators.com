/**
 * Link Handler for Wiki Editor
 * 
 * This file contains functions for handling links in the wiki editor.
 */

import { insertWikiMarkup } from './text-utils.js';

/**
 * Open link dialog
 * @param {HTMLElement} textarea - The textarea element
 */
export function openLinkDialog(textarea) {
    // Create dialog
    const dialog = document.createElement('div');
    dialog.className = 'wiki-dialog wiki-link-dialog';
    
    dialog.innerHTML = `
        <div class="wiki-dialog-content">
            <span class="close-dialog">&times;</span>
            <h3>Insert Link</h3>
            <div class="form-group">
                <label for="link-target">Link Target:</label>
                <input type="text" id="link-target" placeholder="Page name or URL">
            </div>
            <div class="form-group">
                <label for="link-text">Link Text (optional):</label>
                <input type="text" id="link-text" placeholder="Display text (leave empty to use target)">
            </div>
            <div class="link-type-options">
                <label>
                    <input type="radio" name="link-type" value="internal" checked>
                    Internal Wiki Link
                </label>
                <label>
                    <input type="radio" name="link-type" value="external">
                    External URL
                </label>
            </div>
            <div class="dialog-actions">
                <button type="button" id="insert-link-btn">Insert Link</button>
                <button type="button" id="cancel-link-btn">Cancel</button>
            </div>
        </div>
    `;
    
    document.body.appendChild(dialog);
    
    // Handle selected text
    const selectedText = textarea.value.substring(textarea.selectionStart, textarea.selectionEnd);
    if (selectedText) {
        // Check if the selected text looks like a URL
        if (selectedText.startsWith('http://') || selectedText.startsWith('https://') || selectedText.startsWith('www.')) {
            document.getElementById('link-target').value = selectedText;
            document.querySelector('input[name="link-type"][value="external"]').checked = true;
        } else {
            document.getElementById('link-text').value = selectedText;
        }
    }
    
    // Add event listeners
    const closeButton = dialog.querySelector('.close-dialog');
    closeButton.addEventListener('click', () => {
        dialog.remove();
    });
    
    const cancelButton = document.getElementById('cancel-link-btn');
    cancelButton.addEventListener('click', () => {
        dialog.remove();
    });
    
    const insertButton = document.getElementById('insert-link-btn');
    insertButton.addEventListener('click', () => {
        const target = document.getElementById('link-target').value.trim();
        const text = document.getElementById('link-text').value.trim();
        const isExternal = document.querySelector('input[name="link-type"]:checked').value === 'external';
        
        if (!target) {
            alert('Please enter a link target.');
            return;
        }
        
        let linkMarkup = '';
        
        if (isExternal) {
            // External link format: [URL display text]
            linkMarkup = text ? `[${target} ${text}]` : `[${target}]`;
        } else {
            // Internal link format: [[Page name|display text]]
            linkMarkup = text ? `[[${target}|${text}]]` : `[[${target}]]`;
        }
        
        insertWikiMarkup(textarea, linkMarkup);
        dialog.remove();
    });
    
    // Show dialog
    dialog.style.display = 'block';
    
    // Focus the first input
    document.getElementById('link-target').focus();
    
    // Close on outside click
    window.addEventListener('click', (event) => {
        if (event.target === dialog) {
            dialog.remove();
        }
    });
}

/**
 * Remove wiki links from selected text
 * @param {HTMLElement} textarea - The textarea element
 */
export function removeWikiLinks(textarea) {
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const selectedText = textarea.value.substring(start, end);
    
    // Remove internal wiki links: [[Link|Text]] -> Text, [[Link]] -> Link
    let result = selectedText.replace(/\[\[(.*?)\|(.*?)\]\]/g, '$2');
    result = result.replace(/\[\[(.*?)\]\]/g, '$1');
    
    // Remove external links: [URL Text] -> Text, [URL] -> URL
    result = result.replace(/\[(https?:\/\/[^\s\]]+)\s+(.*?)\]/g, '$2');
    result = result.replace(/\[(https?:\/\/[^\s\]]+)\]/g, '$1');
    
    // Replace the selected text with the modified text
    textarea.value = textarea.value.substring(0, start) + result + textarea.value.substring(end);
    
    textarea.focus();
    textarea.setSelectionRange(start, start + result.length);
}

/**
 * Transform links for preview
 * @param {string} markup - Wiki markup containing links
 * @returns {string} HTML with transformed links
 */
export function transformLinks(markup) {
    let html = markup;
    
    // Handle internal links [[Page name]]
    html = html.replace(/\[\[(.*?)\]\]/g, '<a href="/articles/$1">$1</a>');
    
    // Handle internal links with display text [[Page name|Display text]]
    html = html.replace(/\[\[(.*?)\|(.*?)\]\]/g, '<a href="/articles/$1">$2</a>');
    
    // Handle external links [http://example.com Display text]
    html = html.replace(/\[(https?:\/\/[^\s\]]+)\s+(.*?)\]/g, '<a href="$1" target="_blank" rel="noopener">$2</a>');
    
    // Handle external links without display text [http://example.com]
    html = html.replace(/\[(https?:\/\/[^\s\]]+)\]/g, '<a href="$1" target="_blank" rel="noopener">$1</a>');
    
    return html;
}
