// File: static/js/wiki-editor/components/citation-dialog.js
/**
 * Citation Dialog Component for Wiki Editor
 * 
 * This file contains the dialog for inserting citations.
 */

import { insertWikiMarkup } from '../utils/text-utils.js';
import { createDialog, showDialog, hideDialog } from '../utils/dom-utils.js';

/**
 * Create citation dialog
 * @returns {HTMLElement} The dialog element
 */
export function createCitationDialog() {
    const dialogId = 'citation-dialog';
    const existingDialog = document.getElementById(dialogId);
    if (existingDialog) return existingDialog;
    
    const dialogContent = `
        <div class="wiki-dialog-content">
            <span class="close-dialog">&times;</span>
            <h3>Insert Citation</h3>
            <div class="citation-types">
                <select id="citation-type">
                    <option value="book">Book</option>
                    <option value="journal">Journal</option>
                    <option value="news">News</option>
                    <option value="web">Website</option>
                </select>
            </div>
            <div id="citation-fields"></div>
            <div class="dialog-actions">
                <button type="button" id="insert-citation-btn">Insert Citation</button>
                <button type="button" id="cancel-citation-btn">Cancel</button>
            </div>
        </div>
    `;
    
    const dialog = createDialog(dialogId, 'wiki-citation-dialog', dialogContent);
    
    // Set up event handlers
    const typeSelector = dialog.querySelector('#citation-type');
    typeSelector.addEventListener('change', updateCitationFields);
    
    // Initial update of fields
    updateCitationFields();
    
    return dialog;
}

/**
 * Update citation fields based on type
 */
function updateCitationFields() {
    const citationType = document.getElementById('citation-type').value;
    const fieldsContainer = document.getElementById('citation-fields');
    
    // Define fields for each citation type
    const fields = {
        book: [
            { name: 'title', label: 'Title', required: true },
            { name: 'author', label: 'Author', required: true },
            { name: 'publisher', label: 'Publisher', required: false },
            { name: 'year', label: 'Year', required: false },
            { name: 'isbn', label: 'ISBN', required: false },
            { name: 'pages', label: 'Pages', required: false }
        ],
        journal: [
            { name: 'title', label: 'Article Title', required: true },
            { name: 'author', label: 'Author', required: true },
            { name: 'journal', label: 'Journal Name', required: true },
            { name: 'volume', label: 'Volume', required: false },
            { name: 'issue', label: 'Issue', required: false },
            { name: 'year', label: 'Year', required: false },
            { name: 'pages', label: 'Pages', required: false },
            { name: 'doi', label: 'DOI', required: false }
        ],
        news: [
            { name: 'title', label: 'Article Title', required: true },
            { name: 'author', label: 'Author', required: false },
            { name: 'newspaper', label: 'Newspaper', required: true },
            { name: 'date', label: 'Date', required: false },
            { name: 'url', label: 'URL', required: false }
        ],
        web: [
            { name: 'title', label: 'Page Title', required: true },
            { name: 'author', label: 'Author', required: false },
            { name: 'website', label: 'Website Name', required: false },
            { name: 'url', label: 'URL', required: true },
            { name: 'date', label: 'Date Accessed', required: false }
        ]
    };
    
    // Generate HTML for fields
    let fieldsHtml = '';
    fields[citationType].forEach(field => {
        fieldsHtml += `
            <div class="form-group">
                <label for="citation-${field.name}">${field.label}${field.required ? ' *' : ''}:</label>
                <input type="text" id="citation-${field.name}" ${field.required ? 'required' : ''}>
            </div>
        `;
    });
    
    fieldsContainer.innerHTML = fieldsHtml;
}

/**
 * Open citation dialog
 * @param {HTMLElement} textarea - The textarea element
 * @returns {HTMLElement} The dialog element
 */
export function openCitationDialog(textarea) {
    const dialog = createCitationDialog();
    
    // Clear previous inputs
    const inputs = dialog.querySelectorAll('input[type="text"]');
    inputs.forEach(input => {
        input.value = '';
    });
    
    // Remove existing event listeners by cloning elements
    const closeButton = dialog.querySelector('.close-dialog');
    const newCloseButton = closeButton.cloneNode(true);
    closeButton.parentNode.replaceChild(newCloseButton, closeButton);
    
    const cancelButton = dialog.querySelector('#cancel-citation-btn');
    const newCancelButton = cancelButton.cloneNode(true);
    cancelButton.parentNode.replaceChild(newCancelButton, cancelButton);
    
    const insertButton = dialog.querySelector('#insert-citation-btn');
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
        generateCitation(textarea);
        hideDialog(dialog);
    });
    
    // Show dialog
    showDialog(dialog);
    
    return dialog;
}

/**
 * Generate citation based on dialog fields
 * @param {HTMLElement} textarea - The textarea element
 */
function generateCitation(textarea) {
    const citationType = document.getElementById('citation-type').value;
    
    // Get field values
    const fields = {};
    const fieldInputs = document.querySelectorAll('#citation-fields input');
    fieldInputs.forEach(input => {
        const fieldName = input.id.replace('citation-', '');
        fields[fieldName] = input.value.trim();
    });
    
    // Generate citation markup
    let citation = `{{cite ${citationType}`;
    
    for (const [key, value] of Object.entries(fields)) {
        if (value) {
            citation += `|${key}=${value}`;
        }
    }
    
    citation += '}}';
    
    // Insert citation
    insertWikiMarkup(textarea, citation);
}

export default {
    createCitationDialog,
    openCitationDialog
};
