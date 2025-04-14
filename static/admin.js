// File: static/js/admin.js
// JavaScript for Kryptopedia admin dashboard functionality

document.addEventListener('DOMContentLoaded', function() {
    // Initialize admin dashboard
    initAdminDashboard();
    setupTabNavigation();
    setupDataTables();
    setupUserManagement();
    setupArticleManagement();
    setupProposalManagement();
    setupSystemTools();
});

// Initialize the admin dashboard
function initAdminDashboard() {
    // Check if we're on the admin dashboard page
    if (!document.querySelector('.admin-dashboard')) {
        return;
    }

    // Check if user is logged in and has admin privileges
    const token = localStorage.getItem('token');
    if (!token) {
        // Redirect to login page
        window.location.href = '/login?redirect=' + encodeURIComponent(window.location.pathname);
        return;
    }

    // Load dashboard statistics
    loadDashboardStats();
    
    // Set up refresh button
    const refreshButton = document.getElementById('refresh-stats');
    if (refreshButton) {
        refreshButton.addEventListener('click', function() {
            loadDashboardStats(true);
        });
    }
}

// Set up tab navigation on the admin dashboard
function setupTabNavigation() {
    const tabLinks = document.querySelectorAll('.admin-tab-link');
    const tabContents = document.querySelectorAll('.admin-tab-content');

    if (tabLinks.length === 0 || tabContents.length === 0) {
        return;
    }

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

        // Load tab-specific data if needed
        if (tabId === 'users-tab') {
            loadUsers();
        } else if (tabId === 'articles-tab') {
            loadArticles();
        } else if (tabId === 'proposals-tab') {
            loadProposals();
        }
    }
}

// Set up DataTables for admin tables
function setupDataTables() {
    // Check if DataTables is available
    if (typeof $.fn.DataTable === 'undefined') {
        console.warn('DataTables not available');
        return;
    }

    // Initialize DataTables for relevant tables if they exist
    const tables = [
        '#users-table',
        '#articles-table',
        '#proposals-table'
    ];

    tables.forEach(tableId => {
        const table = document.querySelector(tableId);
        if (table) {
            try {
                $(tableId).DataTable({
                    responsive: true,
                    pageLength: 10,
                    lengthMenu: [5, 10, 25, 50],
                    language: {
                        search: "Filter:",
                        lengthMenu: "Show _MENU_ entries",
                        info: "Showing _START_ to _END_ of _TOTAL_ entries"
                    }
                });
            } catch (e) {
                console.error(`Error initializing DataTable for ${tableId}:`, e);
            }
        }
    });
}

// Load dashboard statistics
function loadDashboardStats(forceRefresh = false) {
    const token = localStorage.getItem('token');
    if (!token) return;

    const statsContainer = document.getElementById('dashboard-stats');
    const activityContainer = document.getElementById('recent-activity');
    
    if (!statsContainer && !activityContainer) return;

    // Show loading indicators
    if (statsContainer) {
        statsContainer.innerHTML = '<div class="loading-spinner"></div>';
    }
    
    if (activityContainer) {
        activityContainer.innerHTML = '<div class="loading-spinner"></div>';
    }

    // Set cache-busting parameter if forcing refresh
    const cacheBuster = forceRefresh ? `?_=${Date.now()}` : '';
    
    // Fetch dashboard stats
    fetch(`/api/admin/dashboard${cacheBuster}`, {
        headers: {
            'Authorization': `Bearer ${token}`
        }
    })
    .then(response => {
        if (!response.ok) {
            if (response.status === 401 || response.status === 403) {
                // Unauthorized or forbidden, redirect to login
                window.location.href = '/login?redirect=' + encodeURIComponent(window.location.pathname);
                throw new Error('Unauthorized');
            }
            return response.json().then(data => {
                throw new Error(data.detail || 'Failed to load dashboard statistics');
            });
        }
        return response.json();
    })
    .then(data => {
        // Render stats
        if (statsContainer) {
            renderDashboardStats(data, statsContainer);
        }
        
        // Render activity
        if (activityContainer && data.recent_activity) {
            renderRecentActivity(data.recent_activity, activityContainer);
        }
    })
    .catch(error => {
        console.error('Error loading dashboard stats:', error);
        
        if (error.message !== 'Unauthorized') {
            // Show error message in container
            if (statsContainer) {
                statsContainer.innerHTML = `<div class="error-message">Error loading statistics: ${error.message}</div>`;
            }
            
            if (activityContainer) {
                activityContainer.innerHTML = `<div class="error-message">Error loading recent activity: ${error.message}</div>`;
            }
        }
    });
}

