// File: static/js/wiki-editor/components/image-dialog.js
/**
 * Image Dialog Component for Wiki Editor
 * 
 * This file contains the dialog for inserting images in wiki markup.
 */

import { insertWikiMarkup } from '../utils/text-utils.js';
import { createDialog, showDialog, hideDialog } from '../utils/dom-utils.js';

/**
 * Create image dialog
 * @returns {HTMLElement} The dialog element
 */
export function createImageDialog() {
    const dialogId = 'image-dialog';
    const existingDialog = document.getElementById(dialogId);
    if (existingDialog) return existingDialog;
    
    const dialogContent = `
        <div class="wiki-dialog-content">
            <span class="close-dialog">&times;</span>
            <h3>Insert Image</h3>
            <div class="form-group">
                <label for="image-filename">Image Filename:</label>
                <input type="text" id="image-filename" placeholder="example.jpg">
            </div>
            <div class="form-group">
                <label for="image-caption">Caption (optional):</label>
                <input type="text" id="image-caption" placeholder="Image description">
            </div>
            <div class="image-options">
                <div class="option-group">
                    <h4>Size</h4>
                    <label>
                        <input type="radio" name="image-size" value="thumb" checked>
                        Thumbnail
                    </label>
                    <label>
                        <input type="radio" name="image-size" value="full">
                        Full size
                    </label>
                    <div class="sub-option">
                        <label for="image-width">Width (optional):</label>
                        <input type="text" id="image-width" placeholder="e.g., 300px">
                    </div>
                </div>
                <div class="option-group">
                    <h4>Alignment</h4>
                    <label>
                        <input type="radio" name="image-align" value="none" checked>
                        None
                    </label>
                    <label>
                        <input type="radio" name="image-align" value="left">
                        Left
                    </label>
                    <label>
                        <input type="radio" name="image-align" value="center">
                        Center
                    </label>
                    <label>
                        <input type="radio" name="image-align" value="right">
                        Right
                    </label>
                </div>
            </div>
            <div class="dialog-actions">
                <button type="button" id="insert-image-btn">Insert Image</button>
                <button type="button" id="cancel-image-btn">Cancel</button>
            </div>
        </div>
    `;
    
    return createDialog(dialogId, 'wiki-image-dialog', dialogContent);
}

/**
 * Open image dialog
 * @param {HTMLElement} textarea - The textarea element
 * @returns {HTMLElement} The dialog element
 */
export function openImageDialog(textarea) {
    const dialog = createImageDialog();
    
    // Remove existing event listeners by cloning elements
    const closeButton = dialog.querySelector('.close-dialog');
    const newCloseButton = closeButton.cloneNode(true);
    closeButton.parentNode.replaceChild(newCloseButton, closeButton);
    
    const cancelButton = dialog.querySelector('#cancel-image-btn');
    const newCancelButton = cancelButton.cloneNode(true);
    cancelButton.parentNode.replaceChild(newCancelButton, cancelButton);
    
    const insertButton = dialog.querySelector('#insert-image-btn');
    const newInsertButton = insertButton.cloneNode(true);
    insertButton.parentNode.replaceChild(newInsertButton, insertButton);
    
    // Add event listeners
    newCloseButton.addEventListener('click', () => {
        hideDialog(dialog);
    });
    
    newCancelButton.addEventListener('click', () => {
        hideDialog(dialog);
    });
    
    newInsertButton.addEventListener('click', () => {
        const filename = dialog.querySelector('#image-filename').value.trim();
        const caption = dialog.querySelector('#image-caption').value.trim();
        const size = dialog.querySelector('input[name="image-size"]:checked').value;
        const align = dialog.querySelector('input[name="image-align"]:checked').value;
        const width = dialog.querySelector('#image-width').value.trim();
        
        if (!filename) {
            alert('Please enter an image filename.');
            return;
        }
        
        // Build image markup
        let imageMarkup = `[[File:${filename}`;
        
        if (size === 'thumb') {
            imageMarkup += '|thumb';
        }
        
        if (width) {
            imageMarkup += `|width=${width}`;
        }
        
        if (align !== 'none') {
            imageMarkup += `|${align}`;
        }
        
        if (caption) {
            imageMarkup += `|${caption}`;
        }
        
        imageMarkup += ']]';
        
        insertWikiMarkup(textarea, imageMarkup);
        hideDialog(dialog);
    });
    
    // Show dialog
    showDialog(dialog);
    
    // Focus the first input
    dialog.querySelector('#image-filename').focus();
    
    return dialog;
}

export default {
    createImageDialog,
    openImageDialog
};
