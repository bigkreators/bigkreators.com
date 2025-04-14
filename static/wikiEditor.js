/**
 * Enhanced Wiki Editor Implementation for Kryptopedia
 * 
 * This file implements a Wikipedia-like editor for article content,
 * replacing the Summernote WYSIWYG editor with wiki markup functionality.
 * Includes additional features from Summernote where applicable.
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize wiki editor on appropriate pages
    const editForms = [
        'create-article-form',
        'edit-article-form',
        'propose-edit-form',
        'talk-page-form',
        'quick-edit-form'
    ];
    
    editForms.forEach(formId => {
        const form = document.getElementById(formId);
        if (form) {
            initializeWikiEditor(form);
        }
    });
});

/**
 * Initialize the Wiki Editor on a form
 * @param {HTMLElement} form - The form element containing the editor
 */
function initializeWikiEditor(form) {
    // Find the content textarea
    const contentTextarea = form.querySelector('#article-content');
    if (!contentTextarea) return;
    
    // If Summernote is initialized, destroy it
    if (typeof $ !== 'undefined' && $.fn.summernote) {
        try {
            $(contentTextarea).summernote('destroy');
        } catch (e) {
            console.error('Error destroying Summernote:', e);
        }
    }
    
    // Create the editor toolbar
    const toolbar = createEditorToolbar();
    
    // Create editor container and insert it before the textarea
    const editorContainer = document.createElement('div');
    editorContainer.className = 'wiki-editor-container';
    contentTextarea.parentNode.insertBefore(editorContainer, contentTextarea);
    
    // Move textarea into the container
    editorContainer.appendChild(toolbar);
    editorContainer.appendChild(contentTextarea);
    
    // Add line numbering to textarea
    addLineNumbers(contentTextarea);
    
    // Add the preview area after the editor container (hidden initially)
    const previewArea = document.createElement('div');
    previewArea.className = 'wiki-preview-area';
    previewArea.style.display = 'none';
    editorContainer.parentNode.insertBefore(previewArea, editorContainer.nextSibling);
    
    // Set up the form submission handler to transform the content
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Transform the article content by adding the short description
        transformContent(form);
        
        // Submit the form
        const event = new Event('wiki-editor-submit', {
            bubbles: true,
            cancelable: true
        });
        
        const shouldProceed = form.dispatchEvent(event);
        if (shouldProceed) {
            // If using the original form submission logic
            const originalSubmit = form.getAttribute('data-original-submit');
            if (originalSubmit && window[originalSubmit]) {
                window[originalSubmit]();
            } else {
                form.submit();
            }
        }
    });
    
    // Add show preview button to form actions
    addPreviewButton(form);
    
    // Style the cancel button
    styleCancelButton(form);
    
    // Set up event handlers for toolbar buttons
    setupToolbarHandlers(toolbar, contentTextarea, previewArea);
    
    // Add keyboard shortcuts
    addKeyboardShortcuts(contentTextarea);
    
    // Add the citation and reference dialogs
    createCitationDialog();
    createReferenceDialog();
    
    // Add the table dialog
    createTableDialog();
    
    // Add the template gallery dialog
    createTemplateGallery();
    
    // Create search and replace dialog (once)
    createSearchReplaceDialog();
}

/**
 * Create the editor toolbar with Wikipedia-like buttons
 * @returns {HTMLElement} The toolbar element
 */
