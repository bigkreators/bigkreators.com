// File: static/js/wiki-editor/utils/text-utils.js
/**
 * Text Manipulation Utilities for Wiki Editor
 * 
 * This file contains utility functions for manipulating text in the editor.
 */

/**
 * Insert wiki markup at cursor position
 * @param {HTMLElement} textarea - The textarea element
 * @param {string} markup - The markup to insert
 */
export function insertWikiMarkup(textarea, markup) {
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
export function wrapSelectedText(textarea, before, after) {
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
export function prependToSelectedLines(textarea, prefix) {
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
 * Remove indentation from selected lines
 * @param {HTMLElement} textarea - The textarea element
 */
export function removeIndent(textarea) {
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
 * Escape string for use in RegExp
 * @param {string} string - String to escape
 * @returns {string} Escaped string
 */
export function escapeRegExp(string) {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

/**
 * Escape HTML special characters
 * @param {string} html - String to escape
 * @returns {string} Escaped HTML string
 */
export function escapeHTML(html) {
    const div = document.createElement('div');
    div.textContent = html;
    return div.innerHTML;
}

/**
 * Unescape HTML special characters
 * @param {string} html - String to unescape
 * @returns {string} Unescaped HTML string
 */
export function unescapeHTML(html) {
    const div = document.createElement('div');
    div.innerHTML = html;
    return div.textContent;
}

/**
 * Get the selected text range info
 * @param {HTMLElement} textarea - The textarea element
 * @returns {Object} Object with start, end, and text properties
 */
export function getSelectedTextInfo(textarea) {
    return {
        start: textarea.selectionStart,
        end: textarea.selectionEnd,
        text: textarea.value.substring(textarea.selectionStart, textarea.selectionEnd)
    };
}