// Render dashboard statistics
function renderDashboardStats(data, container) {
    // Create stats cards for article counts
    const articlesHtml = `
        <div class="stats-card">
            <h3>Articles</h3>
            <div class="stats-grid">
                <div class="stat-item">
                    <div class="stat-value">${data.articles || 0}</div>
                    <div class="stat-label">Total</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${data.published_articles || 0}</div>
                    <div class="stat-label">Published</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${data.draft_articles || 0}</div>
                    <div class="stat-label">Drafts</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${data.hidden_articles || 0}</div>
                    <div class="stat-label">Hidden</div>
                </div>
            </div>
        </div>
    `;
    
    // Create stats cards for user counts
    const usersHtml = `
        <div class="stats-card">
            <h3>Users</h3>
            <div class="stats-grid">
                <div class="stat-item">
                    <div class="stat-value">${data.users || 0}</div>
                    <div class="stat-label">Total</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${data.admins || 0}</div>
                    <div class="stat-label">Admins</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${data.editors || 0}</div>
                    <div class="stat-label">Editors</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${data.regular_users || 0}</div>
                    <div class="stat-label">Regular</div>
                </div>
            </div>
        </div>
    `;
    
    // Create stats cards for recent activity counts
    const recentStatsHtml = `
        <div class="stats-card">
            <h3>Last 7 Days</h3>
            <div class="stats-grid">
                <div class="stat-item">
                    <div class="stat-value">${data.new_users_week || 0}</div>
                    <div class="stat-label">New Users</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${data.new_articles_week || 0}</div>
                    <div class="stat-label">New Articles</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${data.edits_week || 0}</div>
                    <div class="stat-label">Edits</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${data.proposals_week || 0}</div>
                    <div class="stat-label">Proposals</div>
                </div>
            </div>
        </div>
    `;
    
    // Create stats card for pending items that need attention
    const pendingHtml = `
        <div class="stats-card attention-required">
            <h3>Attention Required</h3>
            <div class="attention-items">
                <div class="attention-item">
                    <div class="attention-value">${data.pending_proposals || 0}</div>
                    <div class="attention-label">Pending Proposals</div>
                    <a href="#proposals-tab" class="attention-action">Review</a>
                </div>
            </div>
        </div>
    `;
    
    // Combine all HTML
    container.innerHTML = articlesHtml + usersHtml + recentStatsHtml + pendingHtml;
    
    // Set up tab links within the stats cards
    const tabLinks = container.querySelectorAll('[href^="#"]');
    tabLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Get tab ID from href
            const tabId = this.getAttribute('href').substring(1);
            
            // Find and click the corresponding tab link
            const tabLink = document.querySelector(`.admin-tab-link[href="#${tabId}"]`);
            if (tabLink) {
                tabLink.click();
            }
        });
    });
}

// Render recent activity
function renderRecentActivity(activities, container) {
    if (!activities || activities.length === 0) {
        container.innerHTML = '<p>No recent activity found.</p>';
        return;
    }

    let html = '<div class="activity-list">';
    
    activities.forEach(activity => {
        // Format timestamp
        const date = new Date(activity.timestamp);
        const formattedDate = date.toLocaleString();
        
        // Activity icon
        let icon = '';
        let actionText = '';
        
        switch (activity.type) {
            case 'edit':
                icon = '<span class="activity-icon edit-icon">✏️</span>';
                actionText = 'edited';
                break;
            case 'proposal':
                icon = '<span class="activity-icon proposal-icon">📝</span>';
                actionText = 'proposed changes to';
                break;
            case 'new_user':
                icon = '<span class="activity-icon user-icon">👤</span>';
                actionText = 'joined';
                break;
            default:
                icon = '<span class="activity-icon">📄</span>';
                actionText = 'interacted with';
        }
        
        // Create activity item HTML
        html += `
            <div class="activity-item">
                ${icon}
                <div class="activity-content">
                    <span class="activity-user">${activity.user?.username || 'Unknown user'}</span>
                    ${activity.type === 'new_user' ? 'joined Kryptopedia' : 
                      `${actionText} <a href="/articles/${activity.article?.slug || ''}">${activity.article?.title || 'Unknown article'}</a>`}
                </div>
                <div class="activity-time">${formattedDate}</div>
            </div>
        `;
    });
    
    html += '</div>';
    container.innerHTML = html;
}

