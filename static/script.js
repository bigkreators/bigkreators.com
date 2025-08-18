// File: static/script.js

/**
 * Main JavaScript for Kryptopedia site functionality
 * Handles authentication, modals, search, and general site interactions
 * 
 * NOTE: This file should NOT handle article creation - that's handled by
 * templates/create_article.html for Summernote forms
 */

// Global state
let isLoggedIn = false;
let currentUser = null;

// Initialize the app when DOM loads
document.addEventListener('DOMContentLoaded', function() {
    console.log('Kryptopedia script.js loaded');
    
    // Check authentication status
    checkAuthStatus();
    
    // Set up all event listeners
    setupLoginForm();
    setupRegisterForm();
    setupModalClosers();
    setupSearch();
    setupUserMenu();
    setupLogout();
    
    // Update UI based on auth status
    updateUIBasedOnAuth();
});

// Check if user is authenticated
function checkAuthStatus() {
    const token = localStorage.getItem('token');
    if (token) {
        // Verify token with server
        fetch('/api/auth/me', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        })
        .then(response => {
            if (response.ok) {
                return response.json();
            } else {
                // Token is invalid
                localStorage.removeItem('token');
                throw new Error('Invalid token');
            }
        })
        .then(userData => {
            isLoggedIn = true;
            currentUser = userData;
            updateUIBasedOnAuth();
        })
        .catch(error => {
            console.log('Token verification failed:', error);
            isLoggedIn = false;
            currentUser = null;
            updateUIBasedOnAuth();
        });
    } else {
        isLoggedIn = false;
        currentUser = null;
        updateUIBasedOnAuth();
    }
}

// Update UI elements based on authentication status
function updateUIBasedOnAuth() {
    const loginBtn = document.getElementById('login-btn');
    const registerBtn = document.getElementById('register-btn');
    const userMenu = document.getElementById('user-menu');
    const usernameSpan = document.getElementById('username');
    const adminLinks = document.querySelectorAll('.admin-only');
    
    if (isLoggedIn && currentUser) {
        // User is logged in
        if (loginBtn) loginBtn.style.display = 'none';
        if (registerBtn) registerBtn.style.display = 'none';
        
        if (userMenu) {
            userMenu.style.display = 'block';
            if (usernameSpan) usernameSpan.textContent = currentUser.username;
        }
        
        // Show admin links for admins/editors
        if (currentUser.role === 'admin' || currentUser.role === 'editor') {
            adminLinks.forEach(link => link.style.display = 'block');
        }
    } else {
        // User is not logged in
        if (loginBtn) loginBtn.style.display = 'inline-block';
        if (registerBtn) registerBtn.style.display = 'inline-block';
        if (userMenu) userMenu.style.display = 'none';
        
        // Hide admin links
        adminLinks.forEach(link => link.style.display = 'none');
    }
}

// Set up login form
function setupLoginForm() {
    const loginForm = document.getElementById('login-form');
    const loginBtn = document.getElementById('login-btn');
    
    // Open login modal
    if (loginBtn) {
        loginBtn.addEventListener('click', function() {
            const loginModal = document.getElementById('login-modal');
            if (loginModal) loginModal.style.display = 'block';
        });
    }
    
    // Handle login form submission
    if (loginForm) {
        loginForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            
            // Show loading state
            const loginButton = loginForm.querySelector('button[type="submit"]');
            const originalButtonText = loginButton.textContent;
            loginButton.disabled = true;
            loginButton.textContent = 'Logging in...';
            
            // Create form data for OAuth2 format
            const formData = new URLSearchParams();
            formData.append('username', email); // API expects 'username' field
            formData.append('password', password);
            
            fetch('/api/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                body: formData
            })
            .then(response => {
                if (!response.ok) {
                    return response.json().then(data => {
                        throw new Error(data.detail || 'Login failed');
                    });
                }
                return response.json();
            })
            .then(data => {
                console.log('Login successful:', data);
                
                // Store token
                localStorage.setItem('token', data.access_token);
                
                // Close login modal
                const loginModal = document.getElementById('login-modal');
                if (loginModal) loginModal.style.display = 'none';
                
                // Clear form
                loginForm.reset();
                
                // Update auth status
                checkAuthStatus();
                
                // Check if there's a redirect URL
                const redirectUrl = sessionStorage.getItem('redirectAfterLogin');
                if (redirectUrl) {
                    sessionStorage.removeItem('redirectAfterLogin');
                    window.location.href = redirectUrl;
                } else {
                    // Reload page to update UI
                    window.location.reload();
                }
            })
            .catch(error => {
                console.error('Login error:', error);
                alert(error.message || 'Login failed. Please check your credentials and try again.');
            })
            .finally(() => {
                // Reset button state
                loginButton.disabled = false;
                loginButton.textContent = originalButtonText;
            });
        });
    }
}

// Set up register form
function setupRegisterForm() {
    const registerForm = document.getElementById('register-form');
    const registerBtn = document.getElementById('register-btn');
    
    // Open register modal
    if (registerBtn) {
        registerBtn.addEventListener('click', function() {
            const registerModal = document.getElementById('register-modal');
            if (registerModal) registerModal.style.display = 'block';
        });
    }
    
    // Handle register form submission
    if (registerForm) {
        registerForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const username = document.getElementById('reg-username').value;
            const email = document.getElementById('reg-email').value;
            const password = document.getElementById('reg-password').value;
            const confirmPassword = document.getElementById('reg-confirm-password').value;
            
            // Validate passwords match
            if (password !== confirmPassword) {
                alert('Passwords do not match!');
                return;
            }
            
            // Show loading state
            const registerButton = registerForm.querySelector('button[type="submit"]');
            const originalButtonText = registerButton.textContent;
            registerButton.disabled = true;
            registerButton.textContent = 'Registering...';
            
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
                    return response.json().then(data => {
                        throw new Error(data.detail || 'Registration failed');
                    });
                }
                return response.json();
            })
            .then(data => {
                console.log('Registration successful:', data);
                
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
                alert(error.message || 'Registration failed. Please try again with a different username or email.');
            })
            .finally(() => {
                // Reset button state
                registerButton.disabled = false;
                registerButton.textContent = originalButtonText;
            });
        });
    }
}

