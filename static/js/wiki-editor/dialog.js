/**
 * Dialog Components for Wiki Editor
 * 
 * This file contains functions for creating and managing dialog components.
 */

import { insertWikiMarkup, wrapSelectedText, escapeRegExp } from './text-utils.js';

/**
 * Create heading dialog
 * @param {HTMLElement} textarea - The textarea element
 */
export function openHeadingDialog(textarea) {
    const headingLevels = [
        { level: 1, text: "= Heading 1 =" },
        { level: 2, text: "== Heading 2 ==" },
        { level: 3, text: "=== Heading 3 ===" },
        { level: 4, text: "==== Heading 4 ====" },
        { level: 5, text: "===== Heading 5 =====" },
        { level: 6, text: "====== Heading 6 ======" }
    ];
    
    // Create dialog
    const dialog = document.createElement('div');
    dialog.className = 'wiki-dialog wiki-heading-dialog';
    
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
    
    dialog.innerHTML = dialogContent;
    document.body.appendChild(dialog);
    
    // Add event listeners
    const closeButton = dialog.querySelector('.close-dialog');
    closeButton.addEventListener('click', () => {
        dialog.remove();
    });
    
    const headingOptions = dialog.querySelectorAll('.heading-option');
    headingOptions.forEach(option => {
        option.addEventListener('click', () => {
            const level = option.getAttribute('data-level');
            const prefix = '='.repeat(level) + ' ';
            const suffix = ' ' + '='.repeat(level);
            
            wrapSelectedText(textarea, prefix, suffix);
            dialog.remove();
        });
    });
    
    // Show dialog
    dialog.style.display = 'block';
    
    // Close on outside click
    window.addEventListener('click', (event) => {
        if (event.target === dialog) {
            dialog.remove();
        }
    });
    
    return dialog;
}

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
 * Create citation dialog
 */
export function createCitationDialog() {
    if (document.getElementById('citation-dialog')) return;
    
    const dialog = document.createElement('div');
    dialog.id = 'citation-dialog';
    dialog.className = 'wiki-dialog';
    
    dialog.innerHTML = `
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
    
    document.body.appendChild(dialog);
    
    // Set up event handlers
    const typeSelector = document.getElementById('citation-type');
    typeSelector.addEventListener('change', updateCitationFields);
    
    document.getElementById('cancel-citation-btn').addEventListener('click', () => {
        dialog.style.display = 'none';
    });
    
    dialog.querySelector('.close-dialog').addEventListener('click', () => {
        dialog.style.display = 'none';
    });
    
    // Initial update of fields
    updateCitationFields();
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
 */
export function openCitationDialog(textarea) {
    const dialog = document.getElementById('citation-dialog');
    if (!dialog) {
        createCitationDialog();
    }
    
    // Clear previous inputs
    const inputs = dialog.querySelectorAll('input[type="text"]');
    inputs.forEach(input => {
        input.value = '';
    });
    
    // Set up insert button event handler
    const insertButton = document.getElementById('insert-citation-btn');
    
    // Remove any existing event listeners
    const newInsertButton = insertButton.cloneNode(true);
    insertButton.parentNode.replaceChild(newInsertButton, insertButton);
    
    // Add new event listener
    newInsertButton.addEventListener('click', () => {
        generateCitation(textarea);
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

/**
 * Create reference dialog
 */
export function createReferenceDialog() {
    if (document.getElementById('reference-dialog')) return;
    
    const dialog = document.createElement('div');
    dialog.id = 'reference-dialog';
    dialog.className = 'wiki-dialog';
    
    dialog.innerHTML = `
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
    
    document.body.appendChild(dialog);
    
    // Set up event handlers
    document.getElementById('cancel-reference-btn').addEventListener('click', () => {
        dialog.style.display = 'none';
    });
    
    dialog.querySelector('.close-dialog').addEventListener('click', () => {
        dialog.style.display = 'none';
    });
}

/**
 * Open reference dialog
 * @param {HTMLElement} textarea - The textarea element
 */
