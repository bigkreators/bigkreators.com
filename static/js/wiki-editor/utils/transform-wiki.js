// File: static/js/wiki-editor/utils/transform-wiki.js (EXPANDED)
/**
 * Enhanced Wiki Transformation Utilities
 * 
 * Handles transformation of form data to include Short Description template
 * and other Wikipedia-style metadata
 */

/**
 * Transform article content by moving summary to Short Description template
 * @param {HTMLElement} form - The form element
 */
export function transformContent(form) {
    console.log('Transforming article content with Short Description');
    
    const contentTextarea = form.querySelector('#article-content');
    const summaryInput = form.querySelector('#article-summary');
    
    if (!contentTextarea) {
        console.warn('No content textarea found for transformation');
        return;
    }
    
    let content = contentTextarea.value;
    let summary = summaryInput ? summaryInput.value.trim() : '';
    
    // If there's a summary, transform it to Short Description template
    if (summary) {
        // Remove any existing Short Description template first
        content = content.replace(/\{\{Short description\|[^}]*\}\}\s*/gi, '');
        
        // Add the Short Description template at the beginning
        const shortDescTemplate = `{{Short description|${summary}}}`;
        
        // Insert after any disambiguation templates or redirects, but before main content
        if (content.match(/^#REDIRECT/i) || content.match(/^\{\{[Dd]isambig/)) {
            // If there's a redirect or disambiguation, add after the first line
            const lines = content.split('\n');
            lines.splice(1, 0, shortDescTemplate);
            content = lines.join('\n');
        } else {
            // Otherwise, add at the very beginning
            content = shortDescTemplate + '\n' + content;
        }
        
        // Update the textarea
        contentTextarea.value = content;
        
        // Clear the summary field since it's now in the content
        if (summaryInput) {
            summaryInput.value = '';
        }
        
        console.log('Short Description template added to content');
    }
    
    // Additional transformations for Wikipedia-style articles
    applyWikipediaStyleTransformations(contentTextarea);
}

/**
 * Apply additional Wikipedia-style transformations
 * @param {HTMLElement} textarea - The content textarea
 */
function applyWikipediaStyleTransformations(textarea) {
    let content = textarea.value;
    
    // Ensure proper heading hierarchy
    content = normalizeHeadings(content);
    
    // Clean up excessive whitespace
    content = content.replace(/\n{3,}/g, '\n\n');
    
    // Ensure categories are at the end
    content = moveCategoriestoEnd(content);
    
    // Update textarea
    textarea.value = content;
}

/**
 * Normalize heading hierarchy (ensure proper H2, H3, etc. structure)
 * @param {string} content - Wiki markup content
 * @returns {string} Normalized content
 */
function normalizeHeadings(content) {
    const lines = content.split('\n');
    const processedLines = [];
    
    lines.forEach(line => {
        // Check if line is a heading
        const headingMatch = line.match(/^(=+)\s*(.*?)\s*(=+)$/);
        
        if (headingMatch) {
            const startEquals = headingMatch[1];
            const headingText = headingMatch[2];
            const endEquals = headingMatch[3];
            
            // Ensure start and end equals match
            if (startEquals.length !== endEquals.length) {
                const correctLength = Math.min(startEquals.length, endEquals.length);
                const correctedEquals = '='.repeat(correctLength);
                processedLines.push(`${correctedEquals} ${headingText} ${correctedEquals}`);
            } else {
                processedLines.push(line);
            }
        } else {
            processedLines.push(line);
        }
    });
    
    return processedLines.join('\n');
}

/**
 * Move all category declarations to the end of the article
 * @param {string} content - Wiki markup content
 * @returns {string} Content with categories moved to end
 */