// Set up modal functionality
function setupModalClosers() {
    // Close buttons for modals
    const closeButtons = document.querySelectorAll('.close');
    closeButtons.forEach(button => {
        button.addEventListener('click', function() {
            const modal = this.closest('.modal');
            if (modal) modal.style.display = 'none';
        });
    });
    
    // Close modal when clicking outside
    window.addEventListener('click', function(event) {
        if (event.target.classList.contains('modal')) {
            const modals = document.querySelectorAll('.modal');
            modals.forEach(modal => {
                modal.style.display = 'none';
            });
        }
    });
    
    // Register link in login modal
    const registerLink = document.getElementById('register-link');
    if (registerLink) {
        registerLink.addEventListener('click', function(e) {
            e.preventDefault();
            const loginModal = document.getElementById('login-modal');
            const registerModal = document.getElementById('register-modal');
            if (loginModal) loginModal.style.display = 'none';
            if (registerModal) registerModal.style.display = 'block';
            
            // Transfer any redirect URL from login to registration process
            const redirectUrl = sessionStorage.getItem('redirectAfterLogin');
            if (redirectUrl) {
                // Keep the redirectAfterLogin in session storage for the registration process
            }
        });
    }
    
    // Login to create button
    const loginToCreateButton = document.getElementById('login-to-create');
    if (loginToCreateButton) {
        loginToCreateButton.addEventListener('click', function() {
            const loginModal = document.getElementById('login-modal');
            if (loginModal) loginModal.style.display = 'block';
        });
    }
}

// Set up search functionality
function setupSearch() {
    const searchInput = document.getElementById('search-input');
    const searchButton = document.getElementById('search-button');
    const searchForm = document.getElementById('search-form');
    
    // Handle search form submission
    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            e.preventDefault();
            performSearch();
        });
    }
    
    // Handle search button click
    if (searchButton) {
        searchButton.addEventListener('click', function() {
            performSearch();
        });
    }
    
    // Handle enter key in search input
    if (searchInput) {
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                performSearch();
            }
        });
    }
    
    function performSearch() {
        const query = searchInput ? searchInput.value.trim() : '';
        if (query) {
            window.location.href = `/search?q=${encodeURIComponent(query)}`;
        }
    }
}

// Set up user menu functionality
function setupUserMenu() {
    const userMenuToggle = document.getElementById('user-menu-toggle');
    const userMenuDropdown = document.getElementById('user-menu-dropdown');
    
    if (userMenuToggle && userMenuDropdown) {
        userMenuToggle.addEventListener('click', function(e) {
            e.preventDefault();
            userMenuDropdown.style.display = 
                userMenuDropdown.style.display === 'block' ? 'none' : 'block';
        });
        
        // Close dropdown when clicking outside
        document.addEventListener('click', function(e) {
            if (!userMenuToggle.contains(e.target) && !userMenuDropdown.contains(e.target)) {
                userMenuDropdown.style.display = 'none';
            }
        });
    }
}

// Set up logout functionality
function setupLogout() {
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', function(e) {
            e.preventDefault();
            logout();
        });
    }
}

// Logout function
function logout() {
    // Remove token from storage
    localStorage.removeItem('token');
    
    // Update state
    isLoggedIn = false;
    currentUser = null;
    
    // Update UI
    updateUIBasedOnAuth();
    
    // Show success message
    alert('You have been logged out successfully.');
    
    // Redirect to home page if on a protected page
    if (window.location.pathname.includes('/admin') || 
        window.location.pathname.includes('/create-') ||
        window.location.pathname.includes('/edit-')) {
        window.location.href = '/';
    } else {
        // Just reload the current page
        window.location.reload();
    }
}

// Utility function to check if user has permission
function hasPermission(requiredRole) {
    if (!isLoggedIn || !currentUser) return false;
    
    const roles = ['user', 'editor', 'admin'];
    const userRoleIndex = roles.indexOf(currentUser.role);
    const requiredRoleIndex = roles.indexOf(requiredRole);
    
    return userRoleIndex >= requiredRoleIndex;
}

// Utility function to redirect to login with return URL
function redirectToLogin(returnUrl) {
    sessionStorage.setItem('redirectAfterLogin', returnUrl || window.location.href);
    const loginModal = document.getElementById('login-modal');
    if (loginModal) {
        loginModal.style.display = 'block';
    } else {
        // Fallback - redirect to a login page if modal doesn't exist
        window.location.href = '/login';
    }
}

// Utility function to show notification
function showNotification(message, type = 'info') {
    // You can implement a notification system here
    // For now, just use alert
    alert(message);
}

// Export some functions for use by other scripts
window.Kryptopedia = window.Kryptopedia || {};
window.Kryptopedia.auth = {
    isLoggedIn: () => isLoggedIn,
    getCurrentUser: () => currentUser,
    hasPermission: hasPermission,
    redirectToLogin: redirectToLogin,
    logout: logout
};

window.Kryptopedia.ui = {
    showNotification: showNotification
};
