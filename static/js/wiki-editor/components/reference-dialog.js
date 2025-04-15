// File: static/js/wiki-editor/components/reference-dialog.js
/**
 * Reference Dialog Component for Wiki Editor
 * 
 * This file contains the dialog for inserting references.
 */

import { insertWikiMarkup } from '../utils/text-utils.js';
import { createDialog, showDialog, hideDialog } from '../utils/dom-utils.js';

/**
 * Create reference dialog
 * @returns {HTMLElement} The dialog element
 */
export function createReferenceDialog() {
    const dialogId = 'reference-dialog';
    const existingDialog = document.getElementById(dialogId);
    if (existingDialog) return existingDialog;
    
    const dialogContent = `
        <div class="wiki-dialog-content">
            <span class="close-dialog">&times;</span>
            <h3>Insert Reference</h3>
            <div class="form-group">
                <label for="reference-content">Reference Content:</label>
                <textarea id="reference-content" rows="6" placeholder="Enter the reference text here. You can include HTML and wiki markup."></textarea>
            </div>
            <div class="form-group">
                <label for="reference-name">Reference Name (optional):</label>
                <input type="text" id="reference-name" placeholder="For recurring references (e.g., 'smith2020')">
            </div>
            <div class="dialog-actions">
                <button type="button" id="insert-reference-btn">Insert Reference</button>
                <button type="button" id="insert-reflist-btn">Insert Reference List</button>
                <button type="button" id="cancel-reference-btn">Cancel</button>
            </div>
        </div>
    `;
    
    return createDialog(dialogId, 'wiki-reference-dialog', dialogContent);
}

/**
 * Open reference dialog
 * @param {HTMLElement} textarea - The textarea element
 * @returns {HTMLElement} The dialog element
 */
export function openReferenceDialog(textarea) {
    const dialog = createReferenceDialog();
    
    // Clear previous inputs
    dialog.querySelector('#reference-content').value = '';
    dialog.querySelector('#reference-name').value = '';
    
    // Remove existing event listeners by cloning elements
    const closeButton = dialog.querySelector('.close-dialog');
    const newCloseButton = closeButton.cloneNode(true);
    closeButton.parentNode.replaceChild(newCloseButton, closeButton);
    
    const cancelButton = dialog.querySelector('#cancel-reference-btn');
    const newCancelButton = cancelButton.cloneNode(true);
    cancelButton.parentNode.replaceChild(newCancelButton, cancelButton);
    
    const insertButton = dialog.querySelector('#insert-reference-btn');
    const newInsertButton = insertButton.cloneNode(true);
    insertButton.parentNode.replaceChild(newInsertButton, insertButton);
    
    const reflistButton = dialog.querySelector('#insert-reflist-btn');
    const newReflistButton = reflistButton.cloneNode(true);
    reflistButton.parentNode.replaceChild(newReflistButton, reflistButton);
    
    // Add event listeners
    newCloseButton.addEventListener('click', () => {
        hideDialog(dialog);
    });
    
    newCancelButton.addEventListener('click', () => {
        hideDialog(dialog);
    });
    
    newInsertButton.addEventListener('click', () => {
        insertReference(textarea);
        hideDialog(dialog);
    });
    
    newReflistButton.addEventListener('click', () => {
        insertWikiMarkup(textarea, '\n<references />\n');
        hideDialog(dialog);
    });
    
    // Show dialog
    showDialog(dialog);
    
    // Focus the content textarea
    dialog.querySelector('#reference-content').focus();
    
    return dialog;
}

/**
 * Insert reference based on dialog fields
 * @param {HTMLElement} textarea - The textarea element
 */
function insertReference(textarea) {
    const content = document.getElementById('reference-content').value.trim();
    const name = document.getElementById('reference-name').value.trim();
    
    if (!content) {
        alert('Please enter reference content');
        return;
    }
    
    let reference = '';
    
    if (name) {
        reference = `<ref name="${name}">${content}</ref>`;
    } else {
        reference = `<ref>${content}</ref>`;
    }
    
    insertWikiMarkup(textarea, reference);
}

export default {
    createReferenceDialog,
    openReferenceDialog
};
