// File: static/profile.js
// Profile page functionality for Kryptopedia
// This handles authentication, profile data loading and UI updates

document.addEventListener('DOMContentLoaded', function() {
    // Initialize profile functionality
    initializeProfile();
    setupProfileTabs();
    setupEditForms();
    handleAuthRequiredElements();
});

// Main profile initialization
function initializeProfile() {
    // Check if we're on a profile page
    if (window.location.pathname.startsWith('/profile') || 
        window.location.pathname.startsWith('/users/')) {
        
        // Get token from localStorage
        const token = localStorage.getItem('token');
        
        // Handle not logged in state
        if (!token) {
            // Show login required message if it exists
            const profileContent = document.getElementById('profile-content');
            const loginRequired = document.getElementById('login-required');
            
            if (profileContent && loginRequired) {
                profileContent.style.display = 'none';
                loginRequired.style.display = 'block';
            }
            
            // Set up login button if it exists
            const loginButton = document.getElementById('login-to-view-profile');
            if (loginButton) {
                loginButton.addEventListener('click', function() {
                    const loginModal = document.getElementById('login-modal');
                    if (loginModal) {
                        loginModal.style.display = 'block';
                        
                        // Set up redirect after login
                        const loginForm = document.getElementById('login-form');
                        if (loginForm) {
                            loginForm.addEventListener('submit', function(e) {
                                e.preventDefault();
                                
                                // Get email and password
                                const email = document.getElementById('email').value;
                                const password = document.getElementById('password').value;
                                
                                // Create form data for OAuth2 format
                                const formData = new URLSearchParams();
                                formData.append('username', email); // API expects username field
                                formData.append('password', password);
                                
                                // Show loading state
                                const loginButton = loginForm.querySelector('button[type="submit"]');
                                const originalButtonText = loginButton.textContent;
                                loginButton.disabled = true;
                                loginButton.textContent = 'Logging in...';
                                
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
                                    // Store token
                                    localStorage.setItem('token', data.access_token);
                                    
                                    // Close modal
                                    loginModal.style.display = 'none';
                                    
                                    // Reload page to show profile
                                    window.location.reload();
                                })
                                .catch(error => {
                                    console.error('Error logging in:', error);
                                    alert('Login failed. Please check your credentials and try again.');
                                    
                                    // Reset button state
                                    loginButton.disabled = false;
                                    loginButton.textContent = originalButtonText;
                                });
                            });
                        }
                    }
                });
            }
        } else {
            // User is logged in, ensure profile content is visible
            const profileContent = document.getElementById('profile-content');
            const loginRequired = document.getElementById('login-required');
            
            if (profileContent) {
                profileContent.style.display = 'block';
            }
            
            if (loginRequired) {
                loginRequired.style.display = 'none';
            }
            
            // Fetch user data from API to ensure token is valid
            fetch('/api/auth/me', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            })
            .then(response => {
                if (!response.ok) {
                    if (response.status === 401) {
                        // Token expired or invalid, clear it
                        localStorage.removeItem('token');
                        window.location.reload();
                        throw new Error('Unauthorized');
                    }
                    throw new Error('Failed to fetch user data');
                }
                return response.json();
            })
            .then(userData => {
                // Update profile UI with user data if needed
                updateProfileUI(userData);
            })
            .catch(error => {
                console.error('Error fetching user data:', error);
                // If not unauthorized, show error message
                if (error.message !== 'Unauthorized') {
                    showErrorMessage('Could not load profile data. Please try again later.');
                }
            });
        }
    }
}

