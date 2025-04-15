// File: static/js/wiki-editor/components/link-dialog.js
/**
 * Link Dialog Component for Wiki Editor
 * 
 * This file contains the dialog for inserting wiki links.
 */

import { insertWikiMarkup } from '../utils/text-utils.js';
import { createDialog, showDialog, hideDialog } from '../utils/dom-utils.js';

/**
 * Create link dialog
 * @returns {HTMLElement} The dialog element
 */
export function createLinkDialog() {
    const dialogId = 'link-dialog';
    const existingDialog = document.getElementById(dialogId);
    if (existingDialog) return existingDialog;
    
    const dialogContent = `
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
    
    return createDialog(dialogId, 'wiki-link-dialog', dialogContent);
}

/**
 * Open link dialog
 * @param {HTMLElement} textarea - The textarea element
 * @returns {HTMLElement} The dialog element
 */
export function openLinkDialog(textarea) {
    const dialog = createLinkDialog();
    
    // Remove existing event listeners by cloning elements
    const closeButton = dialog.querySelector('.close-dialog');
    const newCloseButton = closeButton.cloneNode(true);
    closeButton.parentNode.replaceChild(newCloseButton, closeButton);
    
    const cancelButton = dialog.querySelector('#cancel-link-btn');
    const newCancelButton = cancelButton.cloneNode(true);
    cancelButton.parentNode.replaceChild(newCancelButton, cancelButton);
    
    const insertButton = dialog.querySelector('#insert-link-btn');
    const newInsertButton = insertButton.cloneNode(true);
    insertButton.parentNode.replaceChild(newInsertButton, insertButton);
    
    // Get the selected text for potential pre-filling
    const selectedText = textarea.value.substring(textarea.selectionStart, textarea.selectionEnd);
    
    // Add event listeners
    newCloseButton.addEventListener('click', () => {
        hideDialog(dialog);
    });
    
    newCancelButton.addEventListener('click', () => {
        hideDialog(dialog);
    });
    
    newInsertButton.addEventListener('click', () => {
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
        hideDialog(dialog);
    });
    
    // Pre-fill the dialog based on selected text
    if (selectedText) {
        // Check if the selected text looks like a URL
        if (selectedText.startsWith('http://') || selectedText.startsWith('https://') || selectedText.startsWith('www.')) {
            document.getElementById('link-target').value = selectedText;
            document.querySelector('input[name="link-type"][value="external"]').checked = true;
        } else {
            document.getElementById('link-text').value = selectedText;
        }
    }
    
    // Show dialog
    showDialog(dialog);
    
    // Focus the first input
    document.getElementById('link-target').focus();
    
    return dialog;
}

export default {
    createLinkDialog,
    openLinkDialog
};
