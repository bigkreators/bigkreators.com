// File: static/js/wiki-editor-init.js
/**
 * Wiki Editor Initialization Script
 * 
 * This file ensures the wiki editor is properly initialized on pages
 * that need it, handling the integration with the existing application.
 */

document.addEventListener('DOMContentLoaded', function() {
    // Check if we're in wiki mode
    const urlParams = new URLSearchParams(window.location.search);
    const currentMode = urlParams.get('mode') || 'wiki';
    
    if (currentMode === 'wiki') {
        // Dynamically import the wiki editor module
        import('./wiki-editor/index.js')
            .then(module => {
                console.log('Wiki Editor module loaded successfully');
                
                // Add mode toggle
                module.addModeToggle();
                
                // Initialize wiki editor on supported forms
                const supportedForms = [
                    'create-article-form',
                    'edit-article-form', 
                    'propose-edit-form',
                    'talk-page-form',
                    'quick-edit-form'
                ];
                
                supportedForms.forEach(formId => {
                    const form = document.getElementById(formId);
                    if (form) {
                        module.initializeWikiEditor(form);
                    }
                });
                
                // Add line numbers to article content textareas
                const contentTextareas = document.querySelectorAll('#article-content');
                contentTextareas.forEach(textarea => {
                    module.addLineNumbers(textarea);
                });
            })
            .catch(error => {
                console.error('Error loading Wiki Editor module:', error);
            });
    } else {
        // In HTML mode, we might need to disable wiki features or ensure HTML editors are loaded
        if (typeof $ !== 'undefined' && $.fn.summernote) {
            // Initialize Summernote WYSIWYG editor if available
            $('#article-content').summernote({
                height: 400,
                toolbar: [
                    ['style', ['style']],
                    ['font', ['bold', 'italic', 'underline', 'strikethrough', 'superscript', 'subscript', 'clear']],
                    ['para', ['ul', 'ol', 'paragraph']],
                    ['insert', ['link', 'picture', 'table']],
                    ['view', ['fullscreen', 'codeview']]
                ]
            });
        }
        
        // Add mode toggle button
        const headers = document.querySelectorAll('.article-header, h1');
        if (headers.length > 0) {
            const header = headers[0];
            const toggleContainer = document.createElement('div');
            toggleContainer.className = 'mode-toggle';
            toggleContainer.innerHTML = `
                <button class="mode-toggle-button" data-mode="wiki">Wiki Mode</button>
                <button class="mode-toggle-button active" data-mode="html">HTML Mode</button>
            `;
            
            // Insert after the header
            header.parentNode.insertBefore(toggleContainer, header.nextSibling);
            
            // Add toggle behavior
            const buttons = toggleContainer.querySelectorAll('.mode-toggle-button');
            buttons.forEach(button => {
                button.addEventListener('click', function() {
                    const mode = this.getAttribute('data-mode');
                    
                    // Don't do anything if already active
                    if (this.classList.contains('active')) return;
                    
                    // Update URL with the new mode
                    const url = new URL(window.location.href);
                    url.searchParams.set('mode', mode);
                    
                    // Navigate to new URL
                    window.location.href = url.toString();
                });
            });
        }
    }
});

// Add a notice at the bottom of the page about wiki/HTML modes
document.addEventListener('DOMContentLoaded', function() {
    const mainContent = document.querySelector('.main-content');
    if (!mainContent) return;
    
    const footer = document.querySelector('footer');
    if (!footer) return;
    
    const urlParams = new URLSearchParams(window.location.search);
    const currentMode = urlParams.get('mode') || 'wiki';
    
    const notice = document.createElement('div');
    notice.className = 'mode-notice';
    notice.innerHTML = `
        <p>
            You are currently viewing this site in <strong>${currentMode.toUpperCase()} mode</strong>. 
            <a href="?mode=${currentMode === 'wiki' ? 'html' : 'wiki'}">Switch to ${currentMode === 'wiki' ? 'HTML' : 'Wiki'} mode</a>
        </p>
    `;
    
    // Insert before the footer
    document.body.insertBefore(notice, footer);
    
    // Add some styles
    const style = document.createElement('style');
    style.textContent = `
        .mode-notice {
            text-align: center;
            padding: 10px;
            background-color: #f8f9fa;
            border-top: 1px solid #e0e0e0;
            font-size: 14px;
            color: #666;
        }
        
        .mode-notice a {
            color: #0645ad;
            text-decoration: none;
        }
        
        .mode-notice a:hover {
            text-decoration: underline;
        }
    `;
    
    document.head.appendChild(style);
});
