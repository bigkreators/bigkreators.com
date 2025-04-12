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
    // Get form inputs
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    
    // Show loading state
    const loginButton = document.querySelector('#login-form button[type="submit"]');
    const originalButtonText = loginButton.textContent;
    loginButton.disabled = true;
    loginButton.textContent = 'Logging in...';
    
    // Create form data in the format expected by OAuth2
    const formData = new URLSearchParams();
    formData.append('username', email);  // API expects 'username' field but we use email
    formData.append('password', password);
    
    // Make the login request
    fetch('/api/auth/login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: formData
    })
    .then(response => {
        // Check for unsuccessful response
        if (!response.ok) {
            console.error('Login failed with status:', response.status);
            return response.text().then(text => {
                console.error('Error response:', text);
                throw new Error('Login failed');
            });
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
    
    // Show loading state
    const registerButton = document.querySelector('#register-form button[type="submit"]');
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
            console.error('Registration failed with status:', response.status);
            return response.text().then(text => {
                console.error('Error response:', text);
                throw new Error('Registration failed');
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
        alert('Registration failed. Please try again with a different username or email.');
    })
    .finally(() => {
        // Reset button state
        registerButton.disabled = false;
        registerButton.textContent = originalButtonText;
    });
}

function logout() {
    // Remove token
    localStorage.removeItem('token');
    
    // Show success message
    alert('You have been logged out successfully.');
    
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
