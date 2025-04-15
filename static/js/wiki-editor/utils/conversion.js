// File: static/js/wiki-editor/utils/conversion.js
/**
 * Conversion Utilities for Wiki Editor
 * 
 * This file provides utilities for converting between HTML and wiki markup,
 * helping users migrating between the two formats.
 */

/**
 * Convert HTML content to wiki markup
 * @param {string} html - HTML content to convert
 * @returns {string} Wiki markup
 */
export function htmlToWikiMarkup(html) {
    let wiki = html;
    
    // Remove any DOCTYPE, html, head, and body tags
    wiki = wiki.replace(/<\!DOCTYPE[^>]*>/i, '');
    wiki = wiki.replace(/<html[^>]*>|<\/html>/gi, '');
    wiki = wiki.replace(/<head[^>]*>.*?<\/head>/gis, '');
    wiki = wiki.replace(/<body[^>]*>|<\/body>/gi, '');
    
    // Format headings
    wiki = wiki.replace(/<h1[^>]*>(.*?)<\/h1>/gi, '= $1 =');
    wiki = wiki.replace(/<h2[^>]*>(.*?)<\/h2>/gi, '== $1 ==');
    wiki = wiki.replace(/<h3[^>]*>(.*?)<\/h3>/gi, '=== $1 ===');
    wiki = wiki.replace(/<h4[^>]*>(.*?)<\/h4>/gi, '==== $1 ====');
    wiki = wiki.replace(/<h5[^>]*>(.*?)<\/h5>/gi, '===== $1 =====');
    wiki = wiki.replace(/<h6[^>]*>(.*?)<\/h6>/gi, '====== $1 ======');
    
    // Format basic text styling
    wiki = wiki.replace(/<strong[^>]*>(.*?)<\/strong>/gi, "'''$1'''");
    wiki = wiki.replace(/<b[^>]*>(.*?)<\/b>/gi, "'''$1'''");
    wiki = wiki.replace(/<em[^>]*>(.*?)<\/em>/gi, "''$1''");
    wiki = wiki.replace(/<i[^>]*>(.*?)<\/i>/gi, "''$1''");
    
    // Handle links
    // Internal links
    wiki = wiki.replace(/<a[^>]*href=["']\/articles\/(.*?)["'][^>]*>(.*?)<\/a>/gi, (match, p1, p2) => {
        if (p1 === p2) {
            return `[[${p1}]]`;
        } else {
            return `[[${p1}|${p2}]]`;
        }
    });
    
    // External links
    wiki = wiki.replace(/<a[^>]*href=["'](https?:\/\/.*?)["'][^>]*>(.*?)<\/a>/gi, (match, p1, p2) => {
        if (p1 === p2) {
            return `[${p1}]`;
        } else {
            return `[${p1} ${p2}]`;
        }
    });
    
    // Format lists
    // Process lists step by step, handling nesting
    let tempWiki = '';
    let inOrderedList = false;
    let inUnorderedList = false;
    let listDepth = 0;
    
    // Split by lines to handle lists
    const lines = wiki.split('\n');
    
    for (let i = 0; i < lines.length; i++) {
        let line = lines[i].trim();
        
        // Detect list item starts
        if (line.match(/<li[^>]*>/i)) {
            let prefix = '';
            
            // Determine if we're in an ordered or unordered list
            let parentUL = line.match(/<ul[^>]*>/i);
            let parentOL = line.match(/<ol[^>]*>/i);
            
            if (parentUL) {
                inUnorderedList = true;
                listDepth++;
                prefix = '*'.repeat(listDepth) + ' ';
            } else if (parentOL) {
                inOrderedList = true;
                listDepth++;
                prefix = '#'.repeat(listDepth) + ' ';
            } else if (inUnorderedList) {
                prefix = '*'.repeat(listDepth) + ' ';
            } else if (inOrderedList) {
                prefix = '#'.repeat(listDepth) + ' ';
            }
            
            // Extract the content of the list item
            let content = line.replace(/<li[^>]*>(.*?)<\/li>/i, '$1');
            // Remove other tags
            content = content.replace(/<[^>]*>/g, '');
            
            tempWiki += prefix + content + '\n';
        }
        // Detect list endings
        else if (line.match(/<\/ul>|<\/ol>/i)) {
            listDepth = Math.max(0, listDepth - 1);
            if (listDepth === 0) {
                inOrderedList = false;
                inUnorderedList = false;
            }
            // Skip this line as we've handled the list ending
        }
        // Not a list element
        else if (!line.match(/<ul[^>]*>|<ol[^>]*>/i)) {
            // Remove remaining HTML tags
            line = line.replace(/<[^>]+>/g, '');
            if (line.trim()) {
                tempWiki += line + '\n';
            }
        }
    }
    
    // Use the processed lists version
    wiki = tempWiki;
    
    // Handle tables
    // This is a simple conversion - complex tables might need manual adjustment
    if (wiki.includes('<table')) {
        const tableRegex = /<table[^>]*>([\s\S]*?)<\/table>/gi;
        let tableMatch;
        
        while ((tableMatch = tableRegex.exec(html)) !== null) {
            const tableContent = tableMatch[1];
            let wikiTable = '{| class="wikitable"\n';
            
            // Handle caption if present
            const captionMatch = tableContent.match(/<caption[^>]*>([\s\S]*?)<\/caption>/i);
            if (captionMatch) {
                wikiTable += `|+ ${captionMatch[1].trim()}\n`;
            }
            
            // Handle rows
            const rows = tableContent.match(/<tr[^>]*>([\s\S]*?)<\/tr>/gi) || [];
            
            for (let i = 0; i < rows.length; i++) {
                const row = rows[i];
                wikiTable += '|-\n';
                
                // Handle header cells
                const headers = row.match(/<th[^>]*>([\s\S]*?)<\/th>/gi) || [];
                if (headers.length > 0) {
                    for (let j = 0; j < headers.length; j++) {
                        const header = headers[j].replace(/<th[^>]*>([\s\S]*?)<\/th>/i, '$1').trim();
                        wikiTable += `! ${header}`;
                        
                        if (j < headers.length - 1) {
                            wikiTable += ' !! ';
                        } else {
                            wikiTable += '\n';
                        }
                    }
                }
                
                // Handle data cells
                const cells = row.match(/<td[^>]*>([\s\S]*?)<\/td>/gi) || [];
                if (cells.length > 0) {
                    for (let j = 0; j < cells.length; j++) {
                        const cell = cells[j].replace(/<td[^>]*>([\s\S]*?)<\/td>/i, '$1').trim();
                        wikiTable += `| ${cell}`;
                        
                        if (j < cells.length - 1) {
                            wikiTable += ' || ';
                        } else {
                            wikiTable += '\n';
                        }
                    }
                }
            }
            
            wikiTable += '|}';
            wiki = wiki.replace(tableMatch[0], wikiTable);
        }
    }
    
    // Clean up extra whitespace
    wiki = wiki.replace(/\n{3,}/g, '\n\n');
    
    return wiki.trim();
}

