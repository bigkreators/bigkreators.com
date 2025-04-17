// File: static/js/wiki-editor/components/table-dialog.js
/**
 * Table Dialog Component for Wiki Editor
 * 
 * This file contains the dialog for inserting wiki tables.
 */

import { insertWikiMarkup } from '../utils/text-utils.js';
import { createDialog, showDialog, hideDialog } from '../utils/dom-utils.js';

/**
 * Create table dialog
 * @returns {HTMLElement} The dialog element
 */
export function createTableDialog() {
    const dialogId = 'table-dialog';
    const existingDialog = document.getElementById(dialogId);
    if (existingDialog) return existingDialog;
    
    const dialogContent = `
        <div class="wiki-dialog-content">
            <span class="close-dialog">&times;</span>
            <h3>Insert Table</h3>
            <div class="form-group">
                <label for="table-rows">Rows:</label>
                <input type="number" id="table-rows" value="3" min="1" max="20">
            </div>
            <div class="form-group">
                <label for="table-columns">Columns:</label>
                <input type="number" id="table-columns" value="3" min="1" max="10">
            </div>
            <div class="form-group">
                <label for="table-header">Include Header Row:</label>
                <input type="checkbox" id="table-header" checked>
            </div>
            <div class="form-group">
                <label for="table-caption">Table Caption (optional):</label>
                <input type="text" id="table-caption">
            </div>
            <div class="form-group">
                <label for="table-class">Table Style:</label>
                <select id="table-class">
                    <option value="wikitable">Standard Wiki Table</option>
                    <option value="wikitable sortable">Sortable Wiki Table</option>
                    <option value="wikitable mw-collapsible">Collapsible Wiki Table</option>
                </select>
            </div>
            <div class="dialog-actions">
                <button type="button" id="insert-table-btn">Insert Table</button>
                <button type="button" id="cancel-table-btn">Cancel</button>
            </div>
        </div>
    `;
    
    return createDialog(dialogId, 'wiki-table-dialog', dialogContent);
}

/**
 * Open table dialog
 * @param {HTMLElement} textarea - The textarea element
 * @returns {HTMLElement} The dialog element
 */
export function openTableDialog(textarea) {
    const dialog = createTableDialog();
    
    // Remove existing event listeners by cloning elements
    const closeButton = dialog.querySelector('.close-dialog');
    const newCloseButton = closeButton.cloneNode(true);
    closeButton.parentNode.replaceChild(newCloseButton, closeButton);
    
    const cancelButton = dialog.querySelector('#cancel-table-btn');
    const newCancelButton = cancelButton.cloneNode(true);
    cancelButton.parentNode.replaceChild(newCancelButton, cancelButton);
    
    const insertButton = dialog.querySelector('#insert-table-btn');
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
        generateTable(textarea, dialog);
        hideDialog(dialog);
    });
    
    // Show dialog
    showDialog(dialog);
    
    // Focus the first input
    const firstInput = dialog.querySelector('#table-rows');
    if (firstInput) {
        firstInput.focus();
    }
    
    return dialog;
}

/**
 * Generate table based on dialog fields
 * @param {HTMLElement} textarea - The textarea element
 * @param {HTMLElement} dialog - The dialog element containing the form fields
 */
function generateTable(textarea, dialog) {
    // Get form elements directly from the dialog to ensure correct reference
    const rowsInput = dialog.querySelector('#table-rows');
    const columnsInput = dialog.querySelector('#table-columns');
    const headerCheckbox = dialog.querySelector('#table-header');
    const captionInput = dialog.querySelector('#table-caption');
    const classSelect = dialog.querySelector('#table-class');
    
    // Validate that all required inputs exist
    if (!rowsInput || !columnsInput || !headerCheckbox || !classSelect) {
        console.error('Table dialog: Missing required form fields');
        return;
    }
    
    const rows = parseInt(rowsInput.value) || 3;
    const columns = parseInt(columnsInput.value) || 3;
    const includeHeader = headerCheckbox.checked;
    const caption = captionInput ? captionInput.value.trim() : '';
    const tableClass = classSelect.value || 'wikitable';
    
    let tableMarkup = `{| class="${tableClass}"\n`;
    
    // Add caption if provided
    if (caption) {
        tableMarkup += `|+ ${caption}\n`;
    }
    
    // Create header row if requested
    if (includeHeader) {
        tableMarkup += '|-\n';
        for (let col = 0; col < columns; col++) {
            tableMarkup += `! Header ${col + 1} `;
            if (col < columns - 1) {
                tableMarkup += '!! ';
            }
        }
        tableMarkup += '\n';
    }
    
    // Create data rows
    for (let row = 0; row < (includeHeader ? rows - 1 : rows); row++) {
        tableMarkup += '|-\n';
        for (let col = 0; col < columns; col++) {
            tableMarkup += `| Cell ${row + 1}-${col + 1} `;
            if (col < columns - 1) {
                tableMarkup += '|| ';
            }
        }
        tableMarkup += '\n';
    }
    
    // Close table
    tableMarkup += '|}';
    
    // Insert table
    insertWikiMarkup(textarea, '\n' + tableMarkup + '\n');
}

export default {
    createTableDialog,
    openTableDialog
};
