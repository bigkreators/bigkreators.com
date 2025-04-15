// File: static/js/wiki-editor/components/heading-dialog.js
/**
 * Heading Dialog Component for Wiki Editor
 * 
 * This file contains the dialog for inserting headings of different levels.
 */

import { wrapSelectedText } from '../utils/text-utils.js';
import { createDialog, showDialog, hideDialog } from '../utils/dom-utils.js';

/**
 * Create heading dialog
 * @returns {HTMLElement} The dialog element
 */
export function createHeadingDialog() {
    const dialogId = 'heading-dialog';
    const existingDialog = document.getElementById(dialogId);
    if (existingDialog) return existingDialog;
    
    const headingLevels = [
        { level: 1, text: "= Heading 1 =" },
        { level: 2, text: "== Heading 2 ==" },
        { level: 3, text: "=== Heading 3 ===" },
        { level: 4, text: "==== Heading 4 ====" },
        { level: 5, text: "===== Heading 5 =====" },
        { level: 6, text: "====== Heading 6 ======" }
    ];
    
    let dialogContent = `
        <div class="wiki-dialog-content">
            <span class="close-dialog">&times;</span>
            <h3>Insert Heading</h3>
            <div class="heading-options">
    `;
    
    headingLevels.forEach(heading => {
        dialogContent += `
            <div class="heading-option" data-level="${heading.level}">
                <div class="heading-preview">${heading.text}</div>
            </div>
        `;
    });
    
    dialogContent += `
            </div>
        </div>
    `;
    
    return createDialog(dialogId, 'wiki-heading-dialog', dialogContent);
}

/**
 * Open heading dialog
 * @param {HTMLElement} textarea - The textarea element
 * @returns {HTMLElement} The dialog element
 */
export function openHeadingDialog(textarea) {
    const dialog = createHeadingDialog();
    
    // Remove existing event listeners
    const closeButton = dialog.querySelector('.close-dialog');
    const newCloseButton = closeButton.cloneNode(true);
    closeButton.parentNode.replaceChild(newCloseButton, closeButton);
    
    const headingOptions = dialog.querySelectorAll('.heading-option');
    headingOptions.forEach(option => {
        const newOption = option.cloneNode(true);
        option.parentNode.replaceChild(newOption, option);
    });
    
    // Add event listeners
    newCloseButton.addEventListener('click', () => {
        hideDialog(dialog);
    });
    
    dialog.querySelectorAll('.heading-option').forEach(option => {
        option.addEventListener('click', () => {
            const level = option.getAttribute('data-level');
            const prefix = '='.repeat(level) + ' ';
            const suffix = ' ' + '='.repeat(level);
            
            wrapSelectedText(textarea, prefix, suffix);
            hideDialog(dialog);
        });
    });
    
    // Show dialog
    showDialog(dialog);
    
    return dialog;
}

export default {
    createHeadingDialog,
    openHeadingDialog
};
