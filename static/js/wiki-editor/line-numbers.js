// File: static/js/wiki-editor/line-numbers.js
/**
 * Line Numbers for Wiki Editor
 * 
 * This file adds line numbering functionality to the wiki editor
 * for better text positioning and reference.
 */

/**
 * Add line numbers to a textarea
 * @param {HTMLElement} textarea - The textarea element
 */
export function addLineNumbers(textarea) {
    if (!textarea) return;
    
    // Create line numbers element
    const lineNumbers = document.createElement('div');
    lineNumbers.className = 'wiki-editor-line-numbers';
    
    // Wrap textarea in container if not already done
    let editorContainer = textarea.closest('.wiki-editor-container');
    if (!editorContainer) {
        editorContainer = document.createElement('div');
        editorContainer.className = 'wiki-editor-container';
        textarea.parentNode.insertBefore(editorContainer, textarea);
        editorContainer.appendChild(textarea);
    }
    
    // Add the line numbers element before textarea
    const editorWrapper = document.createElement('div');
    editorWrapper.className = 'wiki-editor-wrapper';
    
    // Move textarea to wrapper
    textarea.parentNode.insertBefore(editorWrapper, textarea);
    editorWrapper.appendChild(lineNumbers);
    editorWrapper.appendChild(textarea);
    
    // Add necessary CSS
    addLineNumberStyles();
    
    // Add scroll synchronization
    syncScroll(textarea, lineNumbers);
    
    // Initial update
    updateLineNumbers(textarea, lineNumbers);
    
    // Update on input and other events
    textarea.addEventListener('input', function() {
        updateLineNumbers(textarea, lineNumbers);
    });
    
    textarea.addEventListener('keydown', function() {
        // Use setTimeout to update after key processing
        setTimeout(function() {
            updateLineNumbers(textarea, lineNumbers);
        }, 0);
    });
    
    textarea.addEventListener('scroll', function() {
        lineNumbers.scrollTop = textarea.scrollTop;
    });
    
    // Update on window resize
    window.addEventListener('resize', function() {
        updateLineNumbers(textarea, lineNumbers);
    });
}

/**
 * Update line numbers
 * @param {HTMLElement} textarea - The textarea element
 * @param {HTMLElement} lineNumbers - The line numbers element
 */
function updateLineNumbers(textarea, lineNumbers) {
    const lines = textarea.value.split('\n');
    const numbers = [];
    
    for (let i = 0; i < lines.length; i++) {
        numbers.push(i + 1);
    }
    
    lineNumbers.innerHTML = numbers.map(num => `<div class="line-number">${num}</div>`).join('');
    
    // Match textarea line height
    const lineHeight = parseInt(window.getComputedStyle(textarea).lineHeight);
    const lineNumberElements = lineNumbers.querySelectorAll('.line-number');
    
    for (const lineNum of lineNumberElements) {
        lineNum.style.height = `${lineHeight}px`;
    }
}

/**
 * Synchronize scrolling between textarea and line numbers
 * @param {HTMLElement} textarea - The textarea element
 * @param {HTMLElement} lineNumbers - The line numbers element
 */
function syncScroll(textarea, lineNumbers) {
    textarea.addEventListener('scroll', function() {
        lineNumbers.scrollTop = textarea.scrollTop;
    });
}

/**
 * Add CSS styles for line numbers
 */
function addLineNumberStyles() {
    if (document.getElementById('wiki-line-numbers-style')) return;
    
    const styleElement = document.createElement('style');
    styleElement.id = 'wiki-line-numbers-style';
    styleElement.textContent = `
        .wiki-editor-wrapper {
            display: flex;
            width: 100%;
            position: relative;
        }
        
        .wiki-editor-line-numbers {
            width: 40px;
            font-family: monospace;
            font-size: 14px;
            color: #999;
            text-align: right;
            padding: 10px 5px 10px 0;
            border-right: 1px solid #ddd;
            background-color: #f8f9fa;
            overflow: hidden;
            user-select: none;
        }
        
        .line-number {
            padding-right: 5px;
        }
        
        textarea#article-content {
            flex-grow: 1;
            padding-left: 10px;
            white-space: pre;
            overflow-wrap: normal;
            overflow-x: auto;
        }
    `;
    
    document.head.appendChild(styleElement);
}

export default {
    addLineNumbers
};