function moveCategoriestoEnd(content) {
    const categories = [];
    const lines = content.split('\n');
    const contentLines = [];
    
    lines.forEach(line => {
        if (line.match(/^\[\[Category:/i)) {
            categories.push(line);
        } else {
            contentLines.push(line);
        }
    });
    
    // Remove trailing empty lines from content
    while (contentLines.length > 0 && contentLines[contentLines.length - 1].trim() === '') {
        contentLines.pop();
    }
    
    // Combine content and categories
    if (categories.length > 0) {
        return contentLines.join('\n') + '\n\n' + categories.join('\n');
    }
    
    return contentLines.join('\n');
}

/**
 * Add Short Description to content if summary exists
 * @param {string} content - Current article content
 * @param {string} summary - Article summary
 * @returns {string} Content with Short Description added
 */
export function addShortDescription(content, summary) {
    if (!summary || !summary.trim()) {
        return content;
    }
    
    // Remove any existing Short Description
    content = content.replace(/\{\{Short description\|[^}]*\}\}\s*/gi, '');
    
    // Add new Short Description at the beginning
    const shortDescTemplate = `{{Short description|${summary.trim()}}}`;
    
    return shortDescTemplate + '\n' + content;
}

/**
 * Extract Short Description from content
 * @param {string} content - Wiki markup content
 * @returns {Object} Object with content and extracted summary
 */
export function extractShortDescription(content) {
    const match = content.match(/\{\{Short description\|([^}]*)\}\}/i);
    
    if (match) {
        const summary = match[1].trim();
        const contentWithoutShortDesc = content.replace(/\{\{Short description\|[^}]*\}\}\s*/gi, '');
        
        return {
            content: contentWithoutShortDesc,
            summary: summary
        };
    }
    
    return {
        content: content,
        summary: ''
    };
}

/**
 * Validate Wikipedia-style article structure
 * @param {string} content - Wiki markup content
 * @returns {Array} Array of validation issues
 */
export function validateArticleStructure(content) {
    const issues = [];
    
    // Check for Short Description
    if (!content.match(/\{\{Short description\|/i)) {
        issues.push({
            type: 'warning',
            message: 'Article should have a Short Description template'
        });
    }
    
    // Check for proper heading hierarchy
    const headings = content.match(/^=+\s.*\s=+$/gm) || [];
    let previousLevel = 0;
    
    headings.forEach((heading, index) => {
        const level = heading.match(/^=+/)[0].length;
        
        if (index === 0 && level !== 2) {
            issues.push({
                type: 'error',
                message: 'First heading should be level 2 (== Heading ==)'
            });
        }
        
        if (level > previousLevel + 1) {
            issues.push({
                type: 'warning',
                message: `Heading level jumps from ${previousLevel} to ${level} - consider using proper hierarchy`
            });
        }
        
        previousLevel = level;
    });
    
    // Check for categories
    const categories = content.match(/\[\[Category:[^\]]+\]\]/gi) || [];
    if (categories.length === 0) {
        issues.push({
            type: 'warning',
            message: 'Article should have at least one category'
        });
    }
    
    // Check for references
    const references = content.match(/<ref[^>]*>|<ref[^>]*\/>/gi) || [];
    const refList = content.match(/\{\{reflist\}\}|\{\{references\}\}/gi) || [];
    
    if (references.length > 0 && refList.length === 0) {
        issues.push({
            type: 'error',
            message: 'Article has references but no {{reflist}} or {{references}} template'
        });
    }
    
    return issues;
}

/**
 * Generate article metadata for display
 * @param {string} content - Wiki markup content
 * @returns {Object} Article metadata
 */
export function generateArticleMetadata(content) {
    const metadata = {
        shortDescription: '',
        wordCount: 0,
        headingCount: 0,
        linkCount: 0,
        referenceCount: 0,
        categoryCount: 0,
        imageCount: 0
    };
    
    // Extract Short Description
    const shortDescMatch = content.match(/\{\{Short description\|([^}]*)\}\}/i);
    if (shortDescMatch) {
        metadata.shortDescription = shortDescMatch[1].trim();
    }
    
    // Count words (excluding templates and markup)
    const cleanContent = content
        .replace(/\{\{[^}]+\}\}/g, '') // Remove templates
        .replace(/\[\[[^\]]*\|([^\]]*)\]\]/g, '$1') // Extract link text
        .replace(/\[\[([^\]]*)\]\]/g, '$1') // Extract simple links
        .replace(/<[^>]+>/g, '') // Remove HTML tags
        .replace(/^=+.*=+$/gm, '') // Remove headings
        .replace(/^\*.*$/gm, '') // Remove list items
        .replace(/^#.*$/gm, '') // Remove numbered lists
        .replace(/^:.*$/gm, '') // Remove indented lines
        .trim();
    
    const words = cleanContent.split(/\s+/).filter(word => word.length > 0);
    metadata.wordCount = words.length;
    
    // Count headings
    const headings = content.match(/^=+\s.*\s=+$/gm) || [];
    metadata.headingCount = headings.length;
    
    // Count internal links
    const internalLinks = content.match(/\[\[[^\]]+\]\]/g) || [];
    metadata.linkCount = internalLinks.length;
    
    // Count references
    const references = content.match(/<ref[^>]*>|<ref[^>]*\/>/gi) || [];
    metadata.referenceCount = references.length;
    
    // Count categories
    const categories = content.match(/\[\[Category:[^\]]+\]\]/gi) || [];
    metadata.categoryCount = categories.length;
    
    // Count images/files
    const images = content.match(/\[\[File:[^\]]+\]\]|\[\[Image:[^\]]+\]\]/gi) || [];
    metadata.imageCount = images.length;
    
    return metadata;
}

