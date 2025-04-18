// File: static/js/wiki-editor/component-registry.js
/**
 * Component Registry for Wiki Editor
 * 
 * This file manages the registration of all editor components,
 * ensuring they're properly initialized when needed.
 */

// Import all dialogs and components
import { createCitationDialog } from './components/citation-dialog.js';
import { createReferenceDialog } from './components/reference-dialog.js';
import { createTableDialog } from './components/table-dialog.js';
import { createTemplateGallery } from './components/template-gallery.js';
import { createSearchReplaceDialog } from './components/search-replace-dialog.js';
import { createImageDialog } from './components/image-dialog.js';
import { createHeadingDialog } from './components/heading-dialog.js';
import { createLinkDialog } from './components/link-dialog.js';

// Registry of all component creators
const componentCreators = {
    'citation-dialog': createCitationDialog,
    'reference-dialog': createReferenceDialog,
    'table-dialog': createTableDialog,
    'template-gallery': createTemplateGallery,
    'search-replace-dialog': createSearchReplaceDialog,
    'image-dialog': createImageDialog,
    'heading-dialog': createHeadingDialog,
    'link-dialog': createLinkDialog
};

// Registry of created component instances
const componentInstances = {};

/**
 * Register all editor components for use
 */
export function registerEditorComponents() {
    // No initialization needed at this point
    // Components will be created on demand
    console.log('Registering editor components');
    Object.keys(componentCreators).forEach(key => {
        console.log(`Component registered: ${key}`);
    });
}

/**
 * Get or create a component by name
 * @param {string} componentName - Name of the component to retrieve
 * @returns {HTMLElement} The component DOM element
 */
export function getComponent(componentName) {
    // If component doesn't exist yet, create it
    if (!componentInstances[componentName]) {
        if (componentCreators[componentName]) {
            try {
                componentInstances[componentName] = componentCreators[componentName]();
                console.log(`Component created: ${componentName}`);
            } catch (e) {
                console.error(`Error creating component ${componentName}:`, e);
                return null;
            }
        } else {
            console.error(`Component "${componentName}" not found in registry`);
            return null;
        }
    }
    
    return componentInstances[componentName];
}

/**
 * Check if a component has been created
 * @param {string} componentName - Name of the component to check
 * @returns {boolean} True if the component exists
 */
export function hasComponent(componentName) {
    return !!componentInstances[componentName];
}

/**
 * Get all registered component names
 * @returns {Array<string>} Array of component names
 */
export function getComponentNames() {
    return Object.keys(componentCreators);
}

// Export functions
export default {
    registerEditorComponents,
    getComponent,
    hasComponent,
    getComponentNames
};
