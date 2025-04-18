// File: static/js/wiki-editor/image-handler.js
/**
 * Image Handler for Wiki Editor
 * 
 * This file contains functions for handling image insertion and formatting.
 */

import { insertWikiMarkup } from './utils/text-utils.js';

/**
 * Open image dialog
 * @param {HTMLElement} textarea - The textarea element
 */
export function openImageDialog(textarea) {
    console.log('Opening image dialog for', textarea);
    // Create dialog
    const dialog = document.createElement('div');
    dialog.className = 'wiki-dialog wiki-image-dialog';
    
    dialog.innerHTML = `
        <div class="wiki-dialog-content">
            <span class="close-dialog">&times;</span>
            <h3>Insert Image</h3>
            <div class="form-group">
                <label for="image-filename">Image Filename:</label>
                <input type="text" id="image-filename" placeholder="example.jpg">
            </div>
            <div class="form-group">
                <label for="image-caption">Caption (optional):</label>
                <input type="text" id="image-caption" placeholder="Image description">
            </div>
            <div class="image-options">
                <div class="option-group">
                    <h4>Size</h4>
                    <label>
                        <input type="radio" name="image-size" value="thumb" checked>
                        Thumbnail
                    </label>
                    <label>
                        <input type="radio" name="image-size" value="full">
                        Full size
                    </label>
                    <div class="sub-option">
                        <label for="image-width">Width (optional):</label>
                        <input type="text" id="image-width" placeholder="e.g., 300px">
                    </div>
                </div>
                <div class="option-group">
                    <h4>Alignment</h4>
                    <label>
                        <input type="radio" name="image-align" value="none" checked>
                        None
                    </label>
                    <label>
                        <input type="radio" name="image-align" value="left">
                        Left
                    </label>
                    <label>
                        <input type="radio" name="image-align" value="center">
                        Center
                    </label>
                    <label>
                        <input type="radio" name="image-align" value="right">
                        Right
                    </label>
                </div>
            </div>
            <div class="dialog-actions">
                <button type="button" id="insert-image-btn">Insert Image</button>
                <button type="button" id="cancel-image-btn">Cancel</button>
            </div>
        </div>
    `;
    
    document.body.appendChild(dialog);
    
    // Add event listeners
    const closeButton = dialog.querySelector('.close-dialog');
    closeButton.addEventListener('click', () => {
        dialog.remove();
    });
    
    const cancelButton = document.getElementById('cancel-image-btn');
    cancelButton.addEventListener('click', () => {
        dialog.remove();
    });
    
    const insertButton = document.getElementById('insert-image-btn');
    insertButton.addEventListener('click', () => {
        console.log('Insert image button clicked');
        const filename = document.getElementById('image-filename').value.trim();
        const caption = document.getElementById('image-caption').value.trim();
        const size = document.querySelector('input[name="image-size"]:checked').value;
        const align = document.querySelector('input[name="image-align"]:checked').value;
        const width = document.getElementById('image-width').value.trim();
        
        if (!filename) {
            alert('Please enter an image filename.');
            return;
        }
        
        // Build image markup
        let imageMarkup = `[[File:${filename}`;
        
        if (size === 'thumb') {
            imageMarkup += '|thumb';
        }
        
        if (width) {
            imageMarkup += `|width=${width}`;
        }
        
        if (align !== 'none') {
            imageMarkup += `|${align}`;
        }
        
        if (caption) {
            imageMarkup += `|${caption}`;
        }
        
        imageMarkup += ']]';
        
        console.log('Inserting image markup:', imageMarkup);
        insertWikiMarkup(textarea, imageMarkup);
        dialog.remove();
    });
    
    // Show dialog
    dialog.style.display = 'block';
    
    // Focus the first input
    document.getElementById('image-filename').focus();
    
    // Close on outside click
    window.addEventListener('click', (event) => {
        if (event.target === dialog) {
            dialog.remove();
        }
    });
}

/**
 * Transform wiki image markup to HTML for preview
 * @param {string} markup - Wiki markup containing images
 * @returns {string} HTML with transformed images
 */
export function transformImages(markup) {
    // Match image syntax [[File:...]]
    return markup.replace(/\[\[File:(.*?)(?:\|(.*?))?\]\]/g, (match, filename, optionsStr) => {
        const options = optionsStr ? optionsStr.split('|') : [];
        let imageClass = 'wiki-image';
        let caption = '';
        let width = '';
        
        // Process options
        options.forEach(opt => {
            const trimmed = opt.trim();
            
            if (trimmed === 'thumb' || trimmed === 'thumbnail') {
                imageClass += ' thumb';
            } else if (trimmed === 'center') {
                imageClass += ' center';
            } else if (trimmed === 'right') {
                imageClass += ' right';
            } else if (trimmed === 'left') {
                imageClass += ' left';
            } else if (trimmed.startsWith('width=')) {
                width = trimmed.substring(6);
            } else {
                // Assume it's a caption
                caption = trimmed;
            }
        });
        
        // Generate HTML
        let html = `<figure class="${imageClass}">`;
        html += `<img src="/media/${filename}" alt="${caption}"${width ? ` width="${width}"` : ''}>`;
        if (caption) {
            html += `<figcaption>${caption}</figcaption>`;
        }
        html += '</figure>';
        
        return html;
    });
}

export default {
    openImageDialog,
    transformImages
};