function createEditorToolbar() {
    const toolbar = document.createElement('div');
    toolbar.className = 'wiki-editor-toolbar';
    
    // Define toolbar buttons by groups
    const buttonGroups = [
        // Insert group
        [
            { icon: 'file-image', title: 'Insert file/image', action: 'insertFile' },
            { icon: 'template', title: 'Insert template', action: 'insertTemplate' },
            { icon: 'table', title: 'Insert table', action: 'insertTable' },
            { icon: 'math', title: 'Insert math formula', action: 'insertMath' },
            { icon: 'code', title: 'Insert code block', action: 'insertCode' }
        ],
        // Format group
        [
            { icon: 'bold', title: 'Bold (Ctrl+B)', action: 'bold' },
            { icon: 'italic', title: 'Italic (Ctrl+I)', action: 'italic' },
            { icon: 'underline', title: 'Underline (Ctrl+U)', action: 'underline' },
            { icon: 'strikethrough', title: 'Strikethrough', action: 'strikethrough' },
            { icon: 'superscript', title: 'Superscript', action: 'superscript' },
            { icon: 'subscript', title: 'Subscript', action: 'subscript' }
        ],
        // Paragraph group
        [
            { icon: 'heading', title: 'Heading', action: 'heading' },
            { icon: 'list-ul', title: 'Bulleted list', action: 'bulletList' },
            { icon: 'list-ol', title: 'Numbered list', action: 'numberedList' },
            { icon: 'indent', title: 'Indent', action: 'indent' },
            { icon: 'outdent', title: 'Outdent', action: 'outdent' },
            { icon: 'align-left', title: 'Align left', action: 'alignLeft' },
            { icon: 'align-center', title: 'Align center', action: 'alignCenter' },
            { icon: 'align-right', title: 'Align right', action: 'alignRight' }
        ],
        // Links and references group
        [
            { icon: 'link', title: 'Insert link (Ctrl+K)', action: 'insertLink' },
            { icon: 'unlink', title: 'Remove link', action: 'removeLink' },
            { icon: 'citation', title: 'Insert citation', action: 'insertCitation' },
            { icon: 'reference', title: 'Insert reference', action: 'insertReference' }
        ],
        // Utility group
        [
            { icon: 'search', title: 'Search and replace (Ctrl+F)', action: 'searchReplace' },
            { icon: 'undo', title: 'Undo (Ctrl+Z)', action: 'undo' },
            { icon: 'redo', title: 'Redo (Ctrl+Y)', action: 'redo' },
            { icon: 'preview', title: 'Preview (Ctrl+P)', action: 'preview' }
        ]
    ];
    
    // Add buttons to toolbar in groups
    buttonGroups.forEach((group, groupIndex) => {
        const groupDiv = document.createElement('div');
        groupDiv.className = 'wiki-toolbar-group';
        
        group.forEach(button => {
            const btnElement = document.createElement('button');
            btnElement.type = 'button';
            btnElement.className = 'wiki-toolbar-btn';
            btnElement.title = button.title;
            btnElement.setAttribute('data-action', button.action);
            
            // Create icon
            const iconSpan = document.createElement('span');
            iconSpan.className = `wiki-icon wiki-icon-${button.icon}`;
            btnElement.appendChild(iconSpan);
            
            groupDiv.appendChild(btnElement);
        });
        
        toolbar.appendChild(groupDiv);
        
        // Add separator between groups (except after the last group)
        if (groupIndex < buttonGroups.length - 1) {
            const separator = document.createElement('div');
            separator.className = 'wiki-toolbar-separator';
            toolbar.appendChild(separator);
        }
    });
    
    return toolbar;
}

/**
 * Add line numbers to the textarea
 * @param {HTMLElement} textarea - The textarea element
 */
function addLineNumbers(textarea) {
    // Create line numbers container
    const lineNumbers = document.createElement('div');
    lineNumbers.className = 'wiki-editor-line-numbers';
    textarea.parentNode.insertBefore(lineNumbers, textarea);
    
    // Update line numbers on input, scroll and resize
    const updateLineNumbers = () => {
        const lines = textarea.value.split('\n').length;
        const height = textarea.clientHeight;
        const lineHeight = parseFloat(getComputedStyle(textarea).lineHeight);
        const paddingTop = parseFloat(getComputedStyle(textarea).paddingTop);
        
        let html = '';
        for (let i = 1; i <= lines; i++) {
            html += `<div>${i}</div>`;
        }
        
        lineNumbers.innerHTML = html;
        lineNumbers.style.top = `${paddingTop}px`;
        
        // Sync scroll position
        lineNumbers.scrollTop = textarea.scrollTop;
    };
    
    textarea.addEventListener('input', updateLineNumbers);
    textarea.addEventListener('scroll', () => {
        lineNumbers.scrollTop = textarea.scrollTop;
    });
    window.addEventListener('resize', updateLineNumbers);
    
    // Initial update
    updateLineNumbers();
    
    // Add line number container to the wrapper
    const lineNumberWrapper = document.createElement('div');
    lineNumberWrapper.className = 'wiki-editor-line-wrapper';
    textarea.parentNode.insertBefore(lineNumberWrapper, lineNumbers);
    lineNumberWrapper.appendChild(lineNumbers);
    lineNumberWrapper.appendChild(textarea);
}

