// File: static/js/wiki-editor/keyboard.js
/**
 * Keyboard Shortcuts for Wiki Editor
 * 
 * This file contains keyboard shortcut functionality for the wiki editor.
 */

import { wrapSelectedText, insertWikiMarkup, prependToSelectedLines, removeIndent } from './utils/text-utils.js';
import { openLinkDialog } from './components/link-dialog.js';
import { openSearchReplaceDialog } from './components/search-replace-dialog.js';
import { showWikiPreview } from './enhanced-preview.js';

/**
 * Add keyboard shortcuts to the editor
 * @param {HTMLElement} textarea - The textarea element
 */
export function addKeyboardShortcuts(textarea) {
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
            if (textarea.form) {
                showWikiPreview(textarea.form);
            }
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

export default {
    addKeyboardShortcuts
};
