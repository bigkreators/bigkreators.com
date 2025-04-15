// File: static/js/wiki-editor/components/template-gallery.js
/**
 * Template Gallery Component for Wiki Editor
 * 
 * This file contains the dialog for browsing and inserting wiki templates.
 */

import { insertWikiMarkup } from '../utils/text-utils.js';
import { createDialog, showDialog, hideDialog } from '../utils/dom-utils.js';

/**
 * Create template gallery
 * @returns {HTMLElement} The dialog element
 */
export function createTemplateGallery() {
    const dialogId = 'template-gallery';
    const existingDialog = document.getElementById(dialogId);
    if (existingDialog) return existingDialog;
    
    // Define common templates
    const templates = [
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
            name: 'Cite',
            description: 'Citation template',
            markup: '{{Cite web|title=Page Title|url=https://example.com|website=Website Name|access-date=2025-04-14}}'
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
        }
    ];
    
    let dialogContent = `
        <div class="wiki-dialog-content">
            <span class="close-dialog">&times;</span>
            <h3>Template Gallery</h3>
            <div class="template-search">
                <input type="text" id="template-search" placeholder="Search templates...">
            </div>
            <div class="template-grid">
    `;
    
    templates.forEach(template => {
        dialogContent += `
            <div class="template-item" data-template="${template.name.toLowerCase()}">
                <h4>${template.name}</h4>
                <p>${template.description}</p>
                <div class="template-preview">${template.markup.substring(0, 30)}...</div>
                <button class="template-insert" data-markup="${template.markup.replace(/"/g, '&quot;')}">Insert</button>
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
    
    return createDialog(dialogId, 'wiki-template-gallery', dialogContent);
}

/**
 * Open template gallery
 * @param {HTMLElement} textarea - The textarea element
 * @returns {HTMLElement} The dialog element
 */
export function openTemplateGallery(textarea) {
    const dialog = createTemplateGallery();
    
    // Remove existing event listeners by cloning elements
    const closeButton = dialog.querySelector('.close-dialog');
    const newCloseButton = closeButton.cloneNode(true);
    closeButton.parentNode.replaceChild(newCloseButton, closeButton);
    
    const customInsertButton = dialog.querySelector('#insert-custom-template');
    const newCustomButton = customInsertButton.cloneNode(true);
    customInsertButton.parentNode.replaceChild(newCustomButton, customInsertButton);
    
    // Add event listeners
    newCloseButton.addEventListener('click', () => {
        hideDialog(dialog);
    });
    
    // Set up template insert buttons
    const insertButtons = dialog.querySelectorAll('.template-insert');
    insertButtons.forEach(button => {
        // Remove any existing event listeners
        const newButton = button.cloneNode(true);
        button.parentNode.replaceChild(newButton, button);
        
        // Add new event listener
        newButton.addEventListener('click', () => {
            const markup = newButton.getAttribute('data-markup');
            insertWikiMarkup(textarea, markup);
            hideDialog(dialog);
        });
    });
    
    // Setup custom template insert
    newCustomButton.addEventListener('click', () => {
        const templateName = dialog.querySelector('#custom-template-name').value.trim();
        const paramsText = dialog.querySelector('#custom-template-params').value.trim();
        
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
        hideDialog(dialog);
    });
    
    // Add search functionality
    const searchInput = dialog.querySelector('#template-search');
    
    // Remove any existing event listener and add a new one
    const newSearchInput = searchInput.cloneNode(true);
    searchInput.parentNode.replaceChild(newSearchInput, searchInput);
    
    newSearchInput.addEventListener('input', () => {
        const searchTerm = newSearchInput.value.toLowerCase();
        const templateItems = dialog.querySelectorAll('.template-item');
        
        templateItems.forEach(item => {
            const templateName = item.getAttribute('data-template');
            if (templateName.includes(searchTerm)) {
                item.style.display = 'block';
            } else {
                item.style.display = 'none';
            }
        });
    });
    
    // Clear search and reset display
    newSearchInput.value = '';
    const templateItems = dialog.querySelectorAll('.template-item');
    templateItems.forEach(item => {
        item.style.display = 'block';
    });
    
    // Show dialog
    showDialog(dialog);
    
    // Focus search input
    newSearchInput.focus();
    
    return dialog;
}

export default {
    createTemplateGallery,
    openTemplateGallery
};
