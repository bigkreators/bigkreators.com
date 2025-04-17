// File: static/js/wiki-editor/toolbar.js
/**
 * Toolbar Component for Wiki Editor
 * 
 * This file handles creating and managing the toolbar for the wiki editor.
 */

import { insertWikiMarkup, wrapSelectedText, prependToSelectedLines, removeIndent } from './utils/text-utils.js';
import { openTableDialog } from './components/table-dialog.js';
import { openHeadingDialog } from './components/heading-dialog.js';
import { openLinkDialog } from './components/link-dialog.js';
import { openSearchReplaceDialog } from './components/search-replace-dialog.js';
import { openCitationDialog } from './components/citation-dialog.js';
import { openReferenceDialog } from './components/reference-dialog.js';
import { openImageDialog } from './components/image-dialog.js';
import { openTemplateGallery } from './components/template-gallery.js';
import { showWikiPreview } from './enhanced-preview.js';

/**
 * Create the editor toolbar with Wikipedia-like buttons
 * @returns {HTMLElement} The toolbar element
 */
export function createEditorToolbar() {
    console.log('Creating Wiki Editor toolbar');
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
            { icon: 'outdent', title: 'Outdent', action: 'outdent' }
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
            // The separator is now handled by CSS border-right on the groups
        }
    });
    
    return toolbar;
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

/**
 * Set up toolbar button event handlers
 * @param {HTMLElement} toolbar - The toolbar element
 * @param {HTMLElement} textarea - The textarea element
 * @param {HTMLElement} previewArea - The preview area element
 */
export function setupToolbarHandlers(toolbar, textarea, previewArea) {
    console.log('Setting up toolbar handlers for Wiki Editor');
    const buttons = toolbar.querySelectorAll('.wiki-toolbar-btn');
    
    buttons.forEach(button => {
        button.addEventListener('click', function() {
            const action = this.getAttribute('data-action');
            console.log('Toolbar button clicked:', action);
            
            try {
                switch(action) {
                    case 'insertFile':
                        openImageDialog(textarea);
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
                        openHeadingDialog(textarea);
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
                        if (textarea.form) {
                            showWikiPreview(textarea.form);
                        } else {
                            console.error('No form found for textarea');
                        }
                        break;
                    default:
                        console.warn('Unknown toolbar action:', action);
                }
            } catch (error) {
                console.error(`Error executing toolbar action '${action}':`, error);
            }
        });
    });
}

export default {
    createEditorToolbar,
    setupToolbarHandlers,
    removeWikiLinks
};
