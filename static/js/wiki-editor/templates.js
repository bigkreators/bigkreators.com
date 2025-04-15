/**
 * Templates Management for Wiki Editor
 * 
 * This file handles template creation, gallery, and insertion.
 */

import { insertWikiMarkup } from './text-utils.js';

/**
 * Common wiki templates definitions
 */
export const COMMON_TEMPLATES = [
    { 
        name: 'Infobox',
        description: 'Information box for important details',
        markup: '{{Infobox\n| title = Title\n| image = example.jpg\n| caption = Image caption\n| label1 = Label\n| data1 = Data\n| label2 = Label\n| data2 = Data\n}}'
    },
    { 
        name: 'Quote',
        description: 'Block quote with attribution',
        markup: '{{Quote|text=The quoted text goes here.|author=Author Name|source=Source Title|year=Year}}'
    },
    { 
        name: 'Cite Web',
        description: 'Citation for web sources',
        markup: '{{Cite web|title=Page Title|url=https://example.com|website=Website Name|access-date=2025-04-14}}'
    },
    { 
        name: 'Cite Book',
        description: 'Citation for books',
        markup: '{{Cite book|title=Book Title|author=Author Name|publisher=Publisher Name|year=2025|isbn=978-1234567890}}'
    },
    { 
        name: 'Cite Journal',
        description: 'Citation for journal articles',
        markup: '{{Cite journal|title=Article Title|author=Author Name|journal=Journal Name|volume=10|issue=2|year=2025|pages=45-67|doi=10.1234/example}}'
    },
    { 
        name: 'Reflist',
        description: 'Reference list',
        markup: '{{Reflist}}'
    },
    { 
        name: 'Collapse',
        description: 'Collapsible section',
        markup: '{{Collapse|\nTitle=Section Title\n|content=The content goes here.\n}}'
    },
    { 
        name: 'Short description',
        description: 'Article short description',
        markup: '{{Short description|Brief description of the article}}'
    },
    { 
        name: 'TOC',
        description: 'Table of contents',
        markup: '{{TOC|limit=3|width=300px}}'
    },
    { 
        name: 'Notice',
        description: 'Notice box',
        markup: '{{Notice|type=note|This is a notice to readers.}}'
    },
    { 
        name: 'Math',
        description: 'Mathematical formula',
        markup: '{{Math|formula=E = mc^2}}'
    },
    { 
        name: 'Gallery',
        description: 'Image gallery',
        markup: '{{Gallery|\nFile:image1.jpg|Caption 1\nFile:image2.jpg|Caption 2\nFile:image3.jpg|Caption 3\n}}'
    },
    { 
        name: 'Table start',
        description: 'Wiki table starter',
        markup: '{| class="wikitable"\n|+ Caption\n|-\n! Header 1 !! Header 2 !! Header 3\n|-\n| Cell 1 || Cell 2 || Cell 3\n|-\n| Cell 4 || Cell 5 || Cell 6\n|}'
    }
];

/**
 * Create template gallery dialog
 */
export function createTemplateGallery() {
    if (document.getElementById('template-gallery')) return;
    
    const dialog = document.createElement('div');
    dialog.id = 'template-gallery';
    dialog.className = 'wiki-dialog wiki-template-gallery';
    
    let dialogContent = `
        <div class="wiki-dialog-content">
            <span class="close-dialog">&times;</span>
            <h3>Template Gallery</h3>
            <div class="template-search">
                <input type="text" id="template-search" placeholder="Search templates...">
            </div>
            <div class="template-grid">
    `;
    
    COMMON_TEMPLATES.forEach(template => {
        dialogContent += `
            <div class="template-item" data-template="${template.name.toLowerCase()}">
                <h4>${template.name}</h4>
                <p>${template.description}</p>
                <div class="template-preview">${template.markup.substring(0, 30)}...</div>
                <button class="template-insert" data-markup="${escapeHTML(template.markup)}">Insert</button>
            </div>
        `;
    });
    
    dialogContent += `
            </div>
            <div class="custom-template">
                <h4>Custom Template</h4>
                <div class="form-group">
                    <label for="custom-template-name">Template Name:</label>
                    <input type="text" id="custom-template-name" placeholder="Template name">
                </div>
                <div class="form-group">
                    <label for="custom-template-params">Parameters (one per line, name=value):</label>
                    <textarea id="custom-template-params" rows="4" placeholder="param1=value1&#10;param2=value2"></textarea>
                </div>
                <button id="insert-custom-template">Insert Custom Template</button>
            </div>
        </div>
    `;
    
    dialog.innerHTML = dialogContent;
    document.body.appendChild(dialog);
    
    // Set up event handlers
    const closeButton = dialog.querySelector('.close-dialog');
    closeButton.addEventListener('click', () => {
        dialog.style.display = 'none';
    });
    
    // Add search functionality
    const searchInput = document.getElementById('template-search');
    searchInput.addEventListener('input', () => {
        const searchTerm = searchInput.value.toLowerCase();
        const templateItems = document.querySelectorAll('.template-item');
        
        templateItems.forEach(item => {
            const templateName = item.getAttribute('data-template');
            if (templateName.includes(searchTerm)) {
                item.style.display = 'block';
            } else {
                item.style.display = 'none';
            }
        });
    });
    
    // Close on outside click
    window.addEventListener('click', (event) => {
        if (event.target === dialog) {
            dialog.style.display = 'none';
        }
    });
}