/**
 * Add preview button to form actions
 * @param {HTMLElement} form - The form element
 */
function addPreviewButton(form) {
    const formActions = form.querySelector('.form-actions');
    if (!formActions) return;
    
    // Check if preview button already exists
    if (formActions.querySelector('#preview-button')) return;
    
    // Create preview button
    const previewButton = document.createElement('button');
    previewButton.type = 'button';
    previewButton.id = 'preview-button';
    previewButton.className = 'preview-button';
    previewButton.textContent = 'Show Preview';
    
    // Insert before the cancel button (if it exists)
    const cancelButton = formActions.querySelector('.cancel-button');
    if (cancelButton) {
        formActions.insertBefore(previewButton, cancelButton);
    } else {
        formActions.appendChild(previewButton);
    }
    
    // Add click handler
    previewButton.addEventListener('click', function() {
        previewContent(form);
    });
}

/**
 * Style the cancel button
 * @param {HTMLElement} form - The form element
 */
function styleCancelButton(form) {
    const cancelButton = form.querySelector('.cancel-button');
    if (cancelButton) {
        // Ensure the button has the cancel-button class
        if (!cancelButton.classList.contains('cancel-button')) {
            cancelButton.classList.add('cancel-button');
        }
    }
}

/**
 * Set up event handlers for toolbar buttons
 * @param {HTMLElement} toolbar - The toolbar element
 * @param {HTMLElement} textarea - The content textarea
 * @param {HTMLElement} previewArea - The preview area element
 */
function setupToolbarHandlers(toolbar, textarea, previewArea) {
    const buttons = toolbar.querySelectorAll('.wiki-toolbar-btn');
    
    buttons.forEach(button => {
        button.addEventListener('click', function() {
            const action = this.getAttribute('data-action');
            
            switch(action) {
                case 'insertFile':
                    insertWikiMarkup(textarea, '[[File:image.jpg|thumb|Description]]');
                    break;
                case 'insertTemplate':
                    openTemplateGallery(textarea);
                    break;
                case 'insertTable':
                    openTableDialog(textarea);
                    break;
                case 'insertMath':
                    wrapSelectedText(textarea, '<math>', '</math>');
                    break;
                case 'insertCode':
                    wrapSelectedText(textarea, '<code>', '</code>');
                    break;
                case 'searchReplace':
                    openSearchReplaceDialog(textarea);
                    break;
                case 'superscript':
                    wrapSelectedText(textarea, '<sup>', '</sup>');
                    break;
                case 'subscript':
                    wrapSelectedText(textarea, '<sub>', '</sub>');
                    break;
                case 'bold':
                    wrapSelectedText(textarea, "'''", "'''");
                    break;
                case 'italic':
                    wrapSelectedText(textarea, "''", "''");
                    break;
                case 'underline':
                    wrapSelectedText(textarea, '<u>', '</u>');
                    break;
                case 'strikethrough':
                    wrapSelectedText(textarea, '<s>', '</s>');
                    break;
                case 'heading':
                    const headingDialog = openHeadingDialog(textarea);
                    break;
                case 'insertLink':
                    openLinkDialog(textarea);
                    break;
                case 'removeLink':
                    removeWikiLinks(textarea);
                    break;
                case 'bulletList':
                    prependToSelectedLines(textarea, '* ');
                    break;
                case 'numberedList':
                    prependToSelectedLines(textarea, '# ');
                    break;
                case 'indent':
                    prependToSelectedLines(textarea, ':');
                    break;
                case 'outdent':
                    removeIndent(textarea);
                    break;
                case 'alignLeft':
                    wrapSelectedText(textarea, '<div style="text-align:left">', '</div>');
                    break;
                case 'alignCenter':
                    wrapSelectedText(textarea, '<div style="text-align:center">', '</div>');
                    break;
                case 'alignRight':
                    wrapSelectedText(textarea, '<div style="text-align:right">', '</div>');
                    break;
                case 'insertCitation':
                    openCitationDialog(textarea);
                    break;
                case 'insertReference':
                    openReferenceDialog(textarea);
                    break;
                case 'undo':
                    textarea.focus();
                    document.execCommand('undo');
                    break;
                case 'redo':
                    textarea.focus();
                    document.execCommand('redo');
                    break;
                case 'preview':
                    previewContent(textarea.form);
                    break;
            }
        });
    });
}

