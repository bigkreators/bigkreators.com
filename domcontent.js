// Add to the DOMContentLoaded function in templates/article.html

// Check if user is logged in
const token = localStorage.getItem('token');
const authElements = document.querySelectorAll('.auth-required');
const adminElements = document.querySelectorAll('.admin-required');

if (token) {
    // User is logged in, show auth-required elements
    authElements.forEach(element => {
        element.style.display = 'inline-block';
    });
    
    // Check if user is admin/editor for admin-required elements
    fetch('/api/auth/me', {
        headers: {
            'Authorization': `Bearer ${token}`
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Failed to get user info');
        }
        return response.json();
    })
    .then(user => {
        // Only show admin-required elements for admins/editors
        if (user.role === 'admin' || user.role === 'editor') {
            adminElements.forEach(element => {
                element.style.display = 'inline-block';
            });
        }
    })
    .catch(error => {
        console.error('Error checking user role:', error);
    });
} else {
    // User is not logged in, hide auth-required and admin-required elements
    authElements.forEach(element => {
        element.style.display = 'none';
    });
    
    adminElements.forEach(element => {
        element.style.display = 'none';
    });
}
