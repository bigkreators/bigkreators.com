/**
 * Line Numbers Component for Wiki Editor
 * 
 * This file handles the line numbers functionality for the wiki editor.
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
