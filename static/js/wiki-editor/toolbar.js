// File: static/js/wiki-editor/toolbar.js
/**
 * Self-Contained Toolbar Component for Wiki Editor
 * 
 * This file contains ALL necessary functions without external dependencies
 * to avoid import failures.
 */

/**
 * Create the editor toolbar with Wikipedia-like buttons
 * @returns {HTMLElement} The toolbar element
 */
export function createEditorToolbar() {
    console.log('Creating Wiki Editor toolbar (self-contained version)');
    const toolbar = document.createElement('div');
    toolbar.className = 'wiki-editor-toolbar';
    
    // Add inline styles to ensure visibility
    toolbar.style.cssText = `
        background-color: #f8f9fa !important;
        border: 1px solid #ddd !important;
        border-bottom: none !important;
        border-radius: 4px 4px 0 0 !important;
        padding: 8px 12px !important;
        display: flex !important;
        flex-wrap: wrap !important;
        gap: 8px !important;
        align-items: center !important;
        min-height: 50px !important;
        visibility: visible !important;
        opacity: 1 !important;
        position: relative !important;
        z-index: 100 !important;
        margin: 0 !important;
        box-sizing: border-box !important;
    `;
    
    // Define toolbar buttons by groups
    const buttonGroups = [
        // Format group
        [
            { icon: 'B', title: 'Bold (Ctrl+B)', action: 'bold' },
            { icon: 'I', title: 'Italic (Ctrl+I)', action: 'italic' },
            { icon: 'U', title: 'Underline (Ctrl+U)', action: 'underline' },
            { icon: 'S', title: 'Strikethrough', action: 'strikethrough' }
        ],
        // Lists group
        [
            { icon: '•', title: 'Bulleted list', action: 'bulletList' },
            { icon: '1.', title: 'Numbered list', action: 'numberedList' },
            { icon: '→', title: 'Indent', action: 'indent' },
            { icon: '←', title: 'Outdent', action: 'outdent' }
        ],
        // Insert group
        [
            { icon: '🔗', title: 'Insert link (Ctrl+K)', action: 'insertLink' },
            { icon: '⊞', title: 'Insert table', action: 'insertTable' },
            { icon: '<>', title: 'Insert code', action: 'insertCode' },
            { icon: 'H', title: 'Heading', action: 'heading' }
        ],
        // Utility group
        [
            { icon: '👁️', title: 'Preview (Ctrl+P)', action: 'preview' },
            { icon: '↶', title: 'Undo (Ctrl+Z)', action: 'undo' },
            { icon: '↷', title: 'Redo (Ctrl+Y)', action: 'redo' }
        ]
    ];
    
    // Add buttons to toolbar in groups
    buttonGroups.forEach((group, groupIndex) => {
        const groupDiv = document.createElement('div');
        groupDiv.className = 'wiki-toolbar-group';
        groupDiv.style.cssText = `
            display: flex !important;
            gap: 4px !important;
            align-items: center !important;
            border-right: ${groupIndex < buttonGroups.length - 1 ? '1px solid #ccc' : 'none'} !important;
            padding-right: ${groupIndex < buttonGroups.length - 1 ? '8px' : '0'} !important;
            margin-right: ${groupIndex < buttonGroups.length - 1 ? '4px' : '0'} !important;
        `;
        
        group.forEach(button => {
            // Create the button element
            const btnElement = document.createElement('button');
            btnElement.type = 'button';
            btnElement.className = 'wiki-toolbar-btn';
            btnElement.title = button.title;
            btnElement.setAttribute('data-action', button.action);
            btnElement.setAttribute('aria-label', button.title);
            btnElement.textContent = button.icon;
            
            // Force button styles
            btnElement.style.cssText = `
                background: none !important;
                border: 1px solid transparent !important;
                border-radius: 3px !important;
                padding: 6px 8px !important;
                cursor: pointer !important;
                font-size: 14px !important;
                font-weight: bold !important;
                color: #333 !important;
                transition: all 0.2s ease !important;
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                min-width: 32px !important;
                height: 32px !important;
                visibility: visible !important;
                opacity: 1 !important;
                position: relative !important;
                box-sizing: border-box !important;
                margin: 0 !important;
            `;
            
            // Add hover effects
            btnElement.addEventListener('mouseenter', () => {
                btnElement.style.backgroundColor = '#e9ecef';
                btnElement.style.borderColor = '#adb5bd';
            });
            
            btnElement.addEventListener('mouseleave', () => {
                btnElement.style.backgroundColor = 'transparent';
                btnElement.style.borderColor = 'transparent';
            });
            
            // Add the button to the group
            groupDiv.appendChild(btnElement);
        });
        
        toolbar.appendChild(groupDiv);
    });
    
    return toolbar;
}

/**
 * Set up toolbar button event handlers
 * @param {HTMLElement} toolbar - The toolbar element
 * @param {HTMLElement} textarea - The textarea element
 * @param {HTMLElement} previewArea - The preview area element
 */
