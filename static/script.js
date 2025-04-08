// Main script for Cryptopedia frontend

document.addEventListener('DOMContentLoaded', function() {
    // Initialize modals
    initializeModals();
    
    // Handle authentication
    initializeAuth();
    
    // Handle search
    initializeSearch();
    
    // Handle random article
    initializeRandomArticle();
    
    // Initialize article-specific functionality if on article page
    if (document.querySelector('.article-content')) {
        initializeArticleFunctions();
    }
    
    // Initialize article creation if on create article page
    if (document.getElementById('create-article-form')) {
        initializeArticleCreation();
    }
});

// Modal functionality
function initializeModals() {
    // Get modals
    const loginModal = document.getElementById('login-modal');
    const registerModal = document.getElementById('register-modal');
    const rewardModal = document.getElementById('reward-modal');
    
    // Get buttons and links that open modals
    const loginLink = document.getElementById('login-link');
    const registerLink = document.getElementById('register-link');
    const rewardButton = document.getElementById('reward-button');
    
    // Get close buttons
    const closeButtons = document.getElementsByClassName('close');
    
    // Open login modal when login link is clicked
    if (loginLink) {
        loginLink.addEventListener('click', function(e) {
            e.preventDefault();
            if (loginModal) loginModal.style.display = 'block';
        });
    }
    
    // Open register modal when register link is clicked
    if (registerLink) {
        registerLink.addEventListener('click', function(e) {
            e.preventDefault();
            if (loginModal) loginModal.style.display = 'none';
            if (registerModal) registerModal.style.display = 'block';
        });
    }
    
    // Open reward modal when reward button is clicked
    if (rewardButton) {
        rewardButton.addEventListener('click', function() {
            if (rewardModal) rewardModal.style.display = 'block';
        });
    }
    
    // Close modals when close button is clicked
    for (let i = 0; i < closeButtons.length; i++) {
        closeButtons[i].addEventListener('click', function() {
            const modal = this.parentElement.parentElement;
            modal.style.display = 'none';
        });
    }
    
    // Close modals when clicking outside of modal content
    window.addEventListener('click', function(event) {
        if (loginModal && event.target === loginModal) {
            loginModal.style.display = 'none';
        }
        if (registerModal && event.target === registerModal) {
            registerModal.style.display = 'none';
        }
        if (rewardModal && event.target === rewardModal) {
            rewardModal.style.display = 'none';
        }
    });
}

// Authentication functionality
function initializeAuth() {
    // Check if user is logged in
    const token = localStorage.getItem('token');
    const loginLink = document.getElementById('login-link');
    
    if (token && loginLink) {
        // User is logged in, change login link to logout
        loginLink.textContent = 'Logout';
        loginLink.href = '#';
        loginLink.removeEventListener('click', showLoginModal);
        loginLink.addEventListener('click', logout);
        
        // Show restricted elements
        showAuthenticatedElements();
    }
    
    // Handle login form submission
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', function(e) {
            e.preventDefault();
            login();
        });
    }
    
    // Handle register form submission
    const registerForm = document.getElementById('register-form');
    if (registerForm) {
        registerForm.addEventListener('submit', function(e) {
            e.preventDefault();
            register();
        });
    }
}

function showLoginModal() {
    const loginModal = document.getElementById('login-modal');
    if (loginModal) loginModal.style.display = 'block';
}

function login() {
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    
    // Create form data for token endpoint
    const formData = new FormData();
    formData.append('username', email);  // API expects 'username' field but we use email
    formData.append('password', password);
    
    fetch('/api/auth/login', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Login failed');
        }
        return response.json();
    })
    .then(data => {
        // Store token
        localStorage.setItem('token', data.access_token);
        
        // Close modal
        const loginModal = document.getElementById('login-modal');
        if (loginModal) loginModal.style.display = 'none';
        
        // Refresh page or update UI
        window.location.reload();
    })
    .catch(error => {
        console.error('Error logging in:', error);
        alert('Login failed. Please check your credentials and try again.');
    });
}

function register() {
    const username = document.getElementById('reg-username').value;
    const email = document.getElementById('reg-email').value;
    const password = document.getElementById('reg-password').value;
    const confirmPassword = document.getElementById('reg-confirm-password').value;
    
    // Validate passwords match
    if (password !== confirmPassword) {
        alert('Passwords do not match!');
        return;
    }
    
    // Create registration data
    const userData = {
        username: username,
        email: email,
        password: password
    };
    
    fetch('/api/auth/register', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(userData)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Registration failed');
        }
        return response.json();
    })
    .then(data => {
        // Close register modal
        const registerModal = document.getElementById('register-modal');
        if (registerModal) registerModal.style.display = 'none';
        
        // Show success message and open login modal
        alert('Registration successful! Please log in.');
        const loginModal = document.getElementById('login-modal');
        if (loginModal) loginModal.style.display = 'block';
    })
    .catch(error => {
        console.error('Error registering:', error);
        alert('Registration failed. Please try again with a different username or email.');
    });
}

function logout() {
    // Remove token
    localStorage.removeItem('token');
    
    // Refresh page
    window.location.reload();
}

function showAuthenticatedElements() {
    // Show elements that should only be visible to logged-in users
    const authElements = document.querySelectorAll('.auth-required');
    authElements.forEach(element => {
        element.classList.remove('hidden');
    });
    
    // Hide elements that should only be visible to non-logged-in users
    const nonAuthElements = document.querySelectorAll('.non-auth-only');
    nonAuthElements.forEach(element => {
        element.classList.add('hidden');
    });
}

// Search functionality
function initializeSearch() {
    const searchButton = document.getElementById('search-button');
    const searchInput = document.getElementById('search-input');
    
    if (searchButton && searchInput) {
        searchButton.addEventListener('click', function() {
            performSearch();
        });
        
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                performSearch();
            }
        });
    }
}

function performSearch() {
    const searchQuery = document.getElementById('search-input').value.trim();
    
    if (searchQuery !== '') {
        window.location.href = '/search?q=' + encodeURIComponent(searchQuery);
    }
}

// Random article
function initializeRandomArticle() {
    const randomLink = document.getElementById('random-article');
    
    if (randomLink) {
        randomLink.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Redirect to API endpoint, which will redirect to a random article
            window.location.href = '/api/articles/random';
        });
    }
}

// Article-specific functionality
function initializeArticleFunctions() {
    // Reward functionality
    const rewardForm = document.getElementById('reward-form');
    
    if (rewardForm) {
        rewardForm.addEventListener('submit', function(e) {
            e.preventDefault();
            submitReward();
        });
    }
}

function submitReward() {
    // Check if user is authenticated
    const token = localStorage.getItem('token');
    if (!token) {
        alert('Please log in to reward contributors.');
        const loginModal = document.getElementById('login-modal');
        if (loginModal) loginModal.style.display = 'block';
        return;
    }
    
    // Get reward data
    const articleId = document.getElementById('article-id').value;
    const rewardType = document.getElementById('reward-type').value;
    const points = document.getElementById('points').value;
    
    // Create reward data
    const rewardData = {
        rewardType: rewardType,
        points: parseInt(points, 10)
    };
    
    // Submit reward
    fetch(`/api/articles/${articleId}/rewards`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(rewardData)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Failed to submit reward');
        }
        return response.json();
    })
    .then(data => {
        // Close modal
        const rewardModal = document.getElementById('reward-modal');
        if (rewardModal) rewardModal.style.display = 'none';
        
        // Show success message
        alert('Reward submitted successfully!');
    })
    .catch(error => {
        console.error('Error submitting reward:', error);
        alert('Failed to submit reward. Please try again.');
    });
}
