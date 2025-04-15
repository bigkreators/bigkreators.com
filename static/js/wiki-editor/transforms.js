/**
 * Wiki Markup Transformations
 * 
 * This file contains functions for transforming wiki markup to HTML
 * and handling various wiki syntax elements.
 */

/**
 * Transform wiki markup to HTML
 * @param {string} markup - The wiki markup to transform
 * @returns {string} HTML version of the markup
 */
export function transformWikiMarkup(markup) {
    // This is a client-side transformation for preview purposes
    // The server should handle the full transformation
    let html = markup;

    // Extract short description if present
    let shortDescription = null;
    const shortDescMatch = /\{\{Short description\|(.*?)\}\}/g.exec(html);
    if (shortDescMatch) {
        shortDescription = shortDescMatch[1].trim();
        html = html.replace(shortDescMatch[0], '');
    }

    // Handle text formatting
    html = html.replace(/'''(.*?)'''/g, '<strong>$1</strong>');
    html = html.replace(/''(.*?)''/g, '<em>$1</em>');
    html = html.replace(/<u>(.*?)<\/u>/g, '<u>$1</u>');
    html = html.replace(/<s>(.*?)<\/s>/g, '<s>$1</s>');
    html = html.replace(/<sup>(.*?)<\/sup>/g, '<sup>$1</sup>');
    html = html.replace(/<sub>(.*?)<\/sub>/g, '<sub>$1</sub>');

    // Handle headings
    html = html.replace(/======\s*(.*?)\s*======/g, '<h6>$1</h6>');
    html = html.replace(/=====\s*(.*?)\s*=====/g, '<h5>$1</h5>');
    html = html.replace(/====\s*(.*?)\s*====/g, '<h4>$1</h4>');
    html = html.replace(/===\s*(.*?)\s*===/g, '<h3>$1</h3>');
    html = html.replace(/==\s*(.*?)\s*==/g, '<h2>$1</h2>');
    html = html.replace(/=\s*(.*?)\s*=/g, '<h1>$1</h1>');

    // Handle links
    // Internal links [[Page name]]
    html = html.replace(/\[\[(.*?)\]\]/g, '<a href="/articles/$1">$1</a>');
    // Internal links with display text [[Page name|Display text]]
    html = html.replace(/\[\[(.*?)\|(.*?)\]\]/g, '<a href="/articles/$1">$2</a>');
    // External links [http://example.com Display text]
    html = html.replace(/\[(https?:\/\/[^\s\]]+)\s+(.*?)\]/g, '<a href="$1" target="_blank">$2</a>');
    // External links without display text [http://example.com]
    html = html.replace(/\[(https?:\/\/[^\s\]]+)\]/g, '<a href="$1" target="_blank">$1</a>');

    // Handle lists
    const lines = html.split('\n');
    let inList = false;
    let listType = null;
    let result = [];

    for (let i = 0; i < lines.length; i++) {
        const line = lines[i];
        
        // Unordered list
        if (line.startsWith('* ')) {
            if (!inList || listType !== 'ul') {
                if (inList) {
                    result.push(`</${listType}>`);
                }
                result.push('<ul>');
                inList = true;
                listType = 'ul';
            }
            result.push(`<li>${line.substring(2)}</li>`);
        }
        // Ordered list
        else if (line.startsWith('# ')) {
            if (!inList || listType !== 'ol') {
                if (inList) {
                    result.push(`</${listType}>`);
                }
                result.push('<ol>');
                inList = true;
                listType = 'ol';
            }
            result.push(`<li>${line.substring(2)}</li>`);
        }
        // Not a list
        else {
            if (inList) {
                result.push(`</${listType}>`);
                inList = false;
                listType = null;
            }
            result.push(line);
        }
    }

    // Close any open list
    if (inList) {
        result.push(`</${listType}>`);
    }

    html = result.join('\n');

    // Handle tables
    html = transformTables(html);

    // Handle templates
    html = transformTemplates(html);

    // Handle images
    html = transformImages(html);

    // Handle references
    html = transformReferences(html);

    // Handle paragraphs
    html = transformParagraphs(html);

    return { html, shortDescription };
}

/**
 * Transform wiki table markup to HTML
 * @param {string} markup - Wiki markup containing tables
 * @returns {string} HTML with transformed tables
 */
function transformTables(markup) {
    // Match table syntax {| ... |}
    return markup.replace(/\{\|(.*?)\|\}/gs, (match, tableContent) => {
        let tableHTML = '<table class="wiki-table">';
        
        // Extract caption if present
        const captionMatch = /\|\+(.*?)(?:\n|\|-|$)/s.exec(tableContent);
        if (captionMatch) {
            tableHTML += `<caption>${captionMatch[1].trim()}</caption>`;
            tableContent = tableContent.replace(captionMatch[0], '');
        }
        
        // Split into rows by |-
        const rows = tableContent.split(/\|-/);
        
        // Process each row
        rows.forEach((row, index) => {
            if (index === 0 && !row.trim()) return; // Skip empty first row
            
            tableHTML += '<tr>';
            
            // Find all header cells
            const headerCells = row.match(/\!(.*?)(?:\!|$)/gs);
            if (headerCells) {
                headerCells.forEach(cell => {
                    const content = cell.replace(/^\!/, '').trim();
                    if (content) {
                        tableHTML += `<th>${content}</th>`;
                    }
                });
            }
            
            // Find all data cells
            const dataCells = row.match(/\|(.*?)(?:\||$)/gs);
            if (dataCells) {
                dataCells.forEach(cell => {
                    const content = cell.replace(/^\|/, '').trim();
                    if (content) {
                        tableHTML += `<td>${content}</td>`;
                    }
                });
            }
            
            tableHTML += '</tr>';
        });
        
        tableHTML += '</table>';
        return tableHTML;
    });
}