/**
 * Open template gallery
 * @param {HTMLElement} textarea - The textarea element
 */
export function openTemplateGallery(textarea) {
    const dialog = document.getElementById('template-gallery');
    if (!dialog) {
        createTemplateGallery();
    }
    
    // Set up template insert buttons
    const insertButtons = dialog.querySelectorAll('.template-insert');
    insertButtons.forEach(button => {
        // Remove any existing event listeners
        const newButton = button.cloneNode(true);
        button.parentNode.replaceChild(newButton, button);
        
        // Add new event listener
        newButton.addEventListener('click', () => {
            const markup = unescapeHTML(newButton.getAttribute('data-markup'));
            insertWikiMarkup(textarea, markup);
            dialog.style.display = 'none';
        });
    });
    
    // Set up custom template insert button
    const customInsertButton = document.getElementById('insert-custom-template');
    const newCustomButton = customInsertButton.cloneNode(true);
    customInsertButton.parentNode.replaceChild(newCustomButton, customInsertButton);
    
    newCustomButton.addEventListener('click', () => {
        const templateName = document.getElementById('custom-template-name').value.trim();
        const paramsText = document.getElementById('custom-template-params').value.trim();
        
        if (!templateName) {
            alert('Please enter a template name');
            return;
        }
        
        let markup = `{{${templateName}`;
        
        if (paramsText) {
            const params = paramsText.split('\n');
            params.forEach(param => {
                if (param.trim()) {
                    markup += `|${param.trim()}`;
                }
            });
        }
        
        markup += '}}';
        
        insertWikiMarkup(textarea, markup);
        dialog.style.display = 'none';
    });
    
    // Clear search and reset display
    const searchInput = document.getElementById('template-search');
    searchInput.value = '';
    const templateItems = document.querySelectorAll('.template-item');
    templateItems.forEach(item => {
        item.style.display = 'block';
    });
    
    // Show dialog
    dialog.style.display = 'block';
    
    // Focus search input
    searchInput.focus();
}

/**
 * Create template from parameters
 * @param {string} templateName - Name of the template
 * @param {Object} params - Template parameters
 * @returns {string} Wiki markup for the template
 */
export function createTemplate(templateName, params) {
    let markup = `{{${templateName}`;
    
    // Add parameters
    for (const [key, value] of Object.entries(params)) {
        if (value !== undefined && value !== null && value !== '') {
            markup += `|${key}=${value}`;
        }
    }
    
    markup += '}}';
    
    return markup;
}

/**
 * Escape HTML entities for safe insertion into HTML attributes
 * @param {string} html - String to escape
 * @returns {string} Escaped string
 */
function escapeHTML(html) {
    return html
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

/**
 * Unescape HTML entities
 * @param {string} html - String to unescape
 * @returns {string} Unescaped string
 */
function unescapeHTML(html) {
    return html
        .replace(/&amp;/g, '&')
        .replace(/&lt;/g, '<')
        .replace(/&gt;/g, '>')
        .replace(/&quot;/g, '"')
        .replace(/&#039;/g, "'");
}

/**
 * Find all templates in wiki content
 * @param {string} content - Wiki content to search
 * @returns {Array} Array of found templates
 */
export function findTemplates(content) {
    const templates = [];
    const templateRegex = /\{\{([^{}|]+)(?:\|([^{}]*))?}}/g;
    
    let match;
    while ((match = templateRegex.exec(content)) !== null) {
        const templateName = match[1].trim();
        const paramsStr = match[2] || '';
        const fullMatch = match[0];
        const startPos = match.index;
        const endPos = startPos + fullMatch.length;
        
        const params = {};
        
        if (paramsStr) {
            const paramPairs = paramsStr.split('|');
            let position = 1;
            
            paramPairs.forEach(pair => {
                if (pair.includes('=')) {
                    const [key, value] = pair.split('=', 2);
                    params[key.trim()] = value.trim();
                } else {
                    params[position.toString()] = pair.trim();
                    position++;
                }
            });
        }
        
        templates.push({
            name: templateName,
            params: params,
            fullMatch: fullMatch,
            startPos: startPos,
            endPos: endPos
        });
    }
    
    return templates;
}