export function setupToolbarHandlers(toolbar, textarea, previewArea) {
    console.log('Setting up toolbar handlers (self-contained version)');
    
    if (!toolbar || !textarea) {
        console.error('Missing toolbar or textarea');
        return;
    }
    
    const buttons = toolbar.querySelectorAll('.wiki-toolbar-btn');
    console.log(`Found ${buttons.length} buttons to set up handlers for`);
    
    buttons.forEach((button, index) => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            const action = this.getAttribute('data-action');
            console.log(`Button ${index + 1} clicked: ${action}`);
            
            try {
                switch(action) {
                    case 'bold':
                        wrapText(textarea, "'''", "'''");
                        break;
                    case 'italic':
                        wrapText(textarea, "''", "''");
                        break;
                    case 'underline':
                        wrapText(textarea, '<u>', '</u>');
                        break;
                    case 'strikethrough':
                        wrapText(textarea, '<s>', '</s>');
                        break;
                    case 'bulletList':
                        addListPrefix(textarea, '* ');
                        break;
                    case 'numberedList':
                        addListPrefix(textarea, '# ');
                        break;
                    case 'indent':
                        addListPrefix(textarea, ':');
                        break;
                    case 'outdent':
                        removeListPrefix(textarea);
                        break;
                    case 'insertLink':
                        const selectedText = getSelectedText(textarea);
                        if (selectedText) {
                            wrapText(textarea, '[[', ']]');
                        } else {
                            insertTextAtCursor(textarea, '[[Link text|Display text]]');
                        }
                        break;
                    case 'insertTable':
                        const tableMarkup = '\n{| class="wikitable"\n! Header 1\n! Header 2\n|-\n| Cell 1\n| Cell 2\n|-\n| Cell 3\n| Cell 4\n|}\n';
                        insertTextAtCursor(textarea, tableMarkup);
                        break;
                    case 'insertCode':
                        wrapText(textarea, '<code>', '</code>');
                        break;
                    case 'heading':
                        wrapText(textarea, '== ', ' ==');
                        break;
                    case 'preview':
                        alert('Preview functionality - integrate with your preview system');
                        break;
                    case 'undo':
                        document.execCommand('undo');
                        break;
                    case 'redo':
                        document.execCommand('redo');
                        break;
                    default:
                        console.warn('Unknown toolbar action:', action);
                }
                
                // Focus back to textarea
                setTimeout(() => textarea.focus(), 50);
                
            } catch (error) {
                console.error(`Error executing action '${action}':`, error);
            }
        });
    });
    
    console.log(`Successfully set up ${buttons.length} toolbar button handlers`);
}

// Self-contained utility functions (no external dependencies)

function insertTextAtCursor(textarea, text) {
    const start = textarea.selectionStart;
    textarea.value = textarea.value.substring(0, start) + text + textarea.value.substring(start);
    textarea.focus();
    textarea.setSelectionRange(start + text.length, start + text.length);
}

function wrapText(textarea, startTag, endTag) {
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const selectedText = textarea.value.substring(start, end);
    const replacement = startTag + selectedText + endTag;
    
    textarea.value = textarea.value.substring(0, start) + replacement + textarea.value.substring(end);
    textarea.focus();
    textarea.setSelectionRange(start + startTag.length, start + startTag.length + selectedText.length);
}

function getSelectedText(textarea) {
    return textarea.value.substring(textarea.selectionStart, textarea.selectionEnd);
}

function addListPrefix(textarea, prefix) {
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const selectedText = textarea.value.substring(start, end);
    
    if (selectedText.includes('\n') || selectedText === '') {
        // Multi-line or no selection - add prefix to lines
        const lines = selectedText ? selectedText.split('\n') : [''];
        const modifiedLines = lines.map(line => prefix + line);
        const replacement = modifiedLines.join('\n');
        
        textarea.value = textarea.value.substring(0, start) + replacement + textarea.value.substring(end);
        textarea.focus();
        textarea.setSelectionRange(start, start + replacement.length);
    } else {
        // Single line selection - just add prefix at start
        const replacement = prefix + selectedText;
        textarea.value = textarea.value.substring(0, start) + replacement + textarea.value.substring(end);
        textarea.focus();
        textarea.setSelectionRange(start, start + replacement.length);
    }
}

function removeListPrefix(textarea) {
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const selectedText = textarea.value.substring(start, end);
    const lines = selectedText ? selectedText.split('\n') : [''];
    
    const modifiedLines = lines.map(line => {
        if (line.startsWith(':')) return line.substring(1);
        if (line.startsWith('* ')) return line.substring(2);
        if (line.startsWith('# ')) return line.substring(2);
        if (line.startsWith('  ')) return line.substring(2);
        if (line.startsWith('\t')) return line.substring(1);
        return line;
    });
    
    const replacement = modifiedLines.join('\n');
    textarea.value = textarea.value.substring(0, start) + replacement + textarea.value.substring(end);
    textarea.focus();
    textarea.setSelectionRange(start, start + replacement.length);
}

/**
 * Remove wiki links from selected text
 * @param {HTMLElement} textarea - The textarea element
 */
export function removeWikiLinks(textarea) {
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

export default {
    createEditorToolbar,
    setupToolbarHandlers,
    removeWikiLinks
};