/**
 * Setup form to handle Wikipedia-style editing
 * @param {HTMLElement} form - The form element
 */
export function setupWikipediaForm(form) {
    console.log('Setting up Wikipedia-style form');
    
    const summaryInput = form.querySelector('#article-summary');
    
    if (summaryInput) {
        // Add notice about Short Description transformation
        const notice = document.createElement('div');
        notice.className = 'short-description-notice';
        notice.innerHTML = `
            <strong>Note:</strong> The summary will be automatically converted to a 
            <code>{{Short description|...}}</code> template in your article content. 
            This description will appear in search results and article previews.
        `;
        
        summaryInput.parentNode.appendChild(notice);
        
        // Add real-time preview of Short Description
        summaryInput.addEventListener('input', function() {
            updateShortDescriptionPreview(this.value, notice);
        });
    }
    
    // Setup form submission handler
    form.addEventListener('submit', function(e) {
        // Don't prevent submission, just transform content
        transformContent(form);
        
        // Show brief confirmation
        const submitBtn = form.querySelector('[type="submit"]');
        if (submitBtn) {
            const originalText = submitBtn.textContent;
            submitBtn.textContent = 'Processing...';
            setTimeout(() => {
                submitBtn.textContent = originalText;
            }, 2000);
        }
    });
    
    // Setup preview enhancement
    const previewBtn = form.querySelector('#preview-button, .preview-button');
    if (previewBtn) {
        previewBtn.addEventListener('click', function() {
            // Transform content before preview
            transformContent(form);
        });
    }
}

/**
 * Update Short Description preview
 * @param {string} summary - Current summary text
 * @param {HTMLElement} notice - Notice element to update
 */
function updateShortDescriptionPreview(summary, notice) {
    if (summary.trim()) {
        notice.innerHTML = `
            <strong>Preview:</strong> <code>{{Short description|${summary.trim()}}}</code><br>
            <small>This will appear in search results and article previews.</small>
        `;
    } else {
        notice.innerHTML = `
            <strong>Note:</strong> The summary will be automatically converted to a 
            <code>{{Short description|...}}</code> template in your article content. 
            This description will appear in search results and article previews.
        `;
    }
}

/**
 * Auto-save functionality for long editing sessions
 * @param {HTMLElement} form - The form element
 */
export function setupAutoSave(form) {
    const contentTextarea = form.querySelector('#article-content');
    const summaryInput = form.querySelector('#article-summary');
    
    if (!contentTextarea) return;
    
    // Create autosave key based on form and article
    const articleId = form.querySelector('input[name="article_id"]')?.value || 'new';
    const autosaveKey = `kryptopedia_autosave_${articleId}`;
    
    // Load any existing autosaved content
    loadAutoSavedContent(autosaveKey, contentTextarea, summaryInput);
    
    // Setup autosave on input
    let saveTimeout;
    const autoSave = () => {
        clearTimeout(saveTimeout);
        saveTimeout = setTimeout(() => {
            const data = {
                content: contentTextarea.value,
                summary: summaryInput ? summaryInput.value : '',
                timestamp: Date.now()
            };
            
            localStorage.setItem(autosaveKey, JSON.stringify(data));
            console.log('Content auto-saved');
        }, 3000); // Save after 3 seconds of inactivity
    };
    
    contentTextarea.addEventListener('input', autoSave);
    if (summaryInput) {
        summaryInput.addEventListener('input', autoSave);
    }
    
    // Clear autosave on successful submission
    form.addEventListener('submit', () => {
        setTimeout(() => {
            localStorage.removeItem(autosaveKey);
            console.log('Auto-saved content cleared after submission');
        }, 1000);
    });
    
    // Warn about unsaved changes on page unload
    window.addEventListener('beforeunload', (e) => {
        const autosaved = localStorage.getItem(autosaveKey);
        if (autosaved) {
            const data = JSON.parse(autosaved);
            const timeSinceEdit = Date.now() - data.timestamp;
            
            // If there were recent changes (within 5 minutes)
            if (timeSinceEdit < 5 * 60 * 1000) {
                e.preventDefault();
                e.returnValue = 'You have unsaved changes. Are you sure you want to leave?';
                return e.returnValue;
            }
        }
    });
}

