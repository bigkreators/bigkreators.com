// File: static/js/wiki-editor/components/search-replace-dialog.js
/**
 * Search and Replace Dialog Component for Wiki Editor
 * 
 * This file contains the dialog for text search and replacement functionality.
 */

import { escapeRegExp } from '../utils/text-utils.js';
import { createDialog, showDialog, hideDialog } from '../utils/dom-utils.js';

/**
 * Create search and replace dialog
 * @returns {HTMLElement} The dialog element
 */
export function createSearchReplaceDialog() {
    const dialogId = 'search-replace-dialog';
    const existingDialog = document.getElementById(dialogId);
    if (existingDialog) return existingDialog;
    
    const dialogContent = `
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
    
    return createDialog(dialogId, 'wiki-search-replace-dialog', dialogContent);
}

/**
 * Open search and replace dialog
 * @param {HTMLElement} textarea - The textarea element
 * @returns {HTMLElement} The dialog element
 */
export function openSearchReplaceDialog(textarea) {
    const dialog = createSearchReplaceDialog();
    
    // Get the selected text for search field
    const selectedText = textarea.value.substring(textarea.selectionStart, textarea.selectionEnd);
    if (selectedText) {
        dialog.querySelector('#search-text').value = selectedText;
    }
    
    // Setup search and replace functionality
    setupSearchReplaceDialog(dialog, textarea);
    
    // Show dialog
    showDialog(dialog);
    
    // Focus the search text input
    dialog.querySelector('#search-text').focus();
    
    return dialog;
}

/**
 * Set up search and replace dialog functionality
 * @param {HTMLElement} dialog - The dialog element
 * @param {HTMLElement} textarea - The textarea element
 */
function setupSearchReplaceDialog(dialog, textarea) {
    // Clone buttons to remove existing event listeners
    const closeButtons = dialog.querySelectorAll('.close-dialog, #close-dialog-btn');
    closeButtons.forEach(btn => {
        const newBtn = btn.cloneNode(true);
        btn.parentNode.replaceChild(newBtn, btn);
        
        newBtn.addEventListener('click', () => {
            hideDialog(dialog);
        });
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
        const caseSensitive = dialog.querySelector('#search-case-sensitive').checked;
        const wholeWord = dialog.querySelector('#search-whole-word').checked;
        
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
        
        const caseSensitive = dialog.querySelector('#search-case-sensitive').checked;
        const wholeWord = dialog.querySelector('#search-whole-word').checked;
        
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
        const caseSensitive = dialog.querySelector('#search-case-sensitive').checked;
        const wholeWord = dialog.querySelector('#search-whole-word').checked;
        
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
        
        // Trigger input event to update line numbers and changes
        textarea.dispatchEvent(new Event('input'));
    });
}

export default {
    createSearchReplaceDialog,
    openSearchReplaceDialog
};
