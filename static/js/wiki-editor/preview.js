/**
 * Preview Functionality for Wiki Editor
 * 
 * This file contains functions for previewing wiki content.
 */

import { transformWikiMarkup } from './utils.js';

/**
 * Add preview button to form actions
 * @param {HTMLElement} form - The form element
 */
export function addPreviewButton(form) {
    const formActions = form.querySelector('.form-actions');
    if (!formActions) return;
    
    // Check if preview button already exists
    if (formActions.querySelector('#preview-button')) return;
    
    // Create preview button
    const previewButton = document.createElement('button');
    previewButton.type = 'button';
    previewButton.id = 'preview-button';
    previewButton.className = 'preview-button';
    previewButton.textContent = 'Show Preview';
    
    // Insert before the cancel button (if it exists)
    const cancelButton = formActions.querySelector('.cancel-button');
    if (cancelButton) {
        formActions.insertBefore(previewButton, cancelButton);
    } else {
        formActions.appendChild(previewButton);
    }
    
    // Add click handler
    previewButton.addEventListener('click', function() {
        previewContent(form);
    });
}

/**
 * Preview the wiki content
 * @param {HTMLElement} form - The form containing the content
 */
export function previewContent(form) {
    const contentTextarea = form.querySelector('#article-content');
    const summaryTextarea = form.querySelector('#article-summary');
    const previewArea = form.querySelector('.wiki-preview-area');
    
    if (!contentTextarea || !previewArea) return;
    
    // Get the content
    let content = contentTextarea.value;
    
    // Add the short description if available
    if (summaryTextarea && summaryTextarea.value) {
        const summary = summaryTextarea.value;
        // Check if the content already has a short description
        if (!content.includes('{{Short description|')) {
            content = `{{Short description|${summary}}}\n\n${content}`;
        }
    }
    
    // Toggle preview area visibility
    const isVisible = previewArea.style.display !== 'none';
    
    if (isVisible) {
        previewArea.style.display = 'none';
        const previewButton = document.getElementById('preview-button');
        if (previewButton) {
            previewButton.textContent = 'Show Preview';
        }
    } else {
        // Get token from localStorage
        const token = localStorage.getItem('token');
        
        if (token) {
            // Send to server for proper rendering if token exists
            fetch('/api/preview', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ content: content })
            })
            .then(response => response.json())
            .then(data => {
                previewArea.innerHTML = `<h3>Preview:</h3><div class="wiki-preview-content">${data.html}</div>`;
                previewArea.style.display = 'block';
                const previewButton = document.getElementById('preview-button');
                if (previewButton) {
                    previewButton.textContent = 'Hide Preview';
                }
            })
            .catch(error => {
                console.error('Error fetching preview:', error);
                
                // Fall back to client-side rendering
                const html = transformWikiMarkup(content);
                previewArea.innerHTML = `<h3>Preview:</h3><div class="wiki-preview-content">${html}</div>`;
                previewArea.style.display = 'block';
                const previewButton = document.getElementById('preview-button');
                if (previewButton) {
                    previewButton.textContent = 'Hide Preview';
                }
            });
        } else {
            // Transform wiki markup to HTML (client-side)
            const html = transformWikiMarkup(content);
            previewArea.innerHTML = `<h3>Preview:</h3><div class="wiki-preview-content">${html}</div>`;
            previewArea.style.display = 'block';
            const previewButton = document.getElementById('preview-button');
            if (previewButton) {
                previewButton.textContent = 'Hide Preview';
            }
        }
    }
}
