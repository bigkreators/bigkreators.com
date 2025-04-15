/**
 * Format Handler for Wiki Editor
 * 
 * This file contains functions for text formatting options.
 */

import { wrapSelectedText, prependToSelectedLines, removeIndent } from './text-utils.js';

/**
 * Apply bold formatting to selected text
 * @param {HTMLElement} textarea - The textarea element
 */
export function applyBold(textarea) {
    wrapSelectedText(textarea, "'''", "'''");
}

/**
 * Apply italic formatting to selected text
 * @param {HTMLElement} textarea - The textarea element
 */
export function applyItalic(textarea) {
    wrapSelectedText(textarea, "''", "''");
}

/**
 * Apply underline formatting to selected text
 * @param {HTMLElement} textarea - The textarea element
 */
export function applyUnderline(textarea) {
    wrapSelectedText(textarea, '<u>', '</u>');
}

/**
 * Apply strikethrough formatting to selected text
 * @param {HTMLElement} textarea - The textarea element
 */
export function applyStrikethrough(textarea) {
    wrapSelectedText(textarea, '<s>', '</s>');
}

/**
 * Apply superscript formatting to selected text
 * @param {HTMLElement} textarea - The textarea element
 */
export function applySuperscript(textarea) {
    wrapSelectedText(textarea, '<sup>', '</sup>');
}

/**
 * Apply subscript formatting to selected text
 * @param {HTMLElement} textarea - The textarea element
 */
export function applySubscript(textarea) {
    wrapSelectedText(textarea, '<sub>', '</sub>');
}

/**
 * Apply code block formatting to selected text
 * @param {HTMLElement} textarea - The textarea element
 */
export function applyCodeBlock(textarea) {
    wrapSelectedText(textarea, '<code>', '</code>');
}

/**
 * Apply math formula formatting to selected text
 * @param {HTMLElement} textarea - The textarea element
 */
export function applyMathFormula(textarea) {
    wrapSelectedText(textarea, '<math>', '</math>');
}

/**
 * Apply bullet list formatting to selected lines
 * @param {HTMLElement} textarea - The textarea element
 */
export function applyBulletList(textarea) {
    prependToSelectedLines(textarea, '* ');
}

/**
 * Apply numbered list formatting to selected lines
 * @param {HTMLElement} textarea - The textarea element
 */
export function applyNumberedList(textarea) {
    prependToSelectedLines(textarea, '# ');
}

/**
 * Apply indentation to selected lines
 * @param {HTMLElement} textarea - The textarea element
 */
export function applyIndent(textarea) {
    prependToSelectedLines(textarea, ':');
}

/**
 * Remove indentation from selected lines
 * @param {HTMLElement} textarea - The textarea element
 */
export function applyOutdent(textarea) {
    removeIndent(textarea);
}

/**
 * Apply left alignment to selected text
 * @param {HTMLElement} textarea - The textarea element
 */
export function applyAlignLeft(textarea) {
    wrapSelectedText(textarea, '<div style="text-align:left">', '</div>');
}

/**
 * Apply center alignment to selected text
 * @param {HTMLElement} textarea - The textarea element
 */
export function applyAlignCenter(textarea) {
    wrapSelectedText(textarea, '<div style="text-align:center">', '</div>');
}

/**
 * Apply right alignment to selected text
 * @param {HTMLElement} textarea - The textarea element
 */
export function applyAlignRight(textarea) {
    wrapSelectedText(textarea, '<div style="text-align:right">', '</div>');
}

/**
 * Transform text formatting for preview
 * @param {string} markup - Wiki markup with text formatting
 * @returns {string} HTML with transformed formatting
 */
export function transformFormatting(markup) {
    let html = markup;
    
    // Handle text formatting
    html = html.replace(/'''(.*?)'''/g, '<strong>$1</strong>'); // Bold
    html = html.replace(/''(.*?)''/g, '<em>$1</em>'); // Italic
    html = html.replace(/<u>(.*?)<\/u>/g, '<u>$1</u>'); // Underline (already HTML)
    html = html.replace(/<s>(.*?)<\/s>/g, '<s>$1</s>'); // Strikethrough (already HTML)
    html = html.replace(/<sup>(.*?)<\/sup>/g, '<sup>$1</sup>'); // Superscript (already HTML)
    html = html.replace(/<sub>(.*?)<\/sub>/g, '<sub>$1</sub>'); // Subscript (already HTML)
    html = html.replace(/<code>(.*?)<\/code>/g, '<code>$1</code>'); // Code (already HTML)
    html = html.replace(/<math>(.*?)<\/math>/g, '<span class="math">$1</span>'); // Math formula
    
    return html;
}

/**
 * Transform lists for preview
 * @param {string} markup - Wiki markup containing lists
 * @returns {string} HTML with transformed lists
 */
export function transformLists(markup) {
    const lines = markup.split('\n');
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

    return result.join('\n');
}