/**
 * Add keyboard shortcuts
 * @param {HTMLElement} textarea - The textarea element
 */
function addKeyboardShortcuts(textarea) {
    textarea.addEventListener('keydown', function(e) {
        // Ctrl+B: Bold
        if (e.ctrlKey && e.key === 'b') {
            e.preventDefault();
            wrapSelectedText(textarea, "'''", "'''");
        }
        // Ctrl+I: Italic
        else if (e.ctrlKey && e.key === 'i') {
            e.preventDefault();
            wrapSelectedText(textarea, "''", "''");
        }
        // Ctrl+U: Underline
        else if (e.ctrlKey && e.key === 'u') {
            e.preventDefault();
            wrapSelectedText(textarea, '<u>', '</u>');
        }
        // Ctrl+K: Link
        else if (e.ctrlKey && e.key === 'k') {
            e.preventDefault();
            openLinkDialog(textarea);
        }
        // Ctrl+F: Search
        else if (e.ctrlKey && e.key === 'f') {
            e.preventDefault();
            openSearchReplaceDialog(textarea);
        }
        // Ctrl+P: Preview
        else if (e.ctrlKey && e.key === 'p') {
            e.preventDefault();
            previewContent(textarea.form);
        }
        // Tab: Insert tab or handle indentation
        else if (e.key === 'Tab') {
            e.preventDefault();
            
            const start = textarea.selectionStart;
            const end = textarea.selectionEnd;
            
            // If text is selected, indent/outdent selection
            if (start !== end) {
                if (e.shiftKey) {
                    removeIndent(textarea); // Outdent
                } else {
                    prependToSelectedLines(textarea, '  '); // Indent with 2 spaces
                }
            } else {
                // No selection, insert tab at cursor
                insertWikiMarkup(textarea, '  ');
            }
        }
    });
}

/**
 * Create heading dialog
 * @param {HTMLElement} textarea - The textarea element
 */
