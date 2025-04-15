// File: static/js/wiki-editor/utils/transform-wiki.js
/**
 * Wiki Transformation Utilities
 * 
 * This file contains utility functions for transforming content between
 * wiki markup and HTML, and for working with wiki-specific structures.
 */

/**
 * Extract short description from wiki markup
 * @param {string} content - Wiki markup content
 * @returns {Object} Object with extracted description and remaining content
 */
export function extractShortDescription(content) {
    const shortDescriptionRegex = /^\s*\{\{Short description\|(.*?)\}\}\s*\n+/;
    const match = content.match(shortDescriptionRegex);
    
    if (match) {
        return {
            description: match[1].trim(),
            content: content.replace(match[0], '')
        };
    }
    
    return {
        description: '',
        content
    };
}

/**
 * Add short description to wiki markup if not present
 * @param {string} content - Wiki markup content
 * @param {string} description - Short description to add
 * @returns {string} Content with short description
 */
export function addShortDescription(content, description) {
    if (!description) return content;
    
    // Check if content already has a short description
    if (content.match(/^\s*\{\{Short description\|.*?\}\}/)) {
        return content;
    }
    
    // Add short description at the beginning
    return `{{Short description|${description}}}\n\n${content}`;
}

/**
 * Transform wiki markup for specific syntax highlighting
 * @param {string} content - Wiki markup content
 * @returns {string} Transformed content for editor display
 */
export function highlightWikiSyntax(content) {
    // This function can be expanded to add syntax highlighting
    // in the textarea for better editing experience
    return content;
}

/**
 * Parse a template invocation and extract parameters
 * @param {string} template - Template string like {{TemplateName|param1=value1|param2=value2}}
 * @returns {Object} Template data with name and parameters
 */
export function parseTemplate(template) {
    const match = template.match(/\{\{([^|]+)(\|.*?)?\}\}/);
    if (!match) return null;
    
    const name = match[1].trim();
    const paramsString = match[2] || '';
    
    const params = {};
    if (paramsString) {
        // Remove leading pipe
        const cleanParams = paramsString.substring(1);
        
        // Split by pipe but respect nested templates
        let paramList = [];
        let currentParam = '';
        let nestedLevel = 0;
        
        for (let i = 0; i < cleanParams.length; i++) {
            const char = cleanParams[i];
            
            if (char === '{' && cleanParams[i+1] === '{') {
                nestedLevel++;
                currentParam += char;
            } else if (char === '}' && cleanParams[i+1] === '}') {
                nestedLevel--;
                currentParam += char;
            } else if (char === '|' && nestedLevel === 0) {
                paramList.push(currentParam);
                currentParam = '';
            } else {
                currentParam += char;
            }
        }
        
        if (currentParam) {
            paramList.push(currentParam);
        }
        
        // Process parameters
        paramList.forEach((param, index) => {
            const equalPos = param.indexOf('=');
            
            if (equalPos > 0) {
                // Named parameter
                const key = param.substring(0, equalPos).trim();
                const value = param.substring(equalPos + 1).trim();
                params[key] = value;
            } else {
                // Positional parameter
                params[index + 1] = param.trim();
            }
        });
    }
    
    return {
        name,
        params
    };
}

/**
 * Format a template object back to wiki syntax
 * @param {Object} template - Template object with name and params
 * @returns {string} Wiki markup for the template
 */
export function formatTemplate(template) {
    if (!template || !template.name) return '';
    
    let result = `{{${template.name}`;
    
    if (template.params) {
        Object.entries(template.params).forEach(([key, value]) => {
            if (isNaN(parseInt(key))) {
                // Named parameter
                result += `|${key}=${value}`;
            } else {
                // Positional parameter
                result += `|${value}`;
            }
        });
    }
    
    result += '}}';
    return result;
}

/**
 * Get server-side preview of wiki markup
 * @param {string} content - Wiki markup content
 * @param {string} summary - Optional summary for short description
 * @param {Function} callback - Callback function with HTML result
 */
export function getServerPreview(content, summary, callback) {
    // Get token from localStorage
    const token = localStorage.getItem('token');
    if (!token) {
        // Fallback to client-side preview if token not available
        callback(clientPreview(content, summary));
        return;
    }
    
    // Content with short description if needed
    let previewContent = content;
    if (summary && !previewContent.includes('{{Short description|')) {
        previewContent = addShortDescription(previewContent, summary);
    }
    
    // Send to server for proper rendering
    fetch('/api/preview', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ content: previewContent })
    })
    .then(response => response.json())
    .then(data => {
        callback(data.html);
    })
    .catch(error => {
        console.error('Error fetching preview:', error);
        // Fallback to client-side preview
        callback(clientPreview(content, summary));
    });
}

/**
 * Simple client-side preview for when server preview is unavailable
 * @param {string} content - Wiki markup content
 * @param {string} summary - Optional summary
 * @returns {string} HTML preview
 */
function clientPreview(content, summary) {
    let html = content;
    
    // Add short description
    if (summary && !html.includes('{{Short description|')) {
        html = `<div class="wiki-short-description">${summary}</div>\n\n${html}`;
    } else {
        // Extract and format existing short description
        const shortDescMatch = html.match(/\{\{Short description\|(.*?)\}\}/);
        if (shortDescMatch) {
            html = html.replace(shortDescMatch[0], `<div class="wiki-short-description">${shortDescMatch[1]}</div>`);
        }
    }
    
    // Basic transformations
    html = html.replace(/'''(.*?)'''/g, '<strong>$1</strong>');
    html = html.replace(/''(.*?)''/g, '<em>$1</em>');
    html = html.replace(/==== (.*?) ====/g, '<h4>$1</h4>');
    html = html.replace(/=== (.*?) ===/g, '<h3>$1</h3>');
    html = html.replace(/== (.*?) ==/g, '<h2>$1</h2>');
    html = html.replace(/= (.*?) =/g, '<h1>$1</h1>');
    
    // Links
    html = html.replace(/\[\[(.*?)\]\]/g, '<a href="/articles/$1">$1</a>');
    html = html.replace(/\[\[(.*?)\|(.*?)\]\]/g, '<a href="/articles/$1">$2</a>');
    html = html.replace(/\[(https?:\/\/.*?) (.*?)\]/g, '<a href="$1">$2</a>');
    
    // Lists
    const lines = html.split('\n');
    let result = [];
    let inList = false;
    let listType = '';
    
    for (const line of lines) {
        if (line.startsWith('* ')) {
            if (!inList || listType !== 'ul') {
                if (inList) result.push(`</${listType}>`);
                result.push('<ul>');
                inList = true;
                listType = 'ul';
            }
            result.push(`<li>${line.substring(2)}</li>`);
        } else if (line.startsWith('# ')) {
            if (!inList || listType !== 'ol') {
                if (inList) result.push(`</${listType}>`);
                result.push('<ol>');
                inList = true;
                listType = 'ol';
            }
            result.push(`<li>${line.substring(2)}</li>`);
        } else {
            if (inList) {
                result.push(`</${listType}>`);
                inList = false;
            }
            result.push(line);
        }
    }
    
    if (inList) {
        result.push(`</${listType}>`);
    }
    
    html = result.join('\n');
    
    // Split paragraphs
    html = html.split('\n\n').map(para => {
        if (para.trim() && !para.trim().startsWith('<')) {
            return `<p>${para}</p>`;
        }
        return para;
    }).join('\n');
    
    return html;
}

export default {
    extractShortDescription,
    addShortDescription,
    highlightWikiSyntax,
    parseTemplate,
    formatTemplate,
    getServerPreview
};
