// File: static/script.js (Updated)
// Authentication functionality
document.addEventListener('DOMContentLoaded', function() {
    initializeAuth();
    setupLoginForm();
    setupRegisterForm();
    setupModalClosers();
    setupSearch();
});

// Initialize authentication state
function initializeAuth() {
    // Check if user is logged in
    const token = localStorage.getItem('token');
    const loginLink = document.getElementById('login-link');
    const profileLinkContainer = document.getElementById('profile-link-container');
    
    if (token && loginLink) {
        // User is logged in, change login link to logout
        loginLink.textContent = 'Logout';
        loginLink.href = '#';
        loginLink.removeEventListener('click', showLoginModal);
        loginLink.addEventListener('click', logout);
        
        // Show profile link
        if (profileLinkContainer) {
            profileLinkContainer.style.display = 'inline-block';
        }
        
        // Show restricted elements
        showAuthenticatedElements();
        
        // Fetch user data to check role
        fetchCurrentUser()
            .then(userData => {
                if (userData) {
                    // Show admin elements if user is admin
                    if (userData.role === 'admin' || userData.role === 'editor') {
                        showAdminElements();
                    }
                }
            })
            .catch(error => {
                console.error('Error fetching user data:', error);
            });
    } else if (loginLink) {
        // User is not logged in, ensure login modal shows on click
        loginLink.addEventListener('click', showLoginModal);
        
        // Hide profile link
        if (profileLinkContainer) {
            profileLinkContainer.style.display = 'none';
        }
    }
}

// Set up the login form submission
function setupLoginForm() {
    const loginForm = document.getElementById('login-form');
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
            formData.append('username', email); // API expects username field
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
                    throw new Error('Login failed');
                }
                return response.json();
            })
            .then(data => {
                console.log('Login successful');
                
                // Store token
                localStorage.setItem('token', data.access_token);
                
                // Close modal
                const loginModal = document.getElementById('login-modal');
                if (loginModal) loginModal.style.display = 'none';
                
                // Show success message
                alert('Login successful! Welcome back.');
                
                // Refresh page to update UI
                window.location.reload();
            })
            .catch(error => {
                console.error('Error logging in:', error);
                alert('Login failed. Please check your credentials and try again.');
            })
            .finally(() => {
                // Reset button state
                loginButton.disabled = false;
                loginButton.textContent = originalButtonText;
            });
        });
    }
}

// Set up the register form submission
function setupRegisterForm() {
    const registerForm = document.getElementById('register-form');
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

// Set up modal closers
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
    
    if (searchInput && searchButton) {
        // Search when Enter key is pressed
        searchInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                performSearch();
            }
        });
        
        // Search when button is clicked
        searchButton.addEventListener('click', performSearch);
    }
    
    function performSearch() {
        const query = searchInput.value.trim();
        if (query) {
            window.location.href = `/search?q=${encodeURIComponent(query)}`;
        }
    }
}

// Show login modal
function showLoginModal() {
    const loginModal = document.getElementById('login-modal');
    if (loginModal) {
        loginModal.style.display = 'block';
    }
}

// Logout functionality
function logout() {
    // Remove token
    localStorage.removeItem('token');
    
    // Show success message
    alert('You have been logged out successfully.');
    
    // Refresh page
    window.location.reload();
}

// Show elements that require authentication
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

// Show elements that require admin or editor privileges
function showAdminElements() {
    const adminElements = document.querySelectorAll('.admin-required');
    adminElements.forEach(element => {
        element.style.display = 'inline-block';
    });
}

// Fetch current user data
async function fetchCurrentUser() {
    const token = localStorage.getItem('token');
    if (!token) return null;
    
    try {
        const response = await fetch('/api/auth/me', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) {
            if (response.status === 401) {
                // Token expired or invalid, log out
                localStorage.removeItem('token');
                return null;
            }
            throw new Error('Failed to fetch user data');
        }
        
        return await response.json();
    } catch (error) {
        console.error('Error fetching user data:', error);
        return null;
    }
}