/**
 * Transform wiki template markup to HTML
 * @param {string} markup - Wiki markup containing templates
 * @returns {string} HTML with transformed templates
 */
function transformTemplates(markup) {
    // Match template syntax {{template}}
    return markup.replace(/\{\{([^{}]+?)(?:\|(.*?))?\}\}/gs, (match, templateName, params) => {
        templateName = templateName.trim();
        const paramMap = {};
        
        // Parse parameters
        if (params) {
            const paramPairs = params.split('|');
            let position = 1;
            
            paramPairs.forEach(pair => {
                if (pair.includes('=')) {
                    const [key, value] = pair.split('=', 2);
                    paramMap[key.trim()] = value.trim();
                } else {
                    paramMap[position.toString()] = pair.trim();
                    position++;
                }
            });
        }
        
        // Handle different template types
        switch (templateName.toLowerCase()) {
            case 'infobox':
                return renderInfobox(paramMap);
                
            case 'quote':
                return renderQuote(paramMap);
                
            case 'cite':
            case 'cite web':
            case 'cite book':
            case 'cite journal':
                return renderCitation(templateName, paramMap);
                
            case 'shortdescription':
            case 'short description':
                // Already handled separately
                return '';
                
            default:
                // Generic template rendering
                return `<div class="wiki-template"><strong>${templateName}</strong>${
                    Object.entries(paramMap).map(([k, v]) => 
                        `<div><strong>${k}:</strong> ${v}</div>`
                    ).join('')
                }</div>`;
        }
    });
}

/**
 * Render infobox template as HTML
 * @param {Object} params - Template parameters
 * @returns {string} HTML infobox
 */
function renderInfobox(params) {
    let html = '<table class="wiki-infobox">';
    
    // Title row
    if (params.title) {
        html += `<tr><th colspan="2" class="wiki-infobox-title">${params.title}</th></tr>`;
    }
    
    // Image row
    if (params.image) {
        const caption = params.caption || '';
        html += '<tr><td colspan="2" class="wiki-infobox-image">';
        html += `<img src="/media/${params.image}" alt="${caption}">`;
        if (caption) {
            html += `<div>${caption}</div>`;
        }
        html += '</td></tr>';
    }
    
    // Data rows
    let i = 1;
    while (params[`label${i}`]) {
        const label = params[`label${i}`];
        const data = params[`data${i}`] || '';
        html += `<tr><th class="wiki-infobox-label">${label}</th><td class="wiki-infobox-data">${data}</td></tr>`;
        i++;
    }
    
    html += '</table>';
    return html;
}

/**
 * Render quote template as HTML
 * @param {Object} params - Template parameters
 * @returns {string} HTML blockquote
 */
function renderQuote(params) {
    const text = params.text || params['1'] || '';
    const author = params.author || params['2'] || '';
    const source = params.source || params['3'] || '';
    const year = params.year || params['4'] || '';
    
    let html = `<blockquote class="wiki-quote"><p>${text}</p>`;
    
    if (author || source || year) {
        html += '<footer>';
        if (author) {
            html += `<cite>${author}</cite>`;
        }
        if (source) {
            html += author ? `, ${source}` : source;
        }
        if (year) {
            html += ` (${year})`;
        }
        html += '</footer>';
    }
    
    html += '</blockquote>';
    return html;
}

/**
 * Render citation template as HTML
 * @param {string} type - Citation type
 * @param {Object} params - Template parameters
 * @returns {string} HTML citation
 */
function renderCitation(type, params) {
    const citationType = type.replace(/^cite\s+/, '');
    
    switch (citationType.toLowerCase()) {
        case 'web':
            return renderWebCitation(params);
        case 'book':
            return renderBookCitation(params);
        case 'journal':
            return renderJournalCitation(params);
        default:
            return renderGenericCitation(params);
    }
}

/**
 * Render web citation
 * @param {Object} params - Citation parameters
 * @returns {string} HTML citation
 */
function renderWebCitation(params) {
    const title = params.title || '';
    const url = params.url || '';
    const author = params.author || '';
    const website = params.website || '';
    const date = params.date || '';
    const accessDate = params['access-date'] || params.accessdate || '';
    
    let html = '<span class="wiki-citation">';
    
    if (author) {
        html += `${author}. `;
    }
    
    if (title) {
        if (url) {
            html += `"<a href="${url}" target="_blank" rel="noopener">${title}</a>". `;
        } else {
            html += `"${title}". `;
        }
    }
    
    if (website) {
        html += `<em>${website}</em>. `;
    }
    
    if (date) {
        html += `${date}. `;
    }
    
    if (accessDate) {
        html += `Retrieved ${accessDate}.`;
    }
    
    html += '</span>';
    return html;
}