// User management functions
function setupUserManagement() {
    // Setup user search form
    const userSearchForm = document.getElementById('user-search-form');
    if (userSearchForm) {
        userSearchForm.addEventListener('submit', function(e) {
            e.preventDefault();
            loadUsers();
        });
    }
    
    // Setup user edit functionality
    document.addEventListener('click', function(e) {
        // Edit user button
        if (e.target.classList.contains('edit-user-btn') || e.target.closest('.edit-user-btn')) {
            const btn = e.target.classList.contains('edit-user-btn') ? e.target : e.target.closest('.edit-user-btn');
            const userId = btn.getAttribute('data-user-id');
            
            if (userId) {
                openUserEditModal(userId);
            }
        }
        
        // Delete user button
        if (e.target.classList.contains('delete-user-btn') || e.target.closest('.delete-user-btn')) {
            const btn = e.target.classList.contains('delete-user-btn') ? e.target : e.target.closest('.delete-user-btn');
            const userId = btn.getAttribute('data-user-id');
            const username = btn.getAttribute('data-username');
            
            if (userId && username) {
                confirmDeleteUser(userId, username);
            }
        }
    });
    
    // Setup user edit form
    const userEditForm = document.getElementById('user-edit-form');
    if (userEditForm) {
        userEditForm.addEventListener('submit', function(e) {
            e.preventDefault();
            submitUserEdit();
        });
    }
}

// Load users for the user management tab
function loadUsers() {
    const token = localStorage.getItem('token');
    if (!token) return;
    
    const usersContainer = document.getElementById('users-table-container');
    if (!usersContainer) return;
    
    // Show loading indicator
    usersContainer.innerHTML = '<div class="loading-spinner"></div>';
    
    // Get search parameters
    const searchInput = document.getElementById('user-search');
    const roleFilter = document.getElementById('role-filter');
    
    let searchParams = new URLSearchParams();
    if (searchInput && searchInput.value) {
        searchParams.append('search', searchInput.value);
    }
    
    if (roleFilter && roleFilter.value) {
        searchParams.append('role', roleFilter.value);
    }
    
    // Fetch users
    fetch(`/api/admin/users?${searchParams.toString()}`, {
        headers: {
            'Authorization': `Bearer ${token}`
        }
    })
    .then(response => {
        if (!response.ok) {
            if (response.status === 401 || response.status === 403) {
                window.location.href = '/login?redirect=' + encodeURIComponent(window.location.pathname);
                throw new Error('Unauthorized');
            }
            return response.json().then(data => {
                throw new Error(data.detail || 'Failed to load users');
            });
        }
        return response.json();
    })
    .then(data => {
        renderUsersTable(data, usersContainer);
    })
    .catch(error => {
        console.error('Error loading users:', error);
        
        if (error.message !== 'Unauthorized') {
            usersContainer.innerHTML = `<div class="error-message">Error loading users: ${error.message}</div>`;
        }
    });
}