/**
 * Convert wiki markup to HTML
 * @param {string} wiki - Wiki markup to convert
 * @returns {string} HTML content
 */
export function wikiMarkupToHtml(wiki) {
    let html = wiki;
    
    // Handle short description
    const shortDescMatch = /\{\{Short description\|(.*?)\}\}/i.exec(html);
    if (shortDescMatch) {
        const description = shortDescMatch[1].trim();
        html = html.replace(shortDescMatch[0], '');
        
        // We'll add the description at the beginning of the final HTML
        const descriptionHtml = `<div class="article-short-description">${description}</div>\n\n`;
        html = descriptionHtml + html;
    }
    
    // Format headings
    html = html.replace(/======\s*(.*?)\s*======/g, '<h6>$1</h6>');
    html = html.replace(/=====\s*(.*?)\s*=====/g, '<h5>$1</h5>');
    html = html.replace(/====\s*(.*?)\s*====/g, '<h4>$1</h4>');
    html = html.replace(/===\s*(.*?)\s*===/g, '<h3>$1</h3>');
    html = html.replace(/==\s*(.*?)\s*==/g, '<h2>$1</h2>');
    html = html.replace(/=\s*(.*?)\s*=/g, '<h1>$1</h1>');
    
    // Format basic text styling
    html = html.replace(/'''(.*?)'''/g, '<strong>$1</strong>');
    html = html.replace(/''(.*?)''/g, '<em>$1</em>');
    html = html.replace(/<u>(.*?)<\/u>/g, '<u>$1</u>'); // Already in HTML format
    html = html.replace(/<s>(.*?)<\/s>/g, '<s>$1</s>'); // Already in HTML format
    
    // Handle links
    // Internal links with display text
    html = html.replace(/\[\[(.*?)\|(.*?)\]\]/g, '<a href="/articles/$1">$2</a>');
    // Internal links
    html = html.replace(/\[\[(.*?)\]\]/g, '<a href="/articles/$1">$1</a>');
    // External links with display text
    html = html.replace(/\[(https?:\/\/[^\s\]]+)\s+(.*?)\]/g, '<a href="$1" target="_blank" rel="noopener">$2</a>');
    // External links
    html = html.replace(/\[(https?:\/\/[^\s\]]+)\]/g, '<a href="$1" target="_blank" rel="noopener">$1</a>');
    
    // Handle lists
    const lines = html.split('\n');
    let result = [];
    let inList = false;
    let listType = '';
    let listDepth = 0;
    let listStack = [];
    
    for (let i = 0; i < lines.length; i++) {
        const line = lines[i];
        
        // Unordered list
        if (line.match(/^\*+\s/)) {
            const depth = line.indexOf(' ');
            const content = line.substring(depth + 1);
            
            if (!inList) {
                // Start a new list
                result.push('<ul>');
                listStack.push('ul');
                inList = true;
                listDepth = 1;
            } else if (depth > listDepth) {
                // Deeper nesting
                for (let j = listDepth; j < depth; j++) {
                    result.push('<ul>');
                    listStack.push('ul');
                }
                listDepth = depth;
            } else if (depth < listDepth) {
                // Less nesting
                for (let j = listDepth; j > depth; j--) {
                    result.push(`</${listStack.pop()}>`);
                }
                listDepth = depth;
            }
            
            // Add the list item
            result.push(`<li>${content}</li>`);
        }
        // Ordered list
        else if (line.match(/^#+\s/)) {
            const depth = line.indexOf(' ');
            const content = line.substring(depth + 1);
            
            if (!inList) {
                // Start a new list
                result.push('<ol>');
                listStack.push('ol');
                inList = true;
                listDepth = 1;
            } else if (depth > listDepth) {
                // Deeper nesting
                for (let j = listDepth; j < depth; j++) {
                    result.push('<ol>');
                    listStack.push('ol');
                }
                listDepth = depth;
            } else if (depth < listDepth) {
                // Less nesting
                for (let j = listDepth; j > depth; j--) {
                    result.push(`</${listStack.pop()}>`);
                }
                listDepth = depth;
            }
            
            // Add the list item
            result.push(`<li>${content}</li>`);
        }
        // Not a list item
        else {
            // Close any open lists
            while (listStack.length > 0) {
                result.push(`</${listStack.pop()}>`);
            }
            inList = false;
            listDepth = 0;
            
            // Add the line
            result.push(line);
        }
    }
    
    // Close any remaining open lists
    while (listStack.length > 0) {
        result.push(`</${listStack.pop()}>`);
    }
    
    html = result.join('\n');
    
    // Handle tables
    html = html.replace(/\{\|(.*?)^\|\}/gms, (match, tableContent) => {
        let table = '<table';
        
        // Extract table attributes from the first line
        const firstLine = tableContent.trim().split('\n')[0];
        if (firstLine.includes('class=')) {
            const classMatch = firstLine.match(/class=["']([^"']+)["']/);
            if (classMatch) {
                table += ` class="${classMatch[1]}"`;
            }
        }
        
        table += '>\n';
        
        // Process table content
        const lines = tableContent.trim().split('\n');
        let inRow = false;
        
        for (let i = 1; i < lines.length; i++) {
            const line = lines[i].trim();
            
            // Caption
            if (line.startsWith('|+')) {
                table += `<caption>${line.substring(2).trim()}</caption>\n`;
            }
            // Row start
            else if (line === '|-') {
                if (inRow) {
                    table += '</tr>\n';
                }
                table += '<tr>\n';
                inRow = true;
            }
            // Header cell
            else if (line.startsWith('!')) {
                const cells = line.split('!!');
                
                for (let j = 0; j < cells.length; j++) {
                    let cell = cells[j].trim();
                    if (j === 0) {
                        cell = cell.substring(1).trim();
                    }
                    
                    table += `<th>${cell}</th>\n`;
                }
            }
            // Data cell
            else if (line.startsWith('|') && !line.startsWith('|-') && !line.startsWith('|}')) {
                const cells = line.split('||');
                
                for (let j = 0; j < cells.length; j++) {
                    let cell = cells[j].trim();
                    if (j === 0) {
                        cell = cell.substring(1).trim();
                    }
                    
                    table += `<td>${cell}</td>\n`;
                }
            }
        }
        
        // Close any open row
        if (inRow) {
            table += '</tr>\n';
        }
        
        table += '</table>';
        return table;
    });
    
    // Format paragraphs (avoid touching existing HTML tags)
    const paragraphs = html.split('\n\n');
    for (let i = 0; i < paragraphs.length; i++) {
        if (paragraphs[i].trim() && !paragraphs[i].trim().match(/^<([a-z][a-z0-9]*)\b[^>]*>|<\/([a-z][a-z0-9]*)\b[^>]*>$/i)) {
            paragraphs[i] = `<p>${paragraphs[i]}</p>`;
        }
    }
    
    html = paragraphs.join('\n\n');
    
    return html.trim();
}

