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
        generateTable(textarea);
        hideDialog(dialog);
    });
    
    // Show dialog
    showDialog(dialog);
    
    return dialog;
}

/**
 * Generate table based on dialog fields
 * @param {HTMLElement} textarea - The textarea element
 */
function generateTable(textarea) {
    const rows = parseInt(document.getElementById('table-rows').value);
    const columns = parseInt(document.getElementById('table-columns').value);
    const includeHeader = document.getElementById('table-header').checked;
    const caption = document.getElementById('table-caption').value.trim();
    const tableClass = document.getElementById('table-class').value;
    
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
