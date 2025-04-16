// static/js/wiki-editor-backend-integration.js

/**
 * Wiki Editor Backend Integration
 * 
 * This file provides the connection between the frontend wiki editor
 * and the backend API for sending/receiving wiki content.
 */

// Function to fetch preview from backend
export async function getServerPreview(content, summary, callback) {
    try {
        const token = localStorage.getItem('token');
        
        if (!token) {
            // Fall back to client-side preview if no token
            const clientPreviewHtml = transformWikiMarkupLocally(content, summary);
            callback(clientPreviewHtml);
            return;
        }
        
        // Prepare content with short description if needed
        let previewContent = content;
        if (summary && !content.includes('{{Short description|')) {
            previewContent = `{{Short description|${summary}}}\n\n${content}`;
        }
        
        // Request preview from server
        const response = await fetch('/api/preview', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ content: previewContent })
        });
        
        if (!response.ok) {
            throw new Error('Preview request failed');
        }
        
        const data = await response.json();
        callback(data.html);
    } catch (error) {
        console.error('Error getting server preview:', error);
        // Fall back to client-side preview
        const clientPreviewHtml = transformWikiMarkupLocally(content, summary);
        callback(clientPreviewHtml);
    }
}

// Simple local transformation for wiki markup (fallback if server is unavailable)
function transformWikiMarkupLocally(content, summary) {
    let html = content;
    
    // Add short description if needed
    if (summary && !html.includes('{{Short description|')) {
        html = `<div class="wiki-short-description">${summary}</div>\n\n${html}`;
    } else {
        const shortDescMatch = html.match(/\{\{Short description\|(.*?)\}\}/);
        if (shortDescMatch) {
            html = html.replace(shortDescMatch[0], `<div class="wiki-short-description">${shortDescMatch[1]}</div>`);
        }
    }
    
    // Basic transformations
    html = html.replace(/'''(.*?)'''/g, '<strong>$1</strong>');
    html = html.replace(/''(.*?)''/g, '<em>$1</em>');
    html = html.replace(/=== (.*?) ===/g, '<h3>$1</h3>');
    html = html.replace(/== (.*?) ==/g, '<h2>$1</h2>');
    html = html.replace(/= (.*?) =/g, '<h1>$1</h1>');
    
    // Links
    html = html.replace(/\[\[(.*?)\]\]/g, '<a href="/articles/$1">$1</a>');
    html = html.replace(/\[\[(.*?)\|(.*?)\]\]/g, '<a href="/articles/$1">$2</a>');
    
    // Format paragraphs
    const paragraphs = html.split('\n\n').map(para => {
        if (para.trim() && !para.trim().startsWith('<')) {
            return `<p>${para}</p>`;
        }
        return para;
    }).join('\n\n');
    
    return paragraphs;
}

// Save article function
export async function saveArticleContent(articleId, content, summary, title, categories, tags, editComment) {
    const token = localStorage.getItem('token');
    
    if (!token) {
        throw new Error('You must be logged in to save articles');
    }
    
    // Process content to ensure it has the short description
    let processedContent = content;
    if (summary && !processedContent.includes('{{Short description|')) {
        processedContent = `{{Short description|${summary}}}\n\n${processedContent}`;
    }
    
    // Build API request data
    const articleData = {
        content: processedContent,
        summary: summary
    };
    
    // Add optional fields if they're provided
    if (title) articleData.title = title;
    if (categories) articleData.categories = categories;
    if (tags) articleData.tags = tags;
    if (editComment) articleData.editComment = editComment;
    
    // Use POST for new articles, PUT for existing ones
    const method = articleId ? 'PUT' : 'POST';
    const url = articleId ? `/api/articles/${articleId}` : '/api/articles';
    
    const response = await fetch(url, {
        method: method,
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(articleData)
    });
    
    if (!response.ok) {
        // Handle error response
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to save article');
    }
    
    return await response.json();
}

// Create proposal function
export async function createEditProposal(articleId, content, summary) {
    const token = localStorage.getItem('token');
    
    if (!token) {
        throw new Error('You must be logged in to create edit proposals');
    }
    
    // Ensure the content has a proper short description
    let processedContent = content;
    if (summary && !processedContent.includes('{{Short description|')) {
        processedContent = `{{Short description|${summary}}}\n\n${processedContent}`;
    }
    
    const proposalData = {
        content: processedContent,
        summary: summary
    };
    
    const response = await fetch(`/api/articles/${articleId}/proposals`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(proposalData)
    });
    
    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to create edit proposal');
    }
    
    return await response.json();
}

// Initialize the connection to backend services
export function initializeBackendConnection() {
    console.log('Wiki Editor Backend Integration initialized');
    
    // This could include setting up event handlers for auto-saving,
    // or other initialization tasks
}