/**
 * Import content from HTML to wiki format
 * @param {string} url - URL to import from
 * @returns {Promise<string>} Promise resolving to wiki markup
 */
export async function importFromHtml(url) {
    try {
        const response = await fetch(url);
        const html = await response.text();
        return htmlToWikiMarkup(html);
    } catch (error) {
        console.error('Error importing from HTML:', error);
        throw new Error('Failed to import content from HTML');
    }
}

/**
 * Export content from wiki to HTML format
 * @param {string} wiki - Wiki markup to export
 * @param {string} filename - Filename to export to
 */
export function exportToHtml(wiki, filename) {
    const html = wikiMarkupToHtml(wiki);
    
    // Create full HTML document
    const fullHtml = `<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Exported Wiki Content</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; padding: 20px; max-width: 800px; margin: 0 auto; }
        h1, h2, h3, h4, h5, h6 { margin-top: 1.5em; margin-bottom: 0.5em; }
        p { margin-bottom: 1em; }
        table { border-collapse: collapse; width: 100%; margin: 1em 0; }
        th, td { border: 1px solid #ddd; padding: 8px; }
        th { background-color: #f2f2f2; }
        .article-short-description { font-style: italic; color: #666; margin-bottom: 20px; }
    </style>
</head>
<body>
${html}
</body>
</html>`;
    
    // Create download link
    const blob = new Blob([fullHtml], { type: 'text/html' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename || 'exported-wiki.html';
    a.click();
    
    // Clean up
    URL.revokeObjectURL(url);
}

export default {
    htmlToWikiMarkup,
    wikiMarkupToHtml,
    importFromHtml,
    exportToHtml
};
