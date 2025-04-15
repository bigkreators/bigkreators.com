/**
 * Table Handler for Wiki Editor
 * 
 * This file contains functions for managing tables in the wiki editor.
 */

import { insertWikiMarkup } from './text-utils.js';

/**
 * Create table dialog
 */
export function createTableDialog() {
    if (document.getElementById('table-dialog')) return;
    
    const dialog = document.createElement('div');
    dialog.id = 'table-dialog';
    dialog.className = 'wiki-dialog';
    
    dialog.innerHTML = `
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
    
    document.body.appendChild(dialog);
    
    // Set up event handlers
    document.getElementById('cancel-table-btn').addEventListener('click', () => {
        dialog.style.display = 'none';
    });
    
    dialog.querySelector('.close-dialog').addEventListener('click', () => {
        dialog.style.display = 'none';
    });
}

/**
 * Open table dialog
 * @param {HTMLElement} textarea - The textarea element
 */
export function openTableDialog(textarea) {
    const dialog = document.getElementById('table-dialog');
    if (!dialog) {
        createTableDialog();
    }
    
    // Set up insert button event handler
    const insertButton = document.getElementById('insert-table-btn');
    
    // Remove any existing event listeners
    const newInsertButton = insertButton.cloneNode(true);
    insertButton.parentNode.replaceChild(newInsertButton, insertButton);
    
    // Add new event listener
    newInsertButton.addEventListener('click', () => {
        generateTable(textarea);
        dialog.style.display = 'none';
    });
    
    // Show dialog
    dialog.style.display = 'block';
    
    // Close on outside click
    window.addEventListener('click', (event) => {
        if (event.target === dialog) {
            dialog.style.display = 'none';
        }
    });
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

/**
 * Transform wiki table markup to HTML for preview
 * @param {string} markup - Wiki markup containing tables
 * @returns {string} HTML with transformed tables
 */
export function transformTables(markup) {
    // Match table syntax {| ... |}
    return markup.replace(/\{\|(.*?)\|\}/gs, (match, tableContent) => {
        let tableHTML = '<table class="wiki-table">';
        
        // Extract caption if present
        const captionMatch = /\|\+(.*?)(?:\n|\|-|$)/s.exec(tableContent);
        if (captionMatch) {
            tableHTML += `<caption>${captionMatch[1].trim()}</caption>`;
            tableContent = tableContent.replace(captionMatch[0], '');
        }
        
        // Split into rows by |-
        const rows = tableContent.split(/\|-/);
        
        // Process each row
        rows.forEach((row, index) => {
            if (index === 0 && !row.trim()) return; // Skip empty first row
            
            tableHTML += '<tr>';
            
            // Find all header cells
            const headerCells = row.match(/\!(.*?)(?:\!|$)/gs);
            if (headerCells) {
                headerCells.forEach(cell => {
                    const content = cell.replace(/^\!/, '').trim();
                    if (content) {
                        tableHTML += `<th>${content}</th>`;
                    }
                });
            }
            
            // Find all data cells
            const dataCells = row.match(/\|(.*?)(?:\||$)/gs);
            if (dataCells) {
                dataCells.forEach(cell => {
                    const content = cell.replace(/^\|/, '').trim();
                    if (content) {
                        tableHTML += `<td>${content}</td>`;
                    }
                });
            }
            
            tableHTML += '</tr>';
        });
        
        tableHTML += '</table>';
        return tableHTML;
    });
}
