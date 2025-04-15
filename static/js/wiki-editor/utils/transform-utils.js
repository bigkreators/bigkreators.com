// File: static/js/wiki-editor/utils/transform-utils.js
/**
 * Transformation Utilities for Wiki Editor
 * 
 * This file contains utility functions for transforming wiki markup to HTML.
 */

/**
 * Transform wiki markup to HTML for preview
 * @param {string} markup - Wiki markup content
 * @returns {string} HTML content
 */
export function transformWikiToHTML(markup) {
    let html = markup;
    
    // Extract short description if present
    const shortDescMatch = /\{\{Short description\|(.*?)\}\}/g.exec(html);
    if (shortDescMatch) {
        // Remove short description template
        html = html.replace(shortDescMatch[0], '');
    }
    
    // Format text
    html = html.replace(/'''(.*?)'''/g, '<strong>$1</strong>'); // Bold
    html = html.replace(/''(.*?)''/g, '<em>$1</em>'); // Italic
    html = html.replace(/<u>(.*?)<\/u>/g, '<u>$1</u>'); // Underline
    html = html.replace(/<s>(.*?)<\/s>/g, '<s>$1</s>'); // Strikethrough
    
    // Format headings
    html = html.replace(/======\s*(.*?)\s*======/g, '<h6>$1</h6>');
    html = html.replace(/=====\s*(.*?)\s*=====/g, '<h5>$1</h5>');
    html = html.replace(/====\s*(.*?)\s*====/g, '<h4>$1</h4>');
    html = html.replace(/===\s*(.*?)\s*===/g, '<h3>$1</h3>');
    html = html.replace(/==\s*(.*?)\s*==/g, '<h2>$1</h2>');
    html = html.replace(/=\s*(.*?)\s*=/g, '<h1>$1</h1>');
    
    // Format links
    html = html.replace(/\[\[(.*?)\]\]/g, '<a href="/articles/$1">$1</a>'); // Internal link
    html = html.replace(/\[\[(.*?)\|(.*?)\]\]/g, '<a href="/articles/$1">$2</a>'); // Internal link with display text
    html = html.replace(/\[(https?:\/\/[^\s\]]+)\s+(.*?)\]/g, '<a href="$1" target="_blank" rel="noopener">$2</a>'); // External link
    html = html.replace(/\[(https?:\/\/[^\s\]]+)\]/g, '<a href="$1" target="_blank" rel="noopener">$1</a>'); // External link without text
    
    // Format lists (simple implementation, doesn't handle nesting)
    const lines = html.split('\n');
    let inList = false;
    let listType = '';
    let result = [];
    
    for (let i = 0; i < lines.length; i++) {
        const line = lines[i];
        
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
    
    // Handle paragraphs - simple implementation
    html = html.split('\n\n').map(para => {
        if (para.trim() && !para.trim().startsWith('<')) {
            return `<p>${para}</p>`;
        }
        return para;
    }).join('\n\n');
    
    return html;
}

/**
 * Transform HTML to wiki markup
 * @param {string} html - HTML content
 * @returns {string} Wiki markup
 */
export function transformHTMLToWiki(html) {
    let wiki = html;
    
    // Format headings
    wiki = wiki.replace(/<h1.*?>(.*?)<\/h1>/g, '= $1 =');
    wiki = wiki.replace(/<h2.*?>(.*?)<\/h2>/g, '== $1 ==');
    wiki = wiki.replace(/<h3.*?>(.*?)<\/h3>/g, '=== $1 ===');
    wiki = wiki.replace(/<h4.*?>(.*?)<\/h4>/g, '==== $1 ====');
    wiki = wiki.replace(/<h5.*?>(.*?)<\/h5>/g, '===== $1 =====');
    wiki = wiki.replace(/<h6.*?>(.*?)<\/h6>/g, '====== $1 ======');
    
    // Format text
    wiki = wiki.replace(/<strong.*?>(.*?)<\/strong>/g, "'''$1'''");
    wiki = wiki.replace(/<b.*?>(.*?)<\/b>/g, "'''$1'''");
    wiki = wiki.replace(/<em.*?>(.*?)<\/em>/g, "''$1''");
    wiki = wiki.replace(/<i.*?>(.*?)<\/i>/g, "''$1''");
    
    // Format links
    wiki = wiki.replace(/<a\s+href="\/articles\/(.*?)".*?>(.*?)<\/a>/g, (match, p1, p2) => {
        if (p1 === p2) {
            return `[[${p1}]]`;
        } else {
            return `[[${p1}|${p2}]]`;
        }
    });
    wiki = wiki.replace(/<a\s+href="(https?:\/\/.*?)".*?>(.*?)<\/a>/g, (match, p1, p2) => {
        if (p1 === p2) {
            return `[${p1}]`;
        } else {
            return `[${p1} ${p2}]`;
        }
    });
    
    // Format lists
    wiki = wiki.replace(/<ul.*?>([\s\S]*?)<\/ul>/g, (match, content) => {
        const items = content.match(/<li.*?>([\s\S]*?)<\/li>/g) || [];
        return items.map(item => {
            const text = item.replace(/<li.*?>([\s\S]*?)<\/li>/g, '$1');
            return `* ${text}`;
        }).join('\n');
    });
    
    wiki = wiki.replace(/<ol.*?>([\s\S]*?)<\/ol>/g, (match, content) => {
        const items = content.match(/<li.*?>([\s\S]*?)<\/li>/g) || [];
        return items.map(item => {
            const text = item.replace(/<li.*?>([\s\S]*?)<\/li>/g, '$1');
            return `# ${text}`;
        }).join('\n');
    });
    
    // Remove paragraph tags
    wiki = wiki.replace(/<p.*?>([\s\S]*?)<\/p>/g, '$1\n\n');
    
    // Remove line breaks before newlines
    wiki = wiki.replace(/\s*\n/g, '\n');
    
    // Remove extra newlines
    wiki = wiki.replace(/\n{3,}/g, '\n\n');
    
    return wiki.trim();
}