export function openReferenceDialog(textarea) {
    const dialog = document.getElementById('reference-dialog');
    if (!dialog) {
        createReferenceDialog();
    }
    
    // Clear previous inputs
    document.getElementById('reference-content').value = '';
    document.getElementById('reference-name').value = '';
    
    // Set up insert buttons event handlers
    const insertButton = document.getElementById('insert-reference-btn');
    const reflistButton = document.getElementById('insert-reflist-btn');
    
    // Remove any existing event listeners
    const newInsertButton = insertButton.cloneNode(true);
    insertButton.parentNode.replaceChild(newInsertButton, insertButton);
    
    const newReflistButton = reflistButton.cloneNode(true);
    reflistButton.parentNode.replaceChild(newReflistButton, reflistButton);
    
    // Add new event listeners
    newInsertButton.addEventListener('click', () => {
        insertReference(textarea);
        dialog.style.display = 'none';
    });
    
    newReflistButton.addEventListener('click', () => {
        insertWikiMarkup(textarea, '\n<references />\n');
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
 * Create template gallery
 */
export function createTemplateGallery() {
    if (document.getElementById('template-gallery')) return;
    
    const dialog = document.createElement('div');
    dialog.id = 'template-gallery';
    dialog.className = 'wiki-dialog wiki-template-gallery';
    
    // Define common templates
    const templates = [
        { 
            name: 'Infobox',
            description: 'Information box for important details',
            markup: '{{Infobox\n| title = Title\n| image = example.jpg\n| caption = Image caption\n| label1 = Label\n| data1 = Data\n| label2 = Label\n| data2 = Data\n}}'
        },
        { 
            name: 'Quote',
            description: 'Block quote with attribution',
            markup: '{{Quote|text=The quoted text goes here.|author=Author Name|source=Source Title|year=Year}}'
        },
        { 
            name: 'Cite',
            description: 'Citation template',
            markup: '{{Cite web|title=Page Title|url=https://example.com|website=Website Name|access-date=2025-04-14}}'
        },
        { 
            name: 'Reflist',
            description: 'Reference list',
            markup: '{{Reflist}}'
        },
        { 
            name: 'Collapse',
            description: 'Collapsible section',
            markup: '{{Collapse|\nTitle=Section Title\n|content=The content goes here.\n}}'
        },
        { 
            name: 'Short description',
            description: 'Article short description',
            markup: '{{Short description|Brief description of the article}}'
        },
        { 
            name: 'TOC',
            description: 'Table of contents',
            markup: '{{TOC|limit=3|width=300px}}'
        },
        { 
            name: 'Notice',
            description: 'Notice box',
            markup: '{{Notice|type=note|This is a notice to readers.}}'
        },
        { 
            name: 'Math',
            description: 'Mathematical formula',
            markup: '{{Math|formula=E = mc^2}}'
        }
    ];
    
    let dialogContent = `
        <div class="wiki-dialog-content">
            <span class="close-dialog">&times;</span>
            <h3>Template Gallery</h3>
            <div class="template-search">
                <input type="text" id="template-search" placeholder="Search templates...">
            </div>
            <div class="template-grid">
    `;
    
    templates.forEach(template => {
        dialogContent += `
            <div class="template-item" data-template="${template.name.toLowerCase()}">
                <h4>${template.name}</h4>
                <p>${template.description}</p>
                <div class="template-preview">${template.markup.substring(0, 30)}...</div>
                <button class="template-insert" data-markup="${template.markup.replace(/"/g, '&quot;')}">Insert</button>
            </div>
        `;
    });
    
    dialogContent += `
            </div>
            <div class="custom-template">
                <h4>Custom Template</h4>
                <div class="form-group">
                    <label for="custom-template-name">Template Name:</label>
                    <input type="text" id="custom-template-name" placeholder="Template name">
                </div>
                <div class="form-group">
                    <label for="custom-template-params">Parameters (one per line, name=value):</label>
                    <textarea id="custom-template-params" rows="4" placeholder="param1=value1&#10;param2=value2"></textarea>
                </div>
                <button id="insert-custom-template">Insert Custom Template</button>
            </div>
        </div>
    `;
    
    dialog.innerHTML = dialogContent;
    document.body.appendChild(dialog);
    
    // Set up event handlers
    const closeButton = dialog.querySelector('.close-dialog');
    closeButton.addEventListener('click', () => {
        dialog.style.display = 'none';
    });
    
    // Add search functionality
    const searchInput = document.getElementById('template-search');
    searchInput.addEventListener('input', () => {
        const searchTerm = searchInput.value.toLowerCase();
        const templateItems = document.querySelectorAll('.template-item');
        
        templateItems.forEach(item => {
            const templateName = item.getAttribute('data-template');
            if (templateName.includes(searchTerm)) {
                item.style.display = 'block';
            } else {
                item.style.display = 'none';
            }
        });
    });
    
    // Close on outside click
    window.addEventListener('click', (event) => {
        if (event.target === dialog) {
            dialog.style.display = 'none';
        }
    });
}

/**
 * Open template gallery
 * @param {HTMLElement} textarea - The textarea element
 */
export function openTemplateGallery(textarea) {
    const dialog = document.getElementById('template-gallery');
    if (!dialog) {
        createTemplateGallery();
    }
    
    // Set up template insert buttons
    const insertButtons = dialog.querySelectorAll('.template-insert');
    insertButtons.forEach(button => {
        // Remove any existing event listeners
        const newButton = button.cloneNode(true);
        button.parentNode.replaceChild(newButton, button);
        
        // Add new event listener
        newButton.addEventListener('click', () => {
            const markup = newButton.getAttribute('data-markup');
            insertWikiMarkup(textarea, markup);
            dialog.style.display = 'none';
        });
    });
    
    // Set up custom template insert button
    const customInsertButton = document.getElementById('insert-custom-template');
    const newCustomButton = customInsertButton.cloneNode(true);