/**
 * Render book citation
 * @param {Object} params - Citation parameters
 * @returns {string} HTML citation
 */
function renderBookCitation(params) {
    const title = params.title || '';
    const author = params.author || '';
    const publisher = params.publisher || '';
    const year = params.year || '';
    const pages = params.pages || '';
    const isbn = params.isbn || '';
    
    let html = '<span class="wiki-citation">';
    
    if (author) {
        html += `${author}. `;
    }
    
    if (title) {
        html += `<em>${title}</em>. `;
    }
    
    if (publisher) {
        html += `${publisher}`;
        if (year) {
            html += `, ${year}`;
        }
        html += `. `;
    } else if (year) {
        html += `${year}. `;
    }
    
    if (pages) {
        html += `pp. ${pages}. `;
    }
    
    if (isbn) {
        html += `ISBN: ${isbn}`;
    }
    
    html += '</span>';
    return html;
}

/**
 * Render journal citation
 * @param {Object} params - Citation parameters
 * @returns {string} HTML citation
 */
function renderJournalCitation(params) {
    const title = params.title || '';
    const author = params.author || '';
    const journal = params.journal || '';
    const volume = params.volume || '';
    const issue = params.issue || '';
    const year = params.year || '';
    const pages = params.pages || '';
    const doi = params.doi || '';
    
    let html = '<span class="wiki-citation">';
    
    if (author) {
        html += `${author}. `;
    }
    
    if (title) {
        html += `"${title}". `;
    }
    
    if (journal) {
        html += `<em>${journal}</em>`;
        
        if (volume) {
            html += ` ${volume}`;
            if (issue) {
                html += `(${issue})`;
            }
        }
        
        if (year) {
            html += ` (${year})`;
        }
        
        html += `. `;
    }
    
    if (pages) {
        html += `pp. ${pages}. `;
    }
    
    if (doi) {
        html += `DOI: ${doi}`;
    }
    
    html += '</span>';
    return html;
}

/**
 * Render generic citation
 * @param {Object} params - Citation parameters
 * @returns {string} HTML citation
 */
function renderGenericCitation(params) {
    let html = '<span class="wiki-citation">';
    
    // Try to make a reasonable citation from available params
    if (params.author) {
        html += `${params.author}. `;
    }
    
    if (params.title) {
        html += `"${params.title}". `;
    }
    
    if (params.source) {
        html += `<em>${params.source}</em>. `;
    }
    
    if (params.date || params.year) {
        html += `${params.date || params.year}. `;
    }
    
    html += '</span>';
    return html;
}

/**
 * Transform wiki image markup to HTML
 * @param {string} markup - Wiki markup containing images
 * @returns {string} HTML with transformed images
 */
function transformImages(markup) {
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

/**
 * Transform wiki reference markup to HTML
 * @param {string} markup - Wiki markup containing references
 * @returns {string} HTML with transformed references
 */
function transformReferences(markup) {
    // References collection
    const references = [];
    
    // Replace reference tags
    let html = markup.replace(/<ref(?:\s+name\s*=\s*"([^"]+)")?\s*>(.*?)<\/ref>/gs, (match, name, content) => {
        const index = references.length + 1;
        references.push({
            id: index,
            name: name,
            content: content.trim()
        });
        
        return `<sup class="wiki-reference">[<a href="#ref-${index}">${index}</a>]</sup>`;
    });
    
    // Replace reference list placeholder
    html = html.replace(/<references\s*\/>/g, () => {
        if (references.length === 0) return '';
        
        let refList = '<div class="wiki-references"><h2>References</h2><ol>';
        references.forEach(ref => {
            refList += `<li id="ref-${ref.id}">${ref.content}</li>`;
        });
        refList += '</ol></div>';
        
        return refList;
    });
    
    return html;
}

/**
 * Transform wiki markup paragraphs to HTML
 * @param {string} markup - Wiki markup
 * @returns {string} HTML with proper paragraphs
 */
function transformParagraphs(markup) {
    // Split by double newlines to identify paragraphs
    const paragraphs = markup.split(/\n\n+/);
    
    // Wrap each non-empty paragraph in <p> tags, unless it's already wrapped in a block-level element
    const processed = paragraphs.map(para => {
        const trimmed = para.trim();
        if (!trimmed) return '';
        
        // Skip paragraphs that already start with block-level HTML elements
        const blockElements = ['<h1', '<h2', '<h3', '<h4', '<h5', '<h6', '<div', '<table', 
                             '<ul', '<ol', '<blockquote', '<figure', '<pre'];
        
        if (blockElements.some(el => trimmed.startsWith(el))) {
            return trimmed;
        }
        
        return `<p>${trimmed}</p>`;
    });
    
    return processed.join('\n\n');
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
