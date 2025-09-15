// File: static/js/wiki-editor/utils/namespace.js
/**
 * Namespace utilities for the wiki editor
 */

/**
 * Valid namespaces configuration
 */
export const NAMESPACES = {
    '': {
        name: 'Main',
        description: 'Main content namespace for articles',
        urlPrefix: '/articles',
        searchable: true,
        allowCategories: true
    },
    'Category': {
        name: 'Category',
        description: 'Category organization pages',
        urlPrefix: '/categories',
        searchable: true,
        allowCategories: false
    },
    'Template': {
        name: 'Template',
        description: 'Reusable template content',
        urlPrefix: '/templates',
        searchable: false,
        allowCategories: true
    },
    'Help': {
        name: 'Help',
        description: 'Help and documentation pages',
        urlPrefix: '/help',
        searchable: true,
        allowCategories: true
    },
    'User': {
        name: 'User',
        description: 'User pages and subpages',
        urlPrefix: '/users',
        searchable: false,
        allowCategories: false
    },
    'File': {
        name: 'File',
        description: 'File description pages',
        urlPrefix: '/media',
        searchable: true,
        allowCategories: true
    },
    'Kryptopedia': {
        name: 'Kryptopedia',
        description: 'Project-related pages',
        urlPrefix: '/project',
        searchable: true,
        allowCategories: true
    },
    'Talk': {
        name: 'Talk',
        description: 'Discussion pages',
        urlPrefix: '/talk',
        searchable: false,
        allowCategories: false
    }
};

/**
 * Parse namespace from a title
 * @param {string} title - Full title with potential namespace
 * @returns {Object} Object with namespace and title properties
 */
export function parseNamespaceTitle(title) {
    if (title.includes(':')) {
        const [potentialNamespace, ...titleParts] = title.split(':');
        
        if (NAMESPACES[potentialNamespace]) {
            return {
                namespace: potentialNamespace,
                title: titleParts.join(':').trim(),
                fullTitle: title
            };
        }
    }
    
    // No valid namespace found
    return {
        namespace: '',
        title: title.trim(),
        fullTitle: title
    };
}

/**
 * Format title with namespace
 * @param {string} namespace - The namespace (empty for main)
 * @param {string} title - The title
 * @returns {string} Formatted full title
 */
export function formatNamespaceTitle(namespace, title) {
    if (namespace) {
        return `${namespace}:${title}`;
    }
    return title;
}

/**
 * Get URL for a namespace and title
 * @param {string} namespace - The namespace
 * @param {string} title - The title
 * @returns {string} URL path
 */
export function getNamespaceUrl(namespace, title) {
    const urlTitle = title.replace(/ /g, '_');
    const config = NAMESPACES[namespace] || NAMESPACES[''];
    return `${config.urlPrefix}/${urlTitle}`;
}

/**
 * Check if namespace is valid
 * @param {string} namespace - Namespace to check
 * @returns {boolean} True if valid
 */
export function isValidNamespace(namespace) {
    return namespace in NAMESPACES;
}

/**
 * Get namespace display name
 * @param {string} namespace - Namespace key
 * @returns {string} Display name
 */
export function getNamespaceDisplayName(namespace) {
    const config = NAMESPACES[namespace];
    return config ? config.name : 'Unknown';
}

/**
 * Check if namespace allows categories
 * @param {string} namespace - Namespace to check
 * @returns {boolean} True if categories are allowed
 */
export function namespaceAllowsCategories(namespace) {
    const config = NAMESPACES[namespace];
    return config ? config.allowCategories : false;
}

/**
 * Get searchable namespaces
 * @returns {Array} Array of searchable namespace keys
 */
export function getSearchableNamespaces() {
    return Object.keys(NAMESPACES).filter(ns => NAMESPACES[ns].searchable);
}

/**
 * Extract namespace references from content
 * @param {string} content - Wiki markup content
 * @returns {Array} Array of namespace references
 */
export function extractNamespaces(content) {
    const namespaces = new Set();
    
    // Find all internal links that might have namespaces
    const linkPattern = /\[\[([^\]|]+)(?:\|[^\]]*)?\]\]/g;
    let match;
    
    while ((match = linkPattern.exec(content)) !== null) {
        const linkTarget = match[1];
        const parsed = parseNamespaceTitle(linkTarget);
        
        if (parsed.namespace) {
            namespaces.add(parsed.namespace);
        }
    }
    
    return Array.from(namespaces);
}

/**
 * Suggest appropriate namespace based on title patterns
 * @param {string} title - The page title
 * @returns {string} Suggested namespace (empty string for main)
 */
export function suggestNamespaceForTitle(title) {
    const titleLower = title.toLowerCase();
    
    // Category pattern
    if (titleLower.startsWith('category')) {
        return 'Category';
    }
    
    // Template pattern  
    if (titleLower.startsWith('template')) {
        return 'Template';
    }
        
    // Help pattern
    if (['help', 'guide', 'tutorial', 'how to'].some(word => titleLower.includes(word))) {
        return 'Help';
    }
        
    // User pattern
    if (titleLower.startsWith('user')) {
        return 'User';
    }
        
    // File pattern
    if (['.jpg', '.png', '.gif', '.svg', '.pdf', '.doc'].some(ext => titleLower.includes(ext))) {
        return 'File';
    }
        
    // Project pattern
    if (['kryptopedia', 'policy', 'guideline', 'project'].some(word => titleLower.includes(word))) {
        return 'Kryptopedia';
    }
        
    // Default to main namespace
    return '';
}

/**
 * Validate namespace for a title
 * @param {string} namespace - Namespace to validate
 * @param {string} title - Title to validate
 * @returns {Object} Validation result
 */
export function validateNamespace(namespace, title) {
    const result = {
        valid: true,
        warnings: [],
        errors: []
    };
    
    // Check if namespace exists
    if (namespace && !isValidNamespace(namespace)) {
        result.valid = false;
        result.errors.push(`Invalid namespace: ${namespace}`);
        return result;
    }
    
    // Check namespace-specific rules
    const config = NAMESPACES[namespace] || NAMESPACES[''];
    
    // Category namespace should have category-like titles
    if (namespace === 'Category' && !title.match(/^[A-Z]/)) {
        result.warnings.push('Category titles should start with a capital letter');
    }
    
    // Template namespace recommendations
    if (namespace === 'Template' && title.includes(' ')) {
        result.warnings.push('Template names should avoid spaces when possible');
    }
    
    // File namespace should have file extensions
    if (namespace === 'File' && !title.match(/\.[a-zA-Z0-9]+$/)) {
        result.warnings.push('File pages should include file extensions');
    }
    
    return result;
}
