// File: static/js/wiki-editor/utils/dom-utils.js
/**
 * DOM Utilities for Wiki Editor
 * 
 * This file contains utility functions for DOM manipulation in the editor.
 */

/**
 * Add line numbers to the textarea
 * @param {HTMLElement} textarea - The textarea element
 */
export function addLineNumbers(textarea) {
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
 * Create a dialog element
 * @param {string} id - The dialog ID
 * @param {string} className - Additional class name for the dialog
 * @param {string} content - HTML content for the dialog
 * @returns {HTMLElement} The created dialog element
 */
export function createDialog(id, className, content) {
    // Check if dialog already exists
    let dialog = document.getElementById(id);
    if (dialog) return dialog;
    
    // Create new dialog
    dialog = document.createElement('div');
    dialog.id = id;
    dialog.className = 'wiki-dialog ' + (className || '');
    dialog.innerHTML = content;
    
    // Add to document
    document.body.appendChild(dialog);
    
    return dialog;
}

/**
 * Show a dialog
 * @param {HTMLElement|string} dialog - Dialog element or dialog ID
 */
export function showDialog(dialog) {
    if (typeof dialog === 'string') {
        dialog = document.getElementById(dialog);
    }
    
    if (dialog) {
        dialog.style.display = 'block';
        
        // Handle outside clicks (one-time event)
        const handleOutsideClick = function(event) {
            if (event.target === dialog) {
                dialog.style.display = 'none';
                document.removeEventListener('click', handleOutsideClick);
            }
        };
        
        // Add outside click handler with delay to avoid immediate closure
        setTimeout(() => {
            document.addEventListener('click', handleOutsideClick);
        }, 100);
        
        // Focus the first input if present
        const firstInput = dialog.querySelector('input, textarea, select');
        if (firstInput) {
            firstInput.focus();
        }
    }
}

/**
 * Hide a dialog
 * @param {HTMLElement|string} dialog - Dialog element or dialog ID
 */
export function hideDialog(dialog) {
    if (typeof dialog === 'string') {
        dialog = document.getElementById(dialog);
    }
    
    if (dialog) {
        dialog.style.display = 'none';
    }
}

/**
 * Create a button
 * @param {string} text - Button text
 * @param {string} className - Button CSS class
 * @param {Function} onClick - Click handler
 * @returns {HTMLElement} The created button
 */
export function createButton(text, className, onClick) {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = className || '';
    button.textContent = text;
    
    if (onClick) {
        button.addEventListener('click', onClick);
    }
    
    return button;
}

/**
 * Show an alert message
 * @param {string} message - Message to display
 * @param {string} type - Message type: 'error', 'success', 'info'
 * @param {number} duration - Duration in milliseconds, 0 for no auto-hide
 */
export function showMessage(message, type = 'info', duration = 3000) {
    // Create or get message container
    let container = document.getElementById('wiki-editor-messages');
    if (!container) {
        container = document.createElement('div');
        container.id = 'wiki-editor-messages';
        container.className = 'wiki-editor-message-container';
        document.body.appendChild(container);
    }
    
    // Create message element
    const messageEl = document.createElement('div');
    messageEl.className = `wiki-editor-message wiki-editor-message-${type}`;
    messageEl.textContent = message;
    
    // Add close button
    const closeBtn = document.createElement('span');
    closeBtn.className = 'wiki-editor-message-close';
    closeBtn.innerHTML = '&times;';
    closeBtn.addEventListener('click', () => {
        container.removeChild(messageEl);
    });
    
    messageEl.appendChild(closeBtn);
    container.appendChild(messageEl);
    
    // Auto-hide after duration if specified
    if (duration > 0) {
        setTimeout(() => {
            if (messageEl.parentNode === container) {
                container.removeChild(messageEl);
            }
        }, duration);
    }
}
