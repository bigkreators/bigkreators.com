// Add this to the extra_js block in templates/article.html

// Article management functionality
const articleManagementModal = document.getElementById('article-management-modal');
const deleteConfirmationModal = document.getElementById('delete-confirmation-modal');
const manageButton = document.getElementById('manage-button');
const statusButtons = document.querySelectorAll('.status-button');
const deleteArticleButton = document.getElementById('delete-article');
const confirmDeleteButton = document.getElementById('confirm-delete');
const cancelDeleteButton = document.getElementById('cancel-delete');
const deleteConfirmationInput = document.getElementById('delete-confirmation');

// Show management modal when manage button is clicked
if (manageButton) {
    manageButton.addEventListener('click', function() {
        // Check if user is logged in and is admin/editor
        if (!token) {
            showLoginRequiredMessage();
            return;
        }
        
        // Show management modal
        if (articleManagementModal) {
            articleManagementModal.style.display = 'block';
        }
    });
}

// Handle status button clicks
if (statusButtons) {
    statusButtons.forEach(button => {
        button.addEventListener('click', function() {
            const newStatus = this.dataset.status;
            
            // Don't do anything if already active
            if (this.classList.contains('active')) {
                return;
            }
            
            // Confirm status change
            if (!confirm(`Are you sure you want to change the article status to "${newStatus}"?`)) {
                return;
            }
            
            // Show loading state
            this.disabled = true;
            const originalText = this.textContent;
            this.textContent = `Updating...`;
            
            // Update article status via API
            updateArticleStatus(newStatus)
                .then(success => {
                    if (success) {
                        // Update UI
                        statusButtons.forEach(btn => btn.classList.remove('active'));
                        this.classList.add('active');
                        
                        // Update status display
                        const statusDisplay = document.querySelector('.article-status');
                        if (statusDisplay) {
                            statusDisplay.textContent = newStatus;
                        }
                        
                        // Show success message
                        alert(`Article status updated to "${newStatus}"`);
                        
                        // Refresh page after a brief delay
                        setTimeout(() => {
                            window.location.reload();
                        }, 1000);
                    }
                })
                .finally(() => {
                    // Reset button state
                    this.disabled = false;
                    this.textContent = originalText;
                });
        });
    });
}

// Handle delete button click
if (deleteArticleButton) {
    deleteArticleButton.addEventListener('click', function() {
        // Close management modal
        if (articleManagementModal) {
            articleManagementModal.style.display = 'none';
        }
        
        // Show delete confirmation modal
        if (deleteConfirmationModal) {
            deleteConfirmationModal.style.display = 'block';
        }
    });
}

// Handle delete confirmation input
if (deleteConfirmationInput) {
    deleteConfirmationInput.addEventListener('input', function() {
        // Enable confirmation button only if correct text is entered
        if (this.value === 'DELETE') {
            confirmDeleteButton.disabled = false;
        } else {
            confirmDeleteButton.disabled = true;
        }
    });
}

// Handle confirm delete button
if (confirmDeleteButton) {
    confirmDeleteButton.addEventListener('click', function() {
        // Check if confirmation is valid
        if (deleteConfirmationInput.value !== 'DELETE') {
            return;
        }
        
        // Show loading state
        this.disabled = true;
        this.textContent = 'Deleting...';
        
        // Send delete request
        deleteArticle()
            .then(success => {
                if (success) {
                    // Show success message
                    alert('Article has been permanently deleted');
                    
                    // Redirect to homepage
                    window.location.href = '/';
                }
            })
            .catch(error => {
                // Reset button state
                this.disabled = false;
                this.textContent = 'Permanently Delete';
                
                // Show error message
                alert('Error deleting article: ' + error.message);
            });
    });
}

// Handle cancel delete button
if (cancelDeleteButton) {
    cancelDeleteButton.addEventListener('click', function() {
        // Close delete confirmation modal
        if (deleteConfirmationModal) {
            deleteConfirmationModal.style.display = 'none';
        }
        
        // Show management modal again
        if (articleManagementModal) {
            articleManagementModal.style.display = 'block';
        }
        
        // Reset confirmation input
        if (deleteConfirmationInput) {
            deleteConfirmationInput.value = '';
        }
        
        // Disable confirm button
        if (confirmDeleteButton) {
            confirmDeleteButton.disabled = true;
        }
    });
}

// Function to update article status
async function updateArticleStatus(newStatus) {
    try {
        const token = localStorage.getItem('token');
        if (!token) {
            throw new Error('You must be logged in to perform this action');
        }
        
        const response = await fetch(`/api/articles/{{ article._id }}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                status: newStatus
            })
        });
        
        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.detail || 'Failed to update article status');
        }
        
        return true;
    } catch (error) {
        console.error('Error updating article status:', error);
        alert('Error updating article status: ' + error.message);
        return false;
    }
}

// Function to delete article
async function deleteArticle() {
    try {
        const token = localStorage.getItem('token');
        if (!token) {
            throw new Error('You must be logged in to perform this action');
        }
        
        const response = await fetch(`/api/articles/{{ article._id }}?permanent=true`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.detail || 'Failed to delete article');
        }
        
        return true;
    } catch (error) {
        console.error('Error deleting article:', error);
        alert('Error deleting article: ' + error.message);
        throw error;
    }
}

// Function to show login required message
function showLoginRequiredMessage() {
    alert('You must be logged in as an administrator to manage articles');
    
    // Show login modal
    const loginModal = document.getElementById('login-modal');
    if (loginModal) {
        loginModal.style.display = 'block';
    }
}