// Handle tabs in profile page
function setupProfileTabs() {
    const tabLinks = document.querySelectorAll('.profile-tab-link');
    const tabContents = document.querySelectorAll('.profile-tab-content');
    
    if (tabLinks.length > 0 && tabContents.length > 0) {
        // Get active tab from URL if present
        const urlParams = new URLSearchParams(window.location.search);
        const activeTab = urlParams.get('tab');
        
        // Setup tab click handlers
        tabLinks.forEach(link => {
            link.addEventListener('click', function(e) {
                e.preventDefault();
                
                // Get tab ID from href
                const tabId = this.getAttribute('href').substring(1);
                
                // Update URL without reloading page
                history.pushState(null, '', `?tab=${tabId}`);
                
                // Activate this tab
                activateTab(tabId);
            });
            
            // Check if this tab should be active based on URL
            if (activeTab && link.getAttribute('href').substring(1) === activeTab) {
                link.click();
            }
        });
        
        // If no tab is active in URL, activate first tab
        if (!activeTab && tabLinks.length > 0) {
            tabLinks[0].click();
        }
    }
    
    // Function to activate a specific tab
    function activateTab(tabId) {
        // Hide all tab contents and deactivate tab links
        tabContents.forEach(content => {
            content.classList.remove('active');
        });
        
        tabLinks.forEach(link => {
            link.classList.remove('active');
        });
        
        // Show selected tab content and activate tab link
        const selectedTab = document.getElementById(tabId);
        const selectedLink = document.querySelector(`[href="#${tabId}"]`);
        
        if (selectedTab) {
            selectedTab.classList.add('active');
        }
        
        if (selectedLink) {
            selectedLink.classList.add('active');
        }
    }
}

// Handle edit forms for profile
function setupEditForms() {
    const editProfileForm = document.getElementById('edit-profile-form');
    
    if (editProfileForm) {
        editProfileForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Get form values
            const displayName = document.getElementById('display-name')?.value;
            const bio = document.getElementById('bio')?.value;
            const location = document.getElementById('location')?.value;
            const website = document.getElementById('website')?.value;
            const email = document.getElementById('email')?.value;
            const currentPassword = document.getElementById('current-password')?.value;
            const newPassword = document.getElementById('new-password')?.value;
            const confirmPassword = document.getElementById('confirm-password')?.value;
            
            // Validate form
            if (!email) {
                showErrorMessage('Email is required');
                return;
            }
            
            if (!currentPassword) {
                showErrorMessage('Current password is required to save changes');
                return;
            }
            
            if (newPassword && newPassword !== confirmPassword) {
                showErrorMessage('New passwords do not match');
                return;
            }
            
            // Get token
            const token = localStorage.getItem('token');
            if (!token) {
                showErrorMessage('You must be logged in to update your profile');
                return;
            }
            
            // Prepare data
            const userData = {
                displayName: displayName || null,
                bio: bio || null,
                location: location || null,
                website: website || null,
                email: email,
                currentPassword: currentPassword
            };
            
            if (newPassword) {
                userData.password = newPassword;
            }
            
            // Get email preferences if they exist
            const emailPreferences = {};
            const emailPrefElements = document.querySelectorAll('[name^="emailPreferences."]');
            if (emailPrefElements.length > 0) {
                emailPrefElements.forEach(element => {
                    const prefName = element.name.replace('emailPreferences.', '');
                    emailPreferences[prefName] = element.checked;
                });
                userData.emailPreferences = emailPreferences;
            }
            
            // Show loading state
            const submitButton = editProfileForm.querySelector('button[type="submit"]');
            const originalText = submitButton.textContent;
            submitButton.disabled = true;
            submitButton.textContent = 'Saving...';
            
            // Send API request
            fetch('/api/auth/profile', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(userData)
            })
            .then(response => {
                if (!response.ok) {
                    if (response.status === 401) {
                        localStorage.removeItem('token');
                        throw new Error('Your session has expired. Please log in again.');
                    }
                    return response.json().then(data => {
                        throw new Error(data.detail || 'Failed to update profile');
                    });
                }
                return response.json();
            })
            .then(data => {
                showSuccessMessage('Profile updated successfully!');
                
                // Clear password fields
                if (document.getElementById('current-password')) {
                    document.getElementById('current-password').value = '';
                }
                
                if (document.getElementById('new-password')) {
                    document.getElementById('new-password').value = '';
                }
                
                if (document.getElementById('confirm-password')) {
                    document.getElementById('confirm-password').value = '';
                }
                
                // Update UI if needed
                updateProfileUI(data);
                
                // Redirect to profile page after a delay if we're on edit page
                if (window.location.pathname.includes('/edit')) {
                    setTimeout(() => {
                        window.location.href = '/profile';
                    }, 2000);
                }
            })
            .catch(error => {
                console.error('Error updating profile:', error);
                showErrorMessage(error.message || 'Failed to update profile. Please try again.');
            })
            .finally(() => {
                // Reset button state
                submitButton.disabled = false;
                submitButton.textContent = originalText;
            });
        });
    }
}