/**
 * Load auto-saved content if available
 * @param {string} autosaveKey - The localStorage key
 * @param {HTMLElement} contentTextarea - Content textarea
 * @param {HTMLElement} summaryInput - Summary input (optional)
 */
function loadAutoSavedContent(autosaveKey, contentTextarea, summaryInput) {
    const autosaved = localStorage.getItem(autosaveKey);
    
    if (autosaved) {
        try {
            const data = JSON.parse(autosaved);
            const timeSinceEdit = Date.now() - data.timestamp;
            
            // Only restore if it's recent (within 1 hour) and different from current content
            if (timeSinceEdit < 60 * 60 * 1000 && data.content !== contentTextarea.value) {
                const shouldRestore = confirm(
                    'Auto-saved content found from ' + 
                    new Date(data.timestamp).toLocaleTimeString() + 
                    '. Would you like to restore it?'
                );
                
                if (shouldRestore) {
                    contentTextarea.value = data.content;
                    if (summaryInput && data.summary) {
                        summaryInput.value = data.summary;
                    }
                    console.log('Auto-saved content restored');
                }
            }
        } catch (e) {
            console.warn('Failed to parse auto-saved content:', e);
            localStorage.removeItem(autosaveKey);
        }
    }
}

/**
 * Initialize all Wikipedia-style transformations on a form
 * @param {HTMLElement} form - The form element to enhance
 */
export function initializeWikipediaEditor(form) {
    console.log('Initializing Wikipedia-style editor');
    
    // Setup form enhancements
    setupWikipediaForm(form);
    
    // Setup auto-save
    setupAutoSave(form);
    
    // Add metadata display
    addMetadataDisplay(form);
    
    console.log('Wikipedia-style editor initialized');
}

/**
 * Add article metadata display
 * @param {HTMLElement} form - The form element
 */
function addMetadataDisplay(form) {
    const contentTextarea = form.querySelector('#article-content');
    if (!contentTextarea) return;
    
    // Create metadata display
    const metadataDiv = document.createElement('div');
    metadataDiv.className = 'wiki-metadata-display';
    metadataDiv.style.cssText = `
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 4px;
        padding: 10px;
        margin-top: 10px;
        font-size: 12px;
        color: #6c757d;
        display: flex;
        gap: 15px;
        flex-wrap: wrap;
    `;
    
    // Insert after textarea
    contentTextarea.parentNode.insertBefore(metadataDiv, contentTextarea.nextSibling);
    
    // Update metadata on content change
    const updateMetadata = () => {
        const metadata = generateArticleMetadata(contentTextarea.value);
        metadataDiv.innerHTML = `
            <span><strong>Words:</strong> ${metadata.wordCount}</span>
            <span><strong>Headings:</strong> ${metadata.headingCount}</span>
            <span><strong>Links:</strong> ${metadata.linkCount}</span>
            <span><strong>References:</strong> ${metadata.referenceCount}</span>
            <span><strong>Categories:</strong> ${metadata.categoryCount}</span>
            <span><strong>Images:</strong> ${metadata.imageCount}</span>
            ${metadata.shortDescription ? `<span><strong>Description:</strong> ${metadata.shortDescription}</span>` : ''}
        `;
    };
    
    // Initial update
    updateMetadata();
    
    // Update on input (debounced)
    let metadataTimeout;
    contentTextarea.addEventListener('input', () => {
        clearTimeout(metadataTimeout);
        metadataTimeout = setTimeout(updateMetadata, 1000);
    });
}

export default {
    transformContent,
    addShortDescription,
    extractShortDescription,
    validateArticleStructure,
    generateArticleMetadata,
    setupWikipediaForm,
    setupAutoSave,
    initializeWikipediaEditor
};