// Render the users table
function renderUsersTable(data, container) {
    if (!data.users || data.users.length === 0) {
        container.innerHTML = '<p>No users found matching your criteria.</p>';
        return;
    }
    
    // Create table
    let html = `
        <table id="users-table" class="admin-table">
            <thead>
                <tr>
                    <th>Username</th>
                    <th>Email</th>
                    <th>Role</th>
                    <th>Join Date</th>
                    <th>Last Login</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
    `;
    
    // Add rows
    data.users.forEach(user => {
        const joinDate = new Date(user.joinDate || user.createdAt).toLocaleDateString();
        const lastLogin = user.lastLogin ? new Date(user.lastLogin).toLocaleDateString() : 'Never';
        
        html += `
            <tr>
                <td>${user.username}</td>
                <td>${user.email}</td>
                <td><span class="role-badge role-${user.role}">${user.role}</span></td>
                <td>${joinDate}</td>
                <td>${lastLogin}</td>
                <td>
                    <div class="table-actions">
                        <button class="edit-user-btn" data-user-id="${user._id}">Edit</button>
                        <button class="delete-user-btn" data-user-id="${user._id}" data-username="${user.username}">Delete</button>
                    </div>
                </td>
            </tr>
        `;
    });
    
    html += `
            </tbody>
        </table>
        <div class="table-info">
            Showing ${data.users.length} of ${data.total} users
        </div>
    `;
    
    // Set HTML
    container.innerHTML = html;
    
    // Initialize DataTable if available
    if (typeof $.fn.DataTable !== 'undefined') {
        try {
            $('#users-table').DataTable({
                responsive: true,
                pageLength: 10,
                lengthMenu: [5, 10, 25, 50],
                language: {
                    search: "Filter:",
                    lengthMenu: "Show _MENU_ entries",
                    info: "Showing _START_ to _END_ of _TOTAL_ entries"
                }
            });
        } catch (e) {
            console.error('Error initializing DataTable for users:', e);
        }
    }
}

// Open user edit modal
function openUserEditModal(userId) {
    const token = localStorage.getItem('token');
    if (!token) return;
    
    const modal = document.getElementById('user-edit-modal');
    if (!modal) return;
    
    // Show loading state
    modal.querySelector('.modal-content').innerHTML = '<div class="loading-spinner"></div>';
    
    // Show modal
    modal.style.display = 'block';
    
    // Fetch user data
    fetch(`/api/admin/users/${userId}`, {
        headers: {
            'Authorization': `Bearer ${token}`
        }
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(data => {
                throw new Error(data.detail || 'Failed to load user data');
            });
        }
        return response.json();
    })
    .then(user => {
        renderUserEditForm(user, modal);
    })
    .catch(error => {
        console.error('Error loading user data:', error);
        modal.querySelector('.modal-content').innerHTML = `
            <div class="error-message">Error loading user data: ${error.message}</div>
            <div class="modal-actions">
                <button class="close-modal-btn">Close</button>
            </div>
        `;
        
        // Set up close button
        const closeBtn = modal.querySelector('.close-modal-btn');
        if (closeBtn) {
            closeBtn.addEventListener('click', function() {
                modal.style.display = 'none';
            });
        }
    });
}

// Render user edit form
function renderUserEditForm(user, modal) {
    const modalContent = modal.querySelector('.modal-content');
    
    // Create form HTML
    modalContent.innerHTML = `
        <h2>Edit User: ${user.username}</h2>
        <div class="error-message" id="edit-user-error" style="display: none;"></div>
        <form id="user-edit-form">
            <input type="hidden" id="user-id" value="${user._id}">
            
            <div class="form-group">
                <label for="edit-username">Username:</label>
                <input type="text" id="edit-username" value="${user.username}" required>
            </div>
            
            <div class="form-group">
                <label for="edit-email">Email:</label>
                <input type="email" id="edit-email" value="${user.email}" required>
            </div>
            
            <div class="form-group">
                <label for="edit-role">Role:</label>
                <select id="edit-role">
                    <option value="user" ${user.role === 'user' ? 'selected' : ''}>User</option>
                    <option value="editor" ${user.role === 'editor' ? 'selected' : ''}>Editor</option>
                    <option value="admin" ${user.role === 'admin' ? 'selected' : ''}>Admin</option>
                </select>
            </div>
            
            <div class="form-group">
                <label for="edit-password">New Password (leave blank to keep current):</label>
                <input type="password" id="edit-password">
            </div>
            
            <div class="modal-actions">
                <button type="submit" class="primary-button">Save Changes</button>
                <button type="button" class="cancel-button close-modal-btn">Cancel</button>
            </div>
        </form>
        
        <div class="user-stats">
            <h3>User Statistics</h3>
            <div class="stats-grid">
                <div class="stat-item">
                    <div class="stat-value">${user.statistics?.articles_created || 0}</div>
                    <div class="stat-label">Articles Created</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${user.statistics?.edits_performed || 0}</div>
                    <div class="stat-label">Edits Performed</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${user.statistics?.proposals_submitted || 0}</div>
                    <div class="stat-label">Proposals Submitted</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${user.statistics?.rewards_received || 0}</div>
                    <div class="stat-label">Rewards Received</div>
                </div>
            </div>
        </div>
    `;
    
    // Set up close button
    const closeBtn = modal.querySelector('.close-modal-btn');
    if (closeBtn) {
        closeBtn.addEventListener('click', function() {
            modal.style.display = 'none';
        });
    }
    
    // Set up form submission
    const form = modal.querySelector('#user-edit-form');
    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            submitUserEdit(modal);
        });
    }
    
    // Close modal when clicking outside
    window.addEventListener('click', function(event) {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    });
}