// Function to update profile UI with user data
function updateProfileUI(userData) {
    // Update avatar if it exists
    const avatarElements = document.querySelectorAll('.user-avatar');
    avatarElements.forEach(avatar => {
        if (userData.username) {
            avatar.textContent = userData.username[0].toUpperCase();
        }
    });
    
    // Update username elements
    const usernameElements = document.querySelectorAll('.user-username');
    usernameElements.forEach(element => {
        element.textContent = userData.username || '';
    });
    
    // Update other user data in the UI
    const displayNameElements = document.querySelectorAll('.user-display-name');
    displayNameElements.forEach(element => {
        element.textContent = userData.displayName || userData.username || '';
    });
    
    const userRoleElements = document.querySelectorAll('.user-role');
    userRoleElements.forEach(element => {
        element.textContent = userData.role ? userData.role.charAt(0).toUpperCase() + userData.role.slice(1) : '';
    });
    
    const userBioElements = document.querySelectorAll('.user-bio');
    userBioElements.forEach(element => {
        element.textContent = userData.bio || 'No bio provided';
    });
    
    // Update stat counters if they exist
    if (userData.contributions) {
        const articleCountElements = document.querySelectorAll('.articles-count');
        articleCountElements.forEach(element => {
            element.textContent = userData.contributions.articlesCreated || '0';
        });
        
        const editsCountElements = document.querySelectorAll('.edits-count');
        editsCountElements.forEach(element => {
            element.textContent = userData.contributions.editsPerformed || '0';
        });
        
        const rewardsCountElements = document.querySelectorAll('.rewards-count');
        rewardsCountElements.forEach(element => {
            element.textContent = userData.contributions.rewardsReceived || '0';
        });
    }
}

// Show error message
function showErrorMessage(message) {
    const errorMessage = document.getElementById('error-message');
    const successMessage = document.getElementById('success-message');
    
    if (errorMessage) {
        errorMessage.textContent = message;
        errorMessage.style.display = 'block';
        
        if (successMessage) {
            successMessage.style.display = 'none';
        }
        
        // Scroll to error
        errorMessage.scrollIntoView({ behavior: 'smooth', block: 'start' });
        
        // Hide after 5 seconds
        setTimeout(() => {
            errorMessage.style.display = 'none';
        }, 5000);
    } else {
        // Fallback to alert if error element doesn't exist
        alert(message);
    }
}

// Show success message
function showSuccessMessage(message) {
    const successMessage = document.getElementById('success-message');
    const errorMessage = document.getElementById('error-message');
    
    if (successMessage) {
        successMessage.textContent = message;
        successMessage.style.display = 'block';
        
        if (errorMessage) {
            errorMessage.style.display = 'none';
        }
        
        // Hide after 5 seconds
        setTimeout(() => {
            successMessage.style.display = 'none';
        }, 5000);
    } else {
        // Fallback to alert if success element doesn't exist
        alert(message);
    }
}

// Handle authentication-required elements
function handleAuthRequiredElements() {
    const token = localStorage.getItem('token');
    const authElements = document.querySelectorAll('.auth-required');
    
    if (token) {
        // User is logged in, show auth-required elements
        authElements.forEach(element => {
            element.classList.remove('hidden');
            element.style.display = '';
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
            // Show admin-required elements for admins/editors
            if (user.role === 'admin' || user.role === 'editor') {
                const adminElements = document.querySelectorAll('.admin-required');
                adminElements.forEach(element => {
                    element.classList.remove('hidden');
                    element.style.display = '';
                });
            }
        })
        .catch(error => {
            console.error('Error checking user role:', error);
        });
    } else {
        // User is not logged in, hide auth-required elements
        authElements.forEach(element => {
            element.classList.add('hidden');
            
            // Don't override other display styles if hidden class exists
            if (!element.classList.contains('hidden')) {
                element.style.display = 'none';
            }
        });
        
        // Add login redirect for auth-required links
        authElements.forEach(element => {
            if (element.tagName === 'A') {
                element.addEventListener('click', function(e) {
                    e.preventDefault();
                    // Open login modal
                    const loginModal = document.getElementById('login-modal');
                    if (loginModal) loginModal.style.display = 'block';
                });
            }
        });
    }
}
