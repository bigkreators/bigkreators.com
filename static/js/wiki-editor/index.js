// File: static/js/wiki-editor/index.js
// Fixed form submission handler

// Set up the form submission handler to transform the content
form.addEventListener('submit', function(e) {
    // CRITICAL: Prevent default form submission
    e.preventDefault();
    
    // Transform the article content by adding the short description
    transformContent(form);
    
    // Now handle the actual submission via API
    handleFormSubmission(form);
});

/**
 * Handle the actual form submission after content transformation
 * @param {HTMLElement} form - The form element
 */
function handleFormSubmission(form) {
    // Get the token
    const token = localStorage.getItem('token');
    if (!token) {
        alert('You must be logged in to create articles.');
        return;
    }
    
    // Get form values
    const articleTitle = form.querySelector('#article-title')?.value;
    const articleSummary = form.querySelector('#article-summary')?.value;
    const articleContent = form.querySelector('#article-content')?.value;
    const categoriesInput = form.querySelector('#article-categories')?.value || '';
    const tagsInput = form.querySelector('#article-tags')?.value || '';
    const editComment = form.querySelector('#edit-comment')?.value;
    
    // Process categories and tags
    const categories = categoriesInput.split(',')
        .map(item => item.trim())
        .filter(item => item.length > 0);
        
    const tags = tagsInput.split(',')
        .map(item => item.trim())
        .filter(item => item.length > 0);
    
    // Validate required fields
    if (!articleTitle || !articleSummary || !articleContent) {
        alert('Please fill in all required fields.');
        return;
    }
    
    if (!editComment) {
        alert('Please provide a summary of your changes.');
        return;
    }
    
    // Show loading state
    const submitButton = form.querySelector('[type="submit"]');
    const originalText = submitButton.textContent;
    submitButton.textContent = 'Creating Article...';
    submitButton.disabled = true;
    
    // Prepare the data
    const articleData = {
        title: articleTitle,
        summary: articleSummary,
        content: articleContent,
        categories: categories,
        tags: tags,
        editComment: editComment
    };
    
    // Submit via API
    fetch('/api/articles', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(articleData)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        // Success! Clear autosave and redirect
        const formId = form.id || 'wiki-editor-form';
        const autosaveKey = `wiki-autosave-${formId}`;
        localStorage.removeItem(autosaveKey);
        
        // Show success message
        alert('Article created successfully!');
        
        // Redirect to the new article
        if (data.slug) {
            window.location.href = `/articles/${data.slug}`;
        } else {
            window.location.href = '/articles';
        }
    })
    .catch(error => {
        console.error('Error creating article:', error);
        alert('Failed to create article. Please try again.');
        
        // Reset button state
        submitButton.textContent = originalText;
        submitButton.disabled = false;
    });
}