// Submit user edit form
function submitUserEdit(modal) {
    const token = localStorage.getItem('token');
    if (!token) return;
    
    const errorElement = document.getElementById('edit-user-error');
    const userId = document.getElementById('user-id').value;
    const username = document.getElementById('edit-username').value;
    const email = document.getElementById('edit-email').value;
    const role = document.getElementById('edit-role').value;
    const password = document.getElementById('edit-password').value;
    
    // Validate input
    if (!username || !email) {
        if (errorElement) {
            errorElement.textContent = 'Username and email are required';
            errorElement.style.display = 'block';
        }
        return;
    }
    
    // Build user data
    const userData = {
        username: username,
        email: email,
        role: role
    };
    
    // Add password if provided
    if (password) {
        userData.password = password;
    }
    
    // Show loading state
    const submitButton = document.querySelector('#user-edit-form button[type="submit"]');
    if (submitButton) {
        const originalText = submitButton.textContent;
        submitButton.disabled = true;
        submitButton.textContent = 'Saving...';
    }
    
    // Hide error if shown
    if (errorElement) {
        errorElement.style.display = 'none';
    }
    
    // Send update request
    fetch(`/api/admin/users/${userId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(userData)
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(data => {
                throw new Error(data.detail || 'Failed to update user');
            });
        }
        return response.json();
    })
    .then(updatedUser => {
        // Show success message
        alert('User updated successfully');
        
        // Close modal
        if (modal) {
            modal.style.display = 'none';
        }
        
        // Reload users
        loadUsers();
    })
    .catch(error => {
        console.error('Error updating user:', error);
        
        // Show error message
        if (errorElement) {
            errorElement.textContent = error.message;
            errorElement.style.display = 'block';
        } else {
            alert(`Error updating user: ${error.message}`);
        }
    })
    .finally(() => {
        // Reset button state
        if (submitButton) {
            submitButton.disabled = false;
            submitButton.textContent = 'Save Changes';
        }
    });
}

// Confirm user deletion
function confirmDeleteUser(userId, username) {
    if (confirm(`Are you sure you want to delete the user "${username}"? This action cannot be undone.`)) {
        deleteUser(userId);
    }
}

// Delete a user
function deleteUser(userId) {
    const token = localStorage.getItem('token');
    if (!token) return;
    
    fetch(`/api/admin/users/${userId}`, {
        method: 'DELETE',
        headers: {
            'Authorization': `Bearer ${token}`
        }
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(data => {
                throw new Error(data.detail || 'Failed to delete user');
            });
        }
        return response.json();
    })
    .then(result => {
        // Show success message
        alert(result.message || 'User deleted successfully');
        
        // Reload users
        loadUsers();
    })
    .catch(error => {
        console.error('Error deleting user:', error);
        alert(`Error deleting user: ${error.message}`);
    });
}

// Article management functions
function setupArticleManagement() {
    // Setup article search form
    const articleSearchForm = document.getElementById('article-search-form');
    if (articleSearchForm) {
        articleSearchForm.addEventListener('submit', function(e) {
            e.preventDefault();
            loadArticles();
        });
    }
}

// Load articles for the article management tab
function loadArticles() {
    const token = localStorage.getItem('token');
    if (!token) return;
    
    const articlesContainer = document.getElementById('articles-table-container');
    if (!articlesContainer) return;
    
    // Show loading indicator
    articlesContainer.innerHTML = '<div class="loading-spinner"></div>';
    
    // Get article stats
    fetch('/api/admin/articles/stats', {
        headers: {
            'Authorization': `Bearer ${token}`
        }
    })
    .then(response => {
        if (!response.ok) {
            if (response.status === 401 || response.status === 403) {
                window.location.href = '/login?redirect=' + encodeURIComponent(window.location.pathname);
                throw new Error('Unauthorized');
            }
            return response.json().then(data => {
                throw new Error(data.detail || 'Failed to load article statistics');
            });
        }
        return response.json();
    })
    .then(statsData => {
        renderArticleStats(statsData, articlesContainer);
    })
    .catch(error => {
        console.error('Error loading article stats:', error);
        
        if (error.message !== 'Unauthorized') {
            articlesContainer.innerHTML = `<div class="error-message">Error loading article statistics: ${error.message}</div>`;
        }
    });
}

// Render article statistics
function renderArticleStats(data, container) {
    // Create HTML
    let html = `
        <div class="admin-stats-section">
            <h3>Article Statistics</h3>
            <div class="stats-grid">
                <div class="stat-item">
                    <div class="stat-value">${data.total || 0}</div>
                    <div class="stat-label">Total Articles</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${data.published || 0}</div>
                    <div class="stat-label">Published</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${data.draft || 0}</div>
                    <div class="stat-label">Drafts</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${data.hidden || 0}</div>
                    <div class="stat-label">Hidden</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${data.archived || 0}</div>
                    <div class="stat-label">Archived</div>
                </div>
            </div>
        </div>
    `;
    
    // Add most viewed articles
    if (data.most_viewed && data.most_viewed.length > 0) {
        html += `
            <div class="admin-data-section">
                <h3>Most Viewed Articles</h3>
                <table class="admin-table">
                    <thead>
                        <tr>
                            <th>Title</th>
                            <th>Views</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
        `;
        
        data.most_viewed.forEach(article => {
            html += `
                <tr>
                    <td><a href="/articles/${article.slug || article.id}">${article.title}</a></td>
                    <td>${article.views}</td>
                    <td>
                        <div class="table-actions">
                            <a href="/edit-article/${article.id}" class="edit-btn">Edit</a>
                            <a href="/articles/${article.id}/history" class="history-btn">History</a>
                        </div>
                    </td>
                </tr>
            `;
        });
        
        html += `
                    </tbody>
                </table>
            </div>
        `;
    }
    
    // Add recently edited articles
    if (data.recently_edited && data.recently_edited.length > 0) {
        html += `
            <div class="admin-data-section">
                <h3>Recently Edited Articles</h3>
                <table class="admin-table">
                    <thead>
                        <tr>
                            <th>Title</th>
                            <th>Last Edit</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
        `;
        
        data.recently_edited.forEach(article => {
            const date = new Date(article.last_edit).toLocaleString();
            
            html += `
                <tr>
                    <td><a href="/articles/${article.slug || article.id}">${article.title}</a></td>
                    <td>${date}</td>
                    <td>
                        <div class="table-actions">
                            <a href="/edit-article/${article.id}" class="edit-btn">Edit</a>
                            <a href="/articles/${article.id}/history" class="history-btn">History</a>
                        </div>
                    </td>
                </tr>
            `;
        });
        
        html += `
                    </tbody>
                </table>
            </div>
        `;
    }
    
    // Add top categories
    if (data.top_categories && data.top_categories.length > 0) {
        html += `
            <div class="admin-data-section">
                <h3>Top Categories</h3>
                <div class="tag-cloud">
        `;
        
        data.top_categories.forEach(category => {
            html += `
                <a href="/articles?category=${encodeURIComponent(category._id)}" class="tag-item" style="font-size: ${Math.max(100, Math.min(160, 100 + category.count * 10))}%">
                    ${category._id} (${category.count})
                </a>
            `;
        });
        
        html += `
                </div>
            </div>
        `;
    }
    
    // Set HTML
    container.innerHTML = html;
}

// Proposal management functions
function setupProposalManagement() {
    // Setup proposal filter form
    const proposalFilterForm = document.getElementById('proposal-filter-form');
    if (proposalFilterForm) {
        proposalFilterForm.addEventListener('submit', function(e) {
            e.preventDefault();
            loadProposals();
        });
    }
}

// Load proposals for the proposal management tab
function loadProposals() {
    const token = localStorage.getItem('token');
    if (!token) return;
    
    const proposalsContainer = document.getElementById('proposals-management');
    if (!proposalsContainer) return;
    
    // Show loading indicator
    proposalsContainer.innerHTML = '<div class="loading-spinner"></div>';
    
    // Get proposal stats
    fetch('/api/admin/proposals/stats', {
        headers: {
            'Authorization': `Bearer ${token}`
        }
    })
    .then(response => {
        if (!response.ok) {
            if (response.status === 401 || response.status === 403) {
                window.location.href = '/login?redirect=' + encodeURIComponent(window.location.pathname);
                throw new Error('Unauthorized');
            }
            return response.json().then(data => {
                throw new Error(data.detail || 'Failed to load proposal statistics');
            });
        }
        return response.json();
    })
    .then(statsData => {
        renderProposalStats(statsData, proposalsContainer);
    })
    .catch(error => {
        console.error('Error loading proposal stats:', error);
        
        if (error.message !== 'Unauthorized') {
            proposalsContainer.innerHTML = `<div class="error-message">Error loading proposal statistics: ${error.message}</div>`;
        }
    });
}

// Render proposal statistics
function renderProposalStats(data, container) {
    // Create HTML
    let html = `
        <div class="admin-stats-section">
            <h3>Proposal Statistics</h3>
            <div class="stats-grid">
                <div class="stat-item">
                    <div class="stat-value">${data.total || 0}</div>
                    <div class="stat-label">Total Proposals</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${data.pending || 0}</div>
                    <div class="stat-label">Pending</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${data.approved || 0}</div>
                    <div class="stat-label">Approved</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${data.rejected || 0}</div>
                    <div class="stat-label">Rejected</div>
                </div>
            </div>
        </div>
    `;
    
    // Add recent proposals
    if (data.recent_proposals && data.recent_proposals.length > 0) {
        html += `
            <div class="admin-data-section">
                <h3>Recent Proposals</h3>
                <table class="admin-table">
                    <thead>
                        <tr>
                            <th>Article</th>
                            <th>User</th>
                            <th>Status</th>
                            <th>Date</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
        `;
        
        data.recent_proposals.forEach(proposal => {
            const date = new Date(proposal.proposedAt).toLocaleString();
            const statusClass = proposal.status === 'pending' ? 'status-pending' : 
                                proposal.status === 'approved' ? 'status-approved' : 'status-rejected';
            
            html += `
                <tr>
                    <td><a href="/articles/${proposal.article.slug || proposal.article.id}">${proposal.article.title}</a></td>
                    <td>${proposal.user.username}</td>
                    <td><span class="status-badge ${statusClass}">${proposal.status}</span></td>
                    <td>${date}</td>
                    <td>
                        <div class="table-actions">
                            <a href="/articles/${proposal.article.id}/proposals/${proposal.id}" class="view-btn">View</a>
                            ${proposal.status === 'pending' ? `
                                <button class="approve-btn" data-proposal-id="${proposal.id}" data-article-id="${proposal.article.id}">Approve</button>
                                <button class="reject-btn" data-proposal-id="${proposal.id}" data-article-id="${proposal.article.id}">Reject</button>
                            ` : ''}
                        </div>
                    </td>
                </tr>
            `;
        });
        
        html += `
                    </tbody>
                </table>
                
                <div class="view-all-link">
                    <a href="/proposals" class="action-link">View All Proposals</a>
                </div>
            </div>
        `;
    }
    
    // Add top contributors
    if (data.top_contributors && data.top_contributors.length > 0) {
        html += `
            <div class="admin-data-section">
                <h3>Top Proposal Contributors</h3>
                <div class="top-contributors">
        `;
        
        data.top_contributors.forEach(contributor => {
            html += `
                <div class="contributor-card">
                    <div class="contributor-name">${contributor.user.username}</div>
                    <div class="contributor-count">${contributor.count} proposals</div>
                </div>
            `;
        });
        
        html += `
                </div>
            </div>
        `;
    }
    
    // Set HTML
    container.innerHTML = html;
    
    // Set up event listeners for approve/reject buttons
    const approveButtons = container.querySelectorAll('.approve-btn');
    const rejectButtons = container.querySelectorAll('.reject-btn');
    
    approveButtons.forEach(button => {
        button.addEventListener('click', function() {
            const proposalId = this.getAttribute('data-proposal-id');
            const articleId = this.getAttribute('data-article-id');
            if (proposalId && articleId) {
                handleProposalAction(articleId, proposalId, 'approve');
            }
        });
    });
    
    rejectButtons.forEach(button => {
        button.addEventListener('click', function() {
            const proposalId = this.getAttribute('data-proposal-id');
            const articleId = this.getAttribute('data-article-id');
            if (proposalId && articleId) {
                handleProposalAction(articleId, proposalId, 'reject');
            }
        });
    });
}

// Handle proposal approval/rejection
function handleProposalAction(articleId, proposalId, action) {
    const token = localStorage.getItem('token');
    if (!token) return;
    
    // Ask for comment
    const comment = prompt(`Please provide a reason for ${action}ing this proposal:`);
    
    // User cancelled
    if (comment === null) return;
    
    // Show loading state
    const button = document.querySelector(`[data-proposal-id="${proposalId}"][data-article-id="${articleId}"]`);
    if (button) {
        const originalText = button.textContent;
        button.disabled = true;
        button.textContent = 'Processing...';
    }
    
    // Send request
    fetch(`/api/articles/${articleId}/proposals/${proposalId}?status=${action}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ comment: comment })
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(data => {
                throw new Error(data.detail || `Failed to ${action} proposal`);
            });
        }
        return response.json();
    })
    .then(result => {
        // Show success message
        alert(`Proposal ${action}ed successfully`);
        
        // Reload proposals
        loadProposals();
    })
    .catch(error => {
        console.error(`Error ${action}ing proposal:`, error);
        alert(`Error ${action}ing proposal: ${error.message}`);
        
        // Reset button state
        if (button) {
            button.disabled = false;
            button.textContent = originalText;
        }
    });
}

