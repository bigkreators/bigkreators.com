/**
 * Heading Handler for Wiki Editor
 * 
 * This file contains functions for managing headings and sections.
 */

import { wrapSelectedText } from './text-utils.js';

/**
 * Open heading dialog
 * @param {HTMLElement} textarea - The textarea element
 */
export function openHeadingDialog(textarea) {
    const headingLevels = [
        { level: 1, text: "= Heading 1 =" },
        { level: 2, text: "== Heading 2 ==" },
        { level: 3, text: "=== Heading 3 ===" },
        { level: 4, text: "==== Heading 4 ====" },
        { level: 5, text: "===== Heading 5 =====" },
        { level: 6, text: "====== Heading 6 ======" }
    ];
    
    // Create dialog
    const dialog = document.createElement('div');
    dialog.className = 'wiki-dialog wiki-heading-dialog';
    
    let dialogContent = `
        <div class="wiki-dialog-content">
            <span class="close-dialog">&times;</span>
            <h3>Insert Heading</h3>
            <div class="heading-options">
    `;
    
    headingLevels.forEach(heading => {
        dialogContent += `
            <div class="heading-option" data-level="${heading.level}">
                <div class="heading-preview">${heading.text}</div>
            </div>
        `;
    });
    
    dialogContent += `
            </div>
        </div>
    `;
    
    dialog.innerHTML = dialogContent;
    document.body.appendChild(dialog);
    
    // Add event listeners
    const closeButton = dialog.querySelector('.close-dialog');
    closeButton.addEventListener('click', () => {
        dialog.remove();
    });
    
    const headingOptions = dialog.querySelectorAll('.heading-option');
    headingOptions.forEach(option => {
        option.addEventListener('click', () => {
            const level = option.getAttribute('data-level');
            const prefix = '='.repeat(level) + ' ';
            const suffix = ' ' + '='.repeat(level);
            
            wrapSelectedText(textarea, prefix, suffix);
            dialog.remove();
        });
    });
    
    // Show dialog
    dialog.style.display = 'block';
    
    // Close on outside click
    window.addEventListener('click', (event) => {
        if (event.target === dialog) {
            dialog.remove();
        }
    });
    
    return dialog;
}

/**
 * Transform headings for preview
 * @param {string} markup - Wiki markup containing headings
 * @returns {string} HTML with transformed headings
 */
export function transformHeadings(markup) {
    let html = markup;
    
    // Handle headings
    html = html.replace(/======\s*(.*?)\s*======/g, '<h6>$1</h6>');
    html = html.replace(/=====\s*(.*?)\s*=====/g, '<h5>$1</h5>');
    html = html.replace(/====\s*(.*?)\s*====/g, '<h4>$1</h4>');
    html = html.replace(/===\s*(.*?)\s*===/g, '<h3>$1</h3>');
    html = html.replace(/==\s*(.*?)\s*==/g, '<h2>$1</h2>');
    html = html.replace(/=\s*(.*?)\s*=/g, '<h1>$1</h1>');
    
    return html;
}

/**
 * Extract all headings from wiki markup
 * @param {string} markup - Wiki markup content
 * @returns {Array<{level: number, text: string, id: string}>} Array of headings with level and text
 */
export function extractHeadings(markup) {
    const headings = [];
    const headingRegex = /^(=+)\s*(.+?)\s*\1/gm;
    
    let match;
    while ((match = headingRegex.exec(markup)) !== null) {
        const level = match[1].length; // Number of = characters
        const text = match[2].trim();
        const id = text.toLowerCase().replace(/[^\w]+/g, '-');
        
        headings.push({
            level,
            text,
            id
        });
    }
    
    return headings;
}

/**
 * Generate table of contents from headings
 * @param {Array<{level: number, text: string, id: string}>} headings - Extracted headings
 * @returns {string} HTML table of contents
 */
export function generateTableOfContents(headings) {
    if (headings.length === 0) {
        return '';
    }
    
    let toc = '<div class="wiki-toc">\n<h2>Contents</h2>\n<ol>';
    let currentLevel = 1;
    let count = [0, 0, 0, 0, 0, 0]; // Counter for each heading level
    
    headings.forEach(heading => {
        const level = heading.level;
        
        // Update counters
        count[level-1]++;
        for (let i = level; i < 6; i++) {
            count[i] = 0;
        }
        
        // Generate section number
        const sectionNumber = count.slice(0, level).filter(n => n > 0).join('.');
        
        // Handle level changes
        if (level > currentLevel) {
            // Need to open new sublists
            for (let i = 0; i < level - currentLevel; i++) {
                toc += '<ol>';
            }
        } else if (level < currentLevel) {
            // Need to close sublists
            for (let i = 0; i < currentLevel - level; i++) {
                toc += '</li></ol>';
            }
            toc += '</li>';
        } else {
            // Same level, close previous item
            toc += '</li>';
        }
        
        // Add this heading
        toc += `<li><a href="#${heading.id}">${sectionNumber} ${heading.text}</a>`;
        
        // Update current level
        currentLevel = level;
    });
    
    // Close any open lists
    for (let i = 0; i < currentLevel; i++) {
        toc += '</li></ol>';
    }
    
    toc += '</div>';
    return toc;
}
