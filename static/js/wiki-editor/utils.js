/**
 * General Utilities for Wiki Editor
 * 
 * This file contains general utility functions for the wiki editor.
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
 * Transform wiki markup to HTML
 * @param {string} markup - The wiki markup text
 * @returns {string} HTML representation of the markup
 */
export function transformWikiMarkup(markup) {
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

    // Handle reference tags
    html = html.replace(/<ref>(.*?)<\/ref>/g, '<sup class="reference">$1</sup>');
    html = html.replace(/<references\s*\/>/g, '<div class="references"></div>');

    // Handle line breaks and paragraphs
    html = html.replace(/\n\n+/g, '</p><p>');
    html = '<p>' + html + '</p>';
    html = html.replace(/<p>\s*<\/p>/g, ''); // Remove empty paragraphs

    return html;
}
