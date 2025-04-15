/**
 * Search and Replace Functionality for Wiki Editor
 * 
 * This file contains functions for searching and replacing text
 * within the wiki editor.
 */

import { escapeRegExp } from './text-utils.js';

/**
 * Create search and replace dialog
 */
export function createSearchReplaceDialog() {
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
export function openSearchReplaceDialog(textarea) {
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
    
    // Close on outside click
    window.addEventListener('click', (event) => {
        if (event.target === dialog) {
            dialog.style.display = 'none';
        }
    });
}

/**
 * Set up search and replace dialog functionality
 * @param {HTMLElement} dialog - The dialog element
 * @param {HTMLElement} textarea - The textarea element
 */
export function setupSearchReplaceDialog(dialog, textarea) {
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
    
    // Find Next button
    const findNextBtn = dialog.querySelector('#find-next-btn');
    const newFindBtn = findNextBtn.cloneNode(true);
    findNextBtn.parentNode.replaceChild(newFindBtn, findNextBtn);
    
    let lastIndex = -1;
    
    newFindBtn.addEventListener('click', function() {
        const searchText = dialog.querySelector('#search-text').value;
        if (!searchText) return;
        
        findNext(textarea, searchText, lastIndex, {
            caseSensitive: document.getElementById('search-case-sensitive').checked,
            wholeWord: document.getElementById('search-whole-word').checked
        });
    });
    
    // Replace button
    const replaceBtn = dialog.querySelector('#replace-btn');
    const newReplaceBtn = replaceBtn.cloneNode(true);
    replaceBtn.parentNode.replaceChild(newReplaceBtn, replaceBtn);
    
    newReplaceBtn.addEventListener('click', function() {
        const searchText = dialog.querySelector('#search-text').value;
        const replaceText = dialog.querySelector('#replace-text').value;
        
        if (!searchText) return;
        
        replaceSelection(textarea, searchText, replaceText, {
            caseSensitive: document.getElementById('search-case-sensitive').checked,
            wholeWord: document.getElementById('search-whole-word').checked
        });
    });
    
    // Replace All button
    const replaceAllBtn = dialog.querySelector('#replace-all-btn');
    const newReplaceAllBtn = replaceAllBtn.cloneNode(true);
    replaceAllBtn.parentNode.replaceChild(newReplaceAllBtn, replaceAllBtn);
    
    newReplaceAllBtn.addEventListener('click', function() {
        const searchText = dialog.querySelector('#search-text').value;
        const replaceText = dialog.querySelector('#replace-text').value;
        
        if (!searchText) return;
        
        replaceAll(textarea, searchText, replaceText, {
            caseSensitive: document.getElementById('search-case-sensitive').checked,
            wholeWord: document.getElementById('search-whole-word').checked
        });
    });
}

/**
 * Find next occurrence of search text
 * @param {HTMLElement} textarea - The textarea element
 * @param {string} searchText - Text to find
 * @param {number} startIndex - Index to start search from
 * @param {Object} options - Search options
 * @returns {number} Index of the match, or -1 if not found
 */
export function findNext(textarea, searchText, startIndex = -1, options = {}) {
    const content = textarea.value;
    const caseSensitive = options.caseSensitive || false;
    const wholeWord = options.wholeWord || false;
    
    let searchRegex;
    try {
        let pattern = escapeRegExp(searchText);
        
        if (wholeWord) {
            pattern = `\\b${pattern}\\b`;
        }
        
        searchRegex = new RegExp(pattern, caseSensitive ? 'g' : 'gi');
    } catch (e) {
        alert('Invalid search pattern');
        return -1;
    }
    
    // Reset lastIndex if we're at the end of the string
    if (startIndex >= content.length) {
        startIndex = -1;
    }
    
    // Start searching from startIndex + 1
    searchRegex.lastIndex = startIndex + 1;
    const match = searchRegex.exec(content);
    
    if (match) {
        const matchIndex = match.index;
        textarea.focus();
        textarea.setSelectionRange(matchIndex, matchIndex + match[0].length);
        return matchIndex;
    } else {
        // Start from beginning if not found
        alert('No more occurrences found. Starting from the beginning next time.');
        return -1;
    }
}

/**
 * Replace the currently selected text if it matches search criteria
 * @param {HTMLElement} textarea - The textarea element
 * @param {string} searchText - Text to replace
 * @param {string} replaceText - Replacement text
 * @param {Object} options - Search options
 * @returns {boolean} Whether a replacement was made
 */
export function replaceSelection(textarea, searchText, replaceText, options = {}) {
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const selectedText = textarea.value.substring(start, end);
    
    const caseSensitive = options.caseSensitive || false;
    const wholeWord = options.wholeWord || false;
    
    let searchRegex;
    try {
        let pattern = escapeRegExp(searchText);
        
        if (wholeWord) {
            pattern = `\\b${pattern}\\b`;
        }
        
        searchRegex = new RegExp(pattern, caseSensitive ? '' : 'i');
    } catch (e) {
        alert('Invalid search pattern');
        return false;
    }
    
    if (searchRegex.test(selectedText)) {
        // Replace current selection
        const newText = selectedText.replace(searchRegex, replaceText);
        textarea.value = textarea.value.substring(0, start) + 
                        newText + 
                        textarea.value.substring(end);
        
        textarea.focus();
        textarea.setSelectionRange(start, start + newText.length);
        
        // Trigger input event to update any listeners
        textarea.dispatchEvent(new Event('input'));
        
        return true;
    } else {
        // Find next occurrence first
        findNext(textarea, searchText, start, options);
        return false;
    }
}

/**
 * Replace all occurrences of the search text
 * @param {HTMLElement} textarea - The textarea element
 * @param {string} searchText - Text to replace
 * @param {string} replaceText - Replacement text
 * @param {Object} options - Search options
 * @returns {number} Number of replacements made
 */
export function replaceAll(textarea, searchText, replaceText, options = {}) {
    const content = textarea.value;
    const caseSensitive = options.caseSensitive || false;
    const wholeWord = options.wholeWord || false;
    
    let searchRegex;
    try {
        let pattern = escapeRegExp(searchText);
        
        if (wholeWord) {
            pattern = `\\b${pattern}\\b`;
        }
        
        searchRegex = new RegExp(pattern, caseSensitive ? 'g' : 'gi');
    } catch (e) {
        alert('Invalid search pattern');
        return 0;
    }
    
    const newContent = content.replace(searchRegex, replaceText);
    textarea.value = newContent;
    
    // Trigger input event to update any listeners
    textarea.dispatchEvent(new Event('input'));
    
    // Count occurrences
    const count = (content.match(searchRegex) || []).length;
    alert(`Replaced ${count} occurrence(s).`);
    
    return count;
}
