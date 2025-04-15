// File: static/js/wiki-editor/enhanced-preview.js
/**
 * Enhanced Preview for Wiki Editor
 * 
 * This file provides enhanced preview functionality with
 * template rendering, better image handling, and more accurate
 * wiki markup transformation.
 */

import { getServerPreview } from './utils/transform-wiki.js';

/**
 * Show preview for wiki content
 * @param {HTMLElement} form - The form containing the wiki content
 */
export function showWikiPreview(form) {
    const contentTextarea = form.querySelector('#article-content');
    const summaryInput = form.querySelector('#article-summary');
    const previewArea = form.querySelector('.wiki-preview-area');
    
    if (!contentTextarea || !previewArea) {
        console.error('Cannot show preview: missing required elements');
        return;
    }
    
    const content = contentTextarea.value;
    const summary = summaryInput ? summaryInput.value : '';
    
    // Toggle preview visibility
    if (previewArea.style.display === 'none' || !previewArea.style.display) {
        // Show preview
        previewArea.innerHTML = '<div class="preview-loading">Loading preview...</div>';
        previewArea.style.display = 'block';
        
        // Get the preview content
        getServerPreview(content, summary, (html) => {
            renderPreview(previewArea, html);
            
            // Update button text
            const previewButton = document.getElementById('preview-button');
            if (previewButton) {
                previewButton.textContent = 'Hide Preview';
            }
        });
    } else {
        // Hide preview
        previewArea.style.display = 'none';
        
        // Update button text
        const previewButton = document.getElementById('preview-button');
        if (previewButton) {
            previewButton.textContent = 'Show Preview';
        }
    }
}

/**
 * Render HTML preview with enhancements
 * @param {HTMLElement} previewArea - The preview container element
 * @param {string} html - The HTML content to render
 */
function renderPreview(previewArea, html) {
    // Create preview container
    const previewContent = document.createElement('div');
    previewContent.className = 'wiki-preview-content';
    
    // Add header
    const previewHeader = document.createElement('h3');
    previewHeader.textContent = 'Preview:';
    
    // Set preview content
    previewContent.innerHTML = html;
    
    // Clear and update preview area
    previewArea.innerHTML = '';
    previewArea.appendChild(previewHeader);
    previewArea.appendChild(previewContent);
    
    // Add special handling for interactive elements
    addInteractiveFeatures(previewContent);
}

/**
 * Add interactive features to the preview
 * @param {HTMLElement} previewContent - The preview content element
 */
function addInteractiveFeatures(previewContent) {
    // Add collapsible sections
    const collapsibleSections = previewContent.querySelectorAll('.wiki-collapsible');
    collapsibleSections.forEach(section => {
        const header = section.querySelector('.collapsible-header');
        const content = section.querySelector('.collapsible-content');
        
        if (header && content) {
            header.addEventListener('click', function() {
                content.classList.toggle('collapsed');
                header.classList.toggle('collapsed');
            });
            
            // Start collapsed if marked
            if (section.classList.contains('initially-collapsed')) {
                content.classList.add('collapsed');
                header.classList.add('collapsed');
            }
        }
    });
    
    // Handle table sorting if any
    const sortableTables = previewContent.querySelectorAll('table.sortable');
    if (sortableTables.length > 0) {
        enableTableSorting(sortableTables);
    }
    
    // Handle image lightbox
    const images = previewContent.querySelectorAll('img');
    images.forEach(img => {
        img.addEventListener('click', function() {
            // Simple lightbox effect
            const lightbox = document.createElement('div');
            lightbox.className = 'wiki-lightbox';
            lightbox.innerHTML = `
                <div class="lightbox-content">
                    <img src="${img.src}" alt="${img.alt}">
                    <div class="lightbox-caption">${img.alt}</div>
                    <button class="lightbox-close">&times;</button>
                </div>
            `;
            
            document.body.appendChild(lightbox);
            
            // Close on click
            lightbox.addEventListener('click', function(e) {
                if (e.target === lightbox || e.target.classList.contains('lightbox-close')) {
                    document.body.removeChild(lightbox);
                }
            });
        });
        
        // Add indicator that image is clickable
        img.style.cursor = 'pointer';
    });
}

/**
 * Enable sorting functionality for tables
 * @param {NodeList} tables - The sortable tables
 */
function enableTableSorting(tables) {
    tables.forEach(table => {
        const headers = table.querySelectorAll('th');
        headers.forEach((header, index) => {
            // Add sort indicator and cursor
            header.style.cursor = 'pointer';
            header.innerHTML += ' <span class="sort-indicator">⇵</span>';
            
            // Add click handler
            header.addEventListener('click', function() {
                sortTable(table, index);
            });
        });
    });
}

/**
 * Sort a table by a column
 * @param {HTMLElement} table - The table element
 * @param {number} columnIndex - The index of the column to sort by
 */
function sortTable(table, columnIndex) {
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    const headers = table.querySelectorAll('th');
    const header = headers[columnIndex];
    
    // Determine sort direction
    const currentDir = header.getAttribute('data-sort-dir') || 'asc';
    const newDir = currentDir === 'asc' ? 'desc' : 'asc';
    
    // Reset all headers
    headers.forEach(h => {
        h.setAttribute('data-sort-dir', '');
        h.querySelector('.sort-indicator').textContent = '⇵';
    });
    
    // Set new sort direction
    header.setAttribute('data-sort-dir', newDir);
    header.querySelector('.sort-indicator').textContent = newDir === 'asc' ? '↑' : '↓';
    
    // Sort rows
    rows.sort((a, b) => {
        const cellA = a.querySelectorAll('td')[columnIndex].textContent.trim();
        const cellB = b.querySelectorAll('td')[columnIndex].textContent.trim();
        
        // Check if numeric
        if (!isNaN(cellA) && !isNaN(cellB)) {
            return newDir === 'asc' 
                ? parseFloat(cellA) - parseFloat(cellB)
                : parseFloat(cellB) - parseFloat(cellA);
        }
        
        // String comparison
        return newDir === 'asc'
            ? cellA.localeCompare(cellB)
            : cellB.localeCompare(cellA);
    });
    
    // Reorder the rows
    rows.forEach(row => tbody.appendChild(row));
}

export default {
    showWikiPreview
};