// System tools functions
function setupSystemTools() {
    // Setup cache clear button
    const clearCacheButton = document.getElementById('clear-cache-btn');
    if (clearCacheButton) {
        clearCacheButton.addEventListener('click', function() {
            clearSystemCache();
        });
    }
}

// Clear system cache
function clearSystemCache() {
    const token = localStorage.getItem('token');
    if (!token) return;
    
    if (!confirm('Are you sure you want to clear the system cache? This may temporarily impact performance but can resolve data consistency issues.')) {
        return;
    }
    
    // Show loading state
    const button = document.getElementById('clear-cache-btn');
    if (button) {
        const originalText = button.textContent;
        button.disabled = true;
        button.textContent = 'Clearing...';
    }
    
    // Send request
    fetch('/api/admin/system/clear-cache', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`
        }
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(data => {
                throw new Error(data.detail || 'Failed to clear cache');
            });
        }
        return response.json();
    })
    .then(result => {
        // Show success message
        alert(result.message || 'Cache cleared successfully');
        
        // Reset button state
        if (button) {
            button.disabled = false;
            button.textContent = originalText;
        }
    })
    .catch(error => {
        console.error('Error clearing cache:', error);
        alert(`Error clearing cache: ${error.message}`);
        
        // Reset button state
        if (button) {
            button.disabled = false;
            button.textContent = originalText;
        }
    });
}