function openHeadingDialog(textarea) {
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
function openLinkDialog(textarea) {
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
function removeWikiLinks(textarea) {
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
 * Remove indentation from selected lines
 * @param {HTMLElement} textarea - The textarea element
 */
function removeIndent(textarea) {
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const selectedText = textarea.value.substring(start, end);
    
    // Split by newline and remove indent from each line
    const lines = selectedText.split('\n');
    const newLines = lines.map(line => {
        // Remove leading spaces, tabs, or wiki indentation character
        return line.replace(/^(\s+|:+)/, match => {
            // Remove one level of indentation
            if (match.startsWith(':')) {
                return match.substring(1);
            } else if (match.length > 1) {
                return match.substring(1);
            }
            return '';
        });
    });
    
    const newText = newLines.join('\n');
    
    // Replace the selected text with the modified text
    textarea.value = textarea.value.substring(0, start) + newText + textarea.value.substring(end);
    
    textarea.focus();
    textarea.setSelectionRange(start, start + newText.length);
}

/**
 * Create citation dialog
 */
function createCitationDialog() {
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
function openCitationDialog(textarea) {
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
function createReferenceDialog() {
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
function openReferenceDialog(textarea) {
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
function createTableDialog() {
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
function openTableDialog(textarea) {
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
function createTemplateGallery() {
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
function openTemplateGallery(textarea) {
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
    customInsertButton.parentNode.replaceChild(newCustomButton, customInsertButton);
    
    newCustomButton.addEventListener('click', () => {
        const templateName = document.getElementById('custom-template-name').value.trim();
        const paramsText = document.getElementById('custom-template-params').value.trim();
        
        if (!templateName) {
            alert('Please enter a template name');
            return;
        }
        
        let markup = `{{${templateName}`;
        
        if (paramsText) {
            const params = paramsText.split('\n');
            params.forEach(param => {
                if (param.trim()) {
                    markup += `|${param.trim()}`;
                }
            });
        }
        
        markup += '}}';
        
        insertWikiMarkup(textarea, markup);
        dialog.style.display = 'none';
    });
    
    // Clear search and reset display
    const searchInput = document.getElementById('template-search');
    searchInput.value = '';
    const templateItems = document.querySelectorAll('.template-item');
    templateItems.forEach(item => {
        item.style.display = 'block';
    });
    
    // Show dialog
    dialog.style.display = 'block';
    
    // Focus search input
    searchInput.focus();
}

/**
 * Create search and replace dialog
 */
function createSearchReplaceDialog() {
    if (document.getElementById('search-replace-dialog')) return;
    
    const dialog = document.createElement('div');
    dialog.id = 'search-replace-dialog';
    dialog.className = 'wiki-dialog';
    
    dialog.innerHTML = `
        <div class="wiki-dialog-content">
            <span class="close-dialog">&times;</span>
            <h3>Search and Replace</h3>
            <div class="form-group">
                <label for="search-text">Search for:</label>
                <input type="text" id="search-text">
            </div>
            <div class="form-group">
                <label for="replace-text">Replace with:</label>
                <input type="text" id="replace-text">
            </div>
            <div class="search-options">
                <label>
                    <input type="checkbox" id="search-case-sensitive">
                    Match case
                </label>
                <label>
                    <input type="checkbox" id="search-whole-word">
                    Whole word
                </label>
            </div>
            <div class="dialog-actions">
                <button type="button" id="find-next-btn">Find Next</button>
                <button type="button" id="replace-btn">Replace</button>
                <button type="button" id="replace-all-btn">Replace All</button>
                <button type="button" id="close-dialog-btn">Close</button>
            </div>
        </div>
    `;
    
    document.body.appendChild(dialog);
}

/**
 * Open search and replace dialog
 * @param {HTMLElement} textarea - The textarea element
 */
function openSearchReplaceDialog(textarea) {
    const dialog = document.getElementById('search-replace-dialog');
    if (!dialog) {
        createSearchReplaceDialog();
    }
    
    // Get the selected text
    const selectedText = textarea.value.substring(textarea.selectionStart, textarea.selectionEnd);
    if (selectedText) {
        document.getElementById('search-text').value = selectedText;
    }
    
    // Setup search and replace functionality
    setupSearchReplaceDialog(dialog, textarea);
    
    // Show dialog
    dialog.style.display = 'block';
    
    // Focus the search text input
    document.getElementById('search-text').focus();
}

/**
 * Set up search and replace dialog functionality
 * @param {HTMLElement} dialog - The dialog element
 * @param {HTMLElement} textarea - The textarea element
 */
function setupSearchReplaceDialog(dialog, textarea) {
    const closeButtons = dialog.querySelectorAll('.close-dialog, #close-dialog-btn');
    closeButtons.forEach(btn => {
        // Remove existing event listeners
        const newBtn = btn.cloneNode(true);
        btn.parentNode.replaceChild(newBtn, btn);
        
        // Add new event listener
        newBtn.addEventListener('click', () => {
            dialog.style.display = 'none';
        });
    });
    
    // Click outside to close
    window.addEventListener('click', function(event) {
        if (event.target === dialog) {
            dialog.style.display = 'none';
        }
    });
    
    // Find Next button
    const findNextBtn = dialog.querySelector('#find-next-btn');
    const newFindBtn = findNextBtn.cloneNode(true);
    findNextBtn.parentNode.replaceChild(newFindBtn, findNextBtn);
    
    let lastIndex = -1;
    
    newFindBtn.addEventListener('click', function() {
        const searchText = dialog.querySelector('#search-text').value;
        if (!searchText) return;
        
        const content = textarea.value;
        const caseSensitive = document.getElementById('search-case-sensitive').checked;
        const wholeWord = document.getElementById('search-whole-word').checked;
        
        let searchRegex;
        try {
            if (wholeWord) {
                searchRegex = new RegExp(`\\b${escapeRegExp(searchText)}\\b`, caseSensitive ? 'g' : 'gi');
            } else {
                searchRegex = new RegExp(escapeRegExp(searchText), caseSensitive ? 'g' : 'gi');
            }
        } catch (e) {
            alert('Invalid search pattern');
            return;
        }
        
        // Reset the lastIndex if we're at the end of the string
        if (lastIndex >= content.length) {
            lastIndex = -1;
        }
        
        // Start searching from lastIndex + 1
        searchRegex.lastIndex = lastIndex + 1;
        const match = searchRegex.exec(content);
        
        if (match) {
            lastIndex = match.index;
            textarea.focus();
            textarea.setSelectionRange(match.index, match.index + match[0].length);
        } else {
            // Start from beginning if not found
            lastIndex = -1;
            alert('No more occurrences found. Starting from the beginning next time.');
        }
    });
    
    // Replace button
    const replaceBtn = dialog.querySelector('#replace-btn');
    const newReplaceBtn = replaceBtn.cloneNode(true);
    replaceBtn.parentNode.replaceChild(newReplaceBtn, replaceBtn);
    
    newReplaceBtn.addEventListener('click', function() {
        const searchText = dialog.querySelector('#search-text').value;
        const replaceText = dialog.querySelector('#replace-text').value;
        if (!searchText) return;
        
        const start = textarea.selectionStart;
        const end = textarea.selectionEnd;
        const selectedText = textarea.value.substring(start, end);
        
        const caseSensitive = document.getElementById('search-case-sensitive').checked;
        const wholeWord = document.getElementById('search-whole-word').checked;
        
        let searchRegex;
        try {
            if (wholeWord) {
                searchRegex = new RegExp(`\\b${escapeRegExp(searchText)}\\b`, caseSensitive ? '' : 'i');
            } else {
                searchRegex = new RegExp(escapeRegExp(searchText), caseSensitive ? '' : 'i');
            }
        } catch (e) {
            alert('Invalid search pattern');
            return;
        }
        
        if (searchRegex.test(selectedText)) {
            // Replace current selection
            const newText = selectedText.replace(searchRegex, replaceText);
            textarea.value = textarea.value.substring(0, start) + 
                            newText + 
                            textarea.value.substring(end);
            
            textarea.focus();
            textarea.setSelectionRange(start, start + newText.length);
            
            // Update last index for next search
            lastIndex = start;
        } else {
            // Find next occurrence first
            newFindBtn.click();
        }
    });
    
    // Replace All button
    const replaceAllBtn = dialog.querySelector('#replace-all-btn');
    const newReplaceAllBtn = replaceAllBtn.cloneNode(true);
    replaceAllBtn.parentNode.replaceChild(newReplaceAllBtn, replaceAllBtn);
    
    newReplaceAllBtn.addEventListener('click', function() {
        const searchText = dialog.querySelector('#search-text').value;
        const replaceText = dialog.querySelector('#replace-text').value;
        if (!searchText) return;
        
        const content = textarea.value;
        const caseSensitive = document.getElementById('search-case-sensitive').checked;
        const wholeWord = document.getElementById('search-whole-word').checked;
        
        let searchRegex;
        try {
            if (wholeWord) {
                searchRegex = new RegExp(`\\b${escapeRegExp(searchText)}\\b`, caseSensitive ? 'g' : 'gi');
            } else {
                searchRegex = new RegExp(escapeRegExp(searchText), caseSensitive ? 'g' : 'gi');
            }
        } catch (e) {
            alert('Invalid search pattern');
            return;
        }
        
        const newContent = content.replace(searchRegex, replaceText);
        textarea.value = newContent;
        lastIndex = -1;
        
        // Count occurrences
        const count = (content.match(searchRegex) || []).length;
        alert(`Replaced ${count} occurrence(s).`);
    });
}

/**
 * Escape string for use in RegExp
 * @param {string} string - String to escape
 * @returns {string} Escaped string
 */
function escapeRegExp(string) {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

/**
 * Insert wiki markup at cursor position
 * @param {HTMLElement} textarea - The textarea element
 * @param {string} markup - The markup to insert
 */
function insertWikiMarkup(textarea, markup) {
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const text = textarea.value;
    const newText = text.substring(0, start) + markup + text.substring(end);
    
    textarea.value = newText;
    textarea.focus();
    textarea.setSelectionRange(start + markup.length, start + markup.length);
    
    // Trigger input event to update line numbers
    textarea.dispatchEvent(new Event('input'));
}

/**
 * Wrap selected text with markup
 * @param {HTMLElement} textarea - The textarea element
 * @param {string} before - Markup to insert before selected text
 * @param {string} after - Markup to insert after selected text
 */
function wrapSelectedText(textarea, before, after) {
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const selectedText = textarea.value.substring(start, end);
    const newText = textarea.value.substring(0, start) + 
                    before + selectedText + after + 
                    textarea.value.substring(end);
    
    textarea.value = newText;
    textarea.focus();
    textarea.setSelectionRange(start + before.length, start + before.length + selectedText.length);
    
    // Trigger input event to update line numbers
    textarea.dispatchEvent(new Event('input'));
}

/**
 * Prepend text to each selected line
 * @param {HTMLElement} textarea - The textarea element
 * @param {string} prefix - Text to prepend to each line
 */
function prependToSelectedLines(textarea, prefix) {
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const selectedText = textarea.value.substring(start, end);
    
    // Split by newline and prepend to each line
    const lines = selectedText.split('\n');
    const newText = lines.map(line => prefix + line).join('\n');
    
    // Replace the selected text with the modified text
    textarea.value = textarea.value.substring(0, start) + 
                     newText + 
                     textarea.value.substring(end);
    
    textarea.focus();
    textarea.setSelectionRange(start, start + newText.length);
    
    // Trigger input event to update line numbers
    textarea.dispatchEvent(new Event('input'));
}

/**
 * Transform the article content before submission
 * @param {HTMLElement} form - The form element containing the editor
 */
function transformContent(form) {
    const contentTextarea = form.querySelector('#article-content');
    const summaryTextarea = form.querySelector('#article-summary');
    
    if (!contentTextarea || !summaryTextarea) return;
    
    // Get content and summary
    let content = contentTextarea.value;
    const summary = summaryTextarea.value.trim();
    
    // Check if content already has a short description
    if (summary && !content.includes('{{Short description|')) {
        // Add short description at the beginning
        content = `{{Short description|${summary}}}\n\n${content}`;
        contentTextarea.value = content;
    }
}

/**
 * Preview the wiki content
 * @param {HTMLElement} form - The form containing the content
 */
function previewContent(form) {
    const contentTextarea = form.querySelector('#article-content');
    const summaryTextarea = form.querySelector('#article-summary');
    const previewArea = form.querySelector('.wiki-preview-area');
    
    if (!contentTextarea || !previewArea) return;
    
    // Get the content
    let content = contentTextarea.value;
    
    // Add the short description if available
    if (summaryTextarea && summaryTextarea.value) {
        const summary = summaryTextarea.value;
        // Check if the content already has a short description
        if (!content.includes('{{Short description|')) {
            content = `{{Short description|${summary}}}\n\n${content}`;
        }
    }
    
    // Toggle preview area visibility
    const isVisible = previewArea.style.display !== 'none';
    
    if (isVisible) {
        previewArea.style.display = 'none';
        const previewButton = document.getElementById('preview-button');
        if (previewButton) {
            previewButton.textContent = 'Show Preview';
        }
    } else {
        // Transform wiki markup to HTML
        const html = transformWikiMarkup(content);
        previewArea.innerHTML = `<h3>Preview:</h3><div class="wiki-preview-content">${html}</div>`;
        previewArea.style.display = 'block';
        const previewButton = document.getElementById('preview-button');
        if (previewButton) {
            previewButton.textContent = 'Hide Preview';
        }
    }
}

/**
 * Transform wiki markup to HTML
 * @param {string} markup - The wiki markup text
 * @returns {string} HTML representation of the markup
 */
/**
 * Transform wiki markup to HTML
 * @param {string} markup - The wiki markup text
 * @returns {string} HTML representation of the markup
 */
function transformWikiMarkup(markup) {
    // This is a simplified transformation
    // In a real implementation, you would send this to the server
    let html = markup;

    // Handle short description
    const shortDescRegex = /\{\{Short description\|(.*?)\}\}/g;
    html = html.replace(shortDescRegex, '<div class="short-description"><em>$1</em></div>');

    // Handle text formatting
    html = html.replace(/'''(.*?)'''/g, '<strong>$1</strong>');
    html = html.replace(/''(.*?)''/g, '<em>$1</em>');
    html = html.replace(/<u>(.*?)<\/u>/g, '<u>$1</u>');
    html = html.replace(/<s>(.*?)<\/s>/g, '<s>$1</s>');
    html = html.replace(/<sup>(.*?)<\/sup>/g, '<sup>$1</sup>');
    html = html.replace(/<sub>(.*?)<\/sub>/g, '<sub>$1</sub>');

    // Handle headings
    html = html.replace(/======\s*(.*?)\s*======/g, '<h6>$1</h6>');
    html = html.replace(/=====\s*(.*?)\s*=====/g, '<h5>$1</h5>');
    html = html.replace(/====\s*(.*?)\s*====/g, '<h4>$1</h4>');
    html = html.replace(/===\s*(.*?)\s*===/g, '<h3>$1</h3>');
    html = html.replace(/==\s*(.*?)\s*==/g, '<h2>$1</h2>');
    html = html.replace(/=\s*(.*?)\s*=/g, '<h1>$1</h1>');

    // Handle lists
    // Unordered lists
    html = html.replace(/^\*\s*(.*?)$/gm, '<li>$1</li>');
    html = html.replace(/(<li>.*?<\/li>(\n|$))+/g, '<ul>$&</ul>');

    // Ordered lists
    html = html.replace(/^#\s*(.*?)$/gm, '<li>$1</li>');
    html = html.replace(/(<li>.*?<\/li>(\n|$))+/g, '<ol>$&</ol>');

    // Handle links
    // Internal links [[Page name]]
    html = html.replace(/\[\[(.*?)\]\]/g, '<a href="/wiki/$1">$1</a>');
    // Internal links with display text [[Page name|Display text]]
    html = html.replace(/\[\[(.*?)\|(.*?)\]\]/g, '<a href="/wiki/$1">$2</a>');
    // External links [http://example.com Display text]
    html = html.replace(/\[(https?:\/\/[^\s\]]+)\s+(.*?)\]/g, '<a href="$1" target="_blank">$2</a>');
    // External links without display text [http://example.com]
    html = html.replace(/\[(https?:\/\/[^\s\]]+)\]/g, '<a href="$1" target="_blank">$1</a>');

    // Handle templates
    // Infobox
    const infoboxRegex = /\{\{Infobox(.*?)\}\}/gs;
    html = html.replace(infoboxRegex, (match, content) => {
        const lines = content.split(/\n\|/);
        let infoboxHTML = '<div class="infobox">';
        
        lines.forEach(line => {
            const parts = line.split('=').map(part => part.trim());
            if (parts.length >= 2) {
                const key = parts[0];
                const value = parts.slice(1).join('=');
                infoboxHTML += `<div class="infobox-row">
                    <div class="infobox-label">${key}</div>
                    <div class="infobox-value">${value}</div>
                </div>`;
            }
        });
        
        infoboxHTML += '</div>';
        return infoboxHTML;
    });

    // Handle images
    // [[File:Example.jpg|thumb|Caption text]]
    const imageRegex = /\[\[File:(.*?)\|(.*?)\]\]/g;
    html = html.replace(imageRegex, (match, filename, options) => {
        const optionParts = options.split('|');
        let imageClass = '';
        let caption = '';
        
        optionParts.forEach(part => {
            if (part === 'thumb' || part === 'thumbnail') {
                imageClass += ' thumbnail';
            } else if (part === 'center') {
                imageClass += ' center';
            } else if (part === 'right') {
                imageClass += ' right';
            } else if (part === 'left') {
                imageClass += ' left';
            } else if (part.startsWith('width=')) {
                const width = part.split('=')[1];
                imageClass += ` width-${width}`;
            } else {
                // Assume it's a caption
                caption = part;
            }
        });
        
        return `<figure class="image${imageClass}">
            <img src="/images/${filename}" alt="${caption}">
            ${caption ? `<figcaption>${caption}</figcaption>` : ''}
        </figure>`;
    });

    // Handle tables
    // Simple implementation, would need to be more complex for nested tables
    html = html.replace(/\{\|(.*?)\|\}/gs, (match, tableContent) => {
        let tableHTML = '<table>';
        const rows = tableContent.split(/\|-/);
        
        rows.forEach(row => {
            if (row.trim()) {
                tableHTML += '<tr>';
                const cells = row.split(/\|\s*/);
                
                cells.forEach(cell => {
                    if (cell.trim()) {
                        if (cell.startsWith('!')) {
                            tableHTML += `<th>${cell.substring(1).trim()}</th>`;
                        } else {
                            tableHTML += `<td>${cell.trim()}</td>`;
                        }
                    }
                });
                
                tableHTML += '</tr>';
            }
        });
        
        tableHTML += '</table>';
        return tableHTML;
    });

    // Handle reference tags
    html = html.replace(/<ref>(.*?)<\/ref>/g, '<sup class="reference">$1</sup>');
    html = html.replace(/<references\s*\/>/g, '<div class="references"></div>');

    // Handle line breaks and paragraphs
    html = html.replace(/\n\n+/g, '</p><p>');
    html = '<p>' + html + '</p>';
    html = html.replace(/<p>\s*<\/p>/g, ''); // Remove empty paragraphs

    return html;
}
