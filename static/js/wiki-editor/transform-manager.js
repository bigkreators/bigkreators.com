/**
 * Transform Manager for Wiki Editor
 * 
 * This file coordinates the transformation of wiki markup to HTML for previews.
 */

import { transformFormatting, transformLists } from './format-handler.js';
import { transformHeadings } from './heading-handler.js';
import { transformLinks } from './link-handler.js';
import { transformImages } from './image-handler.js';
import { transformTables } from './table-handler.js';
import { transformReferences } from './citation-handler.js';

/**
 * Transform wiki markup to HTML
 * @param {string} markup - The wiki markup to transform
 * @returns {object} Object containing HTML and extracted short description
 */
export function transformWikiMarkup(markup) {
    // Extract short description if present
    let shortDescription = null;
    const shortDescMatch = /\{\{Short description\|(.*?)\}\}/g.exec(markup);
    if (shortDescMatch) {
        shortDescription = shortDescMatch[1].trim();
        markup = markup.replace(shortDescMatch[0], '');
    }

    // Apply transformations in sequence
    let html = markup;
    
    // Format text (bold, italic, etc.)
    html = transformFormatting(html);
    
    // Transform headings
    html = transformHeadings(html);
    
    // Transform links
    html = transformLinks(html);
    
    // Transform lists
    html = transformLists(html);
    
    // Transform tables
    html = transformTables(html);
    
    // Transform images
    html = transformImages(html);
    
    // Transform references
    html = transformReferences(html);
    
    // Handle templates
    html = transformTemplates(html);
    
    // Handle paragraphs
    html = transformParagraphs(html);

    return { html, shortDescription };
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
        const blockElements = ['<h1', '<h2', '<h3', '<h
