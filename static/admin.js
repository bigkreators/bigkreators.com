// File: static/admin.js
// Admin functionality for Kryptopedia

document.addEventListener('DOMContentLoaded', function() {
    initAdminDashboard();
    setupTabNavigation();
    loadDashboardStats();
    setupUserManagement();
    setupArticleManagement();
    setupProposalManagement();
    setupSystemTools();
});

// Initialize admin dashboard
function initAdminDashboard() {
    // Check if user is admin/editor
    const token = localStorage.getItem('token');
    if (!token) {
        window.location.href = '/'; // Redirect to home if not logged in
        return;
    }

    // Set up refresh button
    const refreshButton = document.getElementById('refresh-stats');
    if (refreshButton) {
        refreshButton.addEventListener('click', function() {
            loadDashboardStats(true); // Force refresh
        });
    }
}

// Setup tab navigation - this is the fixed function
function setupTabNavigation() {
    const tabLinks = document.querySelectorAll('.admin-tab-link');
    const tabContents = document.querySelectorAll('.admin-tab-content');
    
    // Get tab from URL hash or default to first tab
    const hash = window.location.hash;
    const defaultTab = tabContents.length > 0 ? tabContents[0].id : 'users-tab';
    const initialTab = hash ? hash.substring(1) : defaultTab;
    
    // Activate the initial tab
    activateTab(initialTab);
    
    // Add click handlers to tab links
    tabLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const tabId = this.getAttribute('href').substring(1);
            
            // Update URL hash without page reload
            window.location.hash = tabId;
            
            // Activate the selected tab
            activateTab(tabId);
        });
    });
    
    // Function to activate a tab
    function activateTab(tabId) {
        // Hide all tabs
        tabContents.forEach(tab => {
            tab.classList.remove('active');
        });
        
        // Show selected tab
        const selectedTab = document.getElementById(tabId);
        if (selectedTab) {
            selectedTab.classList.add('active');
        }
        
        // Update tab links
        tabLinks.forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('href') === '#' + tabId) {
                link.classList.add('active');
            }
        });
        
        // Load tab-specific data as needed
        if (tabId === 'users-tab') {
            loadUsers();
        } else if (tabId === 'articles-tab') {
            loadArticles();
        } else if (tabId === 'proposals-tab') {
            loadProposals();
        }
    }
}

// Load dashboard statistics
function loadDashboardStats(forceRefresh = false) {
    const dashboardStats = document.getElementById('dashboard-stats');
    const recentActivity = document.getElementById('recent-activity');
    const token = localStorage.getItem('token');
    
    if (!dashboardStats || !recentActivity || !token) return;
    
    // Show loading state
    dashboardStats.innerHTML = '<div class="loading-spinner"></div>';
    recentActivity.innerHTML = '<div class="loading-spinner"></div>';
    
    // API endpoint with cache-busting if needed
    let endpoint = '/api/admin/dashboard/stats';
    if (forceRefresh) {
        endpoint += '?t=' + new Date().getTime();
    }
    
    // Fetch dashboard stats
    fetch(endpoint, {
        headers: {
            'Authorization': `Bearer ${token}`
        }
    })
    .then(response => {
        if (!response.ok) {
            if (response.status === 401) {
                // Unauthorized, redirect to login
                localStorage.removeItem('token');
                window.location.href = '/';
                throw new Error('Unauthorized');
            }
            throw new Error('Failed to load dashboard statistics');
        }
        return response.json();
    })
    .then(data => {
        // Render dashboard stats
        renderDashboardStats(data);
        
        // Render recent activity
        renderRecentActivity(data.recent_activity);
    })
    .catch(error => {
        console.error('Error loading dashboard stats:', error);
        dashboardStats.innerHTML = '<div class="error-message">Error loading dashboard statistics</div>';
        recentActivity.innerHTML = '<div class="error-message">Error loading recent activity</div>';
    });
}

// Render dashboard stats
function renderDashboardStats(data) {
    const dashboardStats = document.getElementById('dashboard-stats');
    
    // Create stats grid
    let html = '<div class="stats-grid">';
    
    // Article stats
    html += `
        <div class="stat-item">
            <div class="stat-value">${data.articles || 0}</div>
            <div class="stat-label">Total Articles</div>
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
    `;
    
    // User stats
    html += `
        <div class="stat-item">
            <div class="stat-value">${data.users || 0}</div>
            <div class="stat-label">Total Users</div>
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
            <div class="stat-value">${data.new_users_week || 0}</div>
            <div class="stat-label">New This Week</div>
        </div>
    `;
    
    // Activity stats
    html += `
        <div class="stat-item">
            <div class="stat-value">${data.edits_week || 0}</div>
            <div class="stat-label">Edits This Week</div>
        </div>
        <div class="stat-item">
            <div class="stat-value">${data.proposals_week || 0}</div>
            <div class="stat-label">Proposals This Week</div>
        </div>
        <div class="stat-item">
            <div class="stat-value">${data.pending_proposals || 0}</div>
            <div class="stat-label">Pending Proposals</div>
        </div>
        <div class="stat-item">
            <div class="stat-value">${data.new_articles_week || 0}</div>
            <div class="stat-label">New Articles This Week</div>
        </div>
    `;
    
    html += '</div>';
    
    // Add attention required section if there are pending proposals
    if (data.pending_proposals > 0) {
        html += `
            <div class="admin-section attention-required">
                <h3>Attention Required</h3>
                <div class="attention-items">
                    <div class="attention-item">
                        <div class="attention-value">${data.pending_proposals}</div>
                        <div class="attention-label">Pending Edit Proposals</div>
                        <a href="/proposals?status=pending" class="attention-action">Review Now</a>
                    </div>
                </div>
            </div>
        `;
    }
    
    dashboardStats.innerHTML = html;
}

// Render recent activity
function renderRecentActivity(activities) {
    const recentActivity = document.getElementById('recent-activity');
    
    if (!activities || activities.length === 0) {
        recentActivity.innerHTML = '<p>No recent activity</p>';
        return;
    }
    
    let html = '<div class="activity-list">';
    
    activities.forEach(activity => {
        let iconClass = '';
        let actionText = '';
        
        if (activity.type === 'edit') {
            iconClass = 'edit-icon';
            actionText = 'edited';
        } else if (activity.type === 'proposal') {
            iconClass = 'proposal-icon';
            actionText = 'proposed changes to';
        } else if (activity.type === 'new_user') {
            iconClass = 'user-icon';
            actionText = 'joined the wiki';
        }
        
        html += `
            <div class="activity-item">
                <div class="activity-icon ${iconClass}"></div>
                <div class="activity-content">
                    <span class="activity-user">${activity.user ? activity.user.username : 'Unknown'}</span>
        `;
        
        if (activity.type === 'new_user') {
            html += ` ${actionText}`;
        } else if (activity.article) {
            html += ` ${actionText} <a href="/articles/${activity.article.slug}">${activity.article.title}</a>`;
        }
        
        if (activity.comment) {
            html += `: "${activity.comment}"`;
        }
        
        // Format date
        const date = new Date(activity.timestamp);
        const formattedDate = date.toLocaleString();
        
        html += `</div>
                <div class="activity-time">${formattedDate}</div>
            </div>
        `;
    });
    
    html += '</div>';
    recentActivity.innerHTML = html;
}

// Setup user management
function setupUserManagement() {
    const userSearchForm = document.getElementById('user-search-form');
    
    if (userSearchForm) {
        userSearchForm.addEventListener('submit', function(e) {
            e.preventDefault();
            loadUsers();
        });
    }
}

// Load users
function loadUsers() {
    const userTableContainer = document.getElementById('users-table-container');
    const token = localStorage.getItem('token');
    
    if (!userTableContainer || !token) return;
    
    // Show loading state
    userTableContainer.innerHTML = '<div class="loading-spinner"></div>';
    
    // Get search params
    const searchInput = document.getElementById('user-search');
    const roleFilter = document.getElementById('role-filter');
    
    let search = searchInput ? searchInput.value : '';
    let role = roleFilter ? roleFilter.value : '';
    
    // Build API url
    let apiUrl = `/api/admin/users?limit=20`;
    if (search) apiUrl += `&search=${encodeURIComponent(search)}`;
    if (role) apiUrl += `&role=${encodeURIComponent(role)}`;
    
    // Fetch users
    fetch(apiUrl, {
        headers: {
            'Authorization': `Bearer ${token}`
        }
    })
    .then(response => {
        if (!response.ok) {
            if (response.status === 401) {
                localStorage.removeItem('token');
                window.location.href = '/';
                throw new Error('Unauthorized');
            }
            throw new Error('Failed to load users');
        }
        return response.json();
    })
    .then(data => {
        renderUsersTable(data.users || []);
    })
    .catch(error => {
        console.error('Error loading users:', error);
        userTableContainer.innerHTML = '<div class="error-message">Error loading users</div>';
    });
}

// Render users table
function renderUsersTable(users) {
    const userTableContainer = document.getElementById('users-table-container');
    
    if (!users || users.length === 0) {
        userTableContainer.innerHTML = '<p>No users found</p>';
        return;
    }
    
    let html = `
        <table class="admin-table">
            <thead>
                <tr>
                    <th>Username</th>
                    <th>Email</th>
                    <th>Role</th>
                    <th>Join Date</th>
                    <th>Articles</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
    `;
    
    users.forEach(user => {
        // Format date
        const joinDate = user.joinDate ? new Date(user.joinDate) : new Date();
        const formattedDate = joinDate.toLocaleDateString();
        
        // Get role badge class
        let roleBadgeClass = '';
        if (user.role === 'admin') {
            roleBadgeClass = 'role-admin';
        } else if (user.role === 'editor') {
            roleBadgeClass = 'role-editor';
        } else {
            roleBadgeClass = 'role-user';
        }
        
        html += `
            <tr id="user-row-${user._id}">
                <td>${user.username}</td>
                <td>${user.email}</td>
                <td><span class="role-badge ${roleBadgeClass}">${user.role}</span></td>
                <td>${formattedDate}</td>
                <td>${user.contributions?.articlesCreated || 0}</td>
                <td class="table-actions">
                    <a href="/users/${user._id}" class="view-btn">View</a>
                    <a href="/users/${user._id}/edit" class="edit-user-btn">Edit</a>
                    <button class="change-role-btn" data-userid="${user._id}" data-username="${user.username}" data-role="${user.role}">Change Role</button>
                    <button class="delete-user-btn" data-userid="${user._id}" data-username="${user.username}">Delete</button>
                </td>
            </tr>
        `;
    });
    
    html += `
            </tbody>
        </table>
    `;
    
    userTableContainer.innerHTML = html;
    
    // Setup change role buttons
    const changeRoleButtons = document.querySelectorAll('.change-role-btn');
    changeRoleButtons.forEach(button => {
        button.addEventListener('click', function() {
            const userId = this.getAttribute('data-userid');
            const username = this.getAttribute('data-username');
            const currentRole = this.getAttribute('data-role');
            
            showChangeRoleDialog(userId, username, currentRole);
        });
    });
    
    // Setup delete user buttons
    const deleteUserButtons = document.querySelectorAll('.delete-user-btn');
    deleteUserButtons.forEach(button => {
        button.addEventListener('click', function() {
            const userId = this.getAttribute('data-userid');
            const username = this.getAttribute('data-username');
            
            confirmDeleteUser(userId, username);
        });
    });
}

// Show change role dialog
function showChangeRoleDialog(userId, username, currentRole) {
    // Create modal content
    const modal = document.getElementById('user-edit-modal');
    const modalContent = modal.querySelector('.modal-content');
    
    modalContent.innerHTML = `
        <span class="close-modal-btn">&times;</span>
        <h2>Change Role for ${username}</h2>
        
        <div class="form-group">
            <label>Select Role:</label>
            <select id="new-role">
                <option value="user" ${currentRole === 'user' ? 'selected' : ''}>Regular User</option>
                <option value="editor" ${currentRole === 'editor' ? 'selected' : ''}>Editor</option>
                <option value="admin" ${currentRole === 'admin' ? 'selected' : ''}>Administrator</option>
            </select>
        </div>
        
        <div class="modal-actions">
            <button id="save-role-btn" class="primary-button">Save Changes</button>
            <button id="cancel-role-btn" class="cancel-button">Cancel</button>
        </div>
    `;
    
    // Show modal
    modal.style.display = 'block';
    
    // Setup close button
    const closeBtn = modalContent.querySelector('.close-modal-btn');
    closeBtn.addEventListener('click', function() {
        modal.style.display = 'none';
    });
    
    // Setup cancel button
    const cancelBtn = document.getElementById('cancel-role-btn');
    cancelBtn.addEventListener('click', function() {
        modal.style.display = 'none';
    });
    
    // Setup save button
    const saveBtn = document.getElementById('save-role-btn');
    saveBtn.addEventListener('click', function() {
        const newRole = document.getElementById('new-role').value;
        
        if (newRole === currentRole) {
            alert('No change in role');
            return;
        }
        
        changeUserRole(userId, newRole);
    });
    
    // Close when clicking outside
    window.addEventListener('click', function(event) {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    });
}

// Change user role
function changeUserRole(userId, newRole) {
    const token = localStorage.getItem('token');
    if (!token) return;
    
    // Show loading state
    const saveButton = document.getElementById('save-role-btn');
    const originalText = saveButton.textContent;
    saveButton.disabled = true;
    saveButton.textContent = 'Saving...';
    
    // Call API to change role
    fetch(`/api/admin/users/${userId}/role?role=${newRole}`, {
        method: 'PUT',
        headers: {
            'Authorization': `Bearer ${token}`
        }
    })
    .then(response => {
        if (!response.ok) {
            if (response.status === 401) {
                localStorage.removeItem('token');
                window.location.href = '/';
                throw new Error('Unauthorized');
            }
            return response.json().then(data => {
                throw new Error(data.detail || 'Failed to change user role');
            });
        }
        return response.json();
    })
    .then(data => {
        // Close modal
        document.getElementById('user-edit-modal').style.display = 'none';
        
        // Show success alert
        alert(data.message || 'User role updated successfully');
        
        // Update user row in the table
        const userRow = document.getElementById(`user-row-${userId}`);
        if (userRow) {
            const roleCell = userRow.querySelector('td:nth-child(3)');
            const actionCell = userRow.querySelector('td:nth-child(6)');
            
            // Update role badge
            let roleBadgeClass = '';
            if (newRole === 'admin') {
                roleBadgeClass = 'role-admin';
            } else if (newRole === 'editor') {
                roleBadgeClass = 'role-editor';
            } else {
                roleBadgeClass = 'role-user';
            }
            
            if (roleCell) {
                roleCell.innerHTML = `<span class="role-badge ${roleBadgeClass}">${newRole}</span>`;
            }
            
            // Update change role button data attribute
            if (actionCell) {
                const changeRoleBtn = actionCell.querySelector('.change-role-btn');
                if (changeRoleBtn) {
                    changeRoleBtn.setAttribute('data-role', newRole);
                }
            }
        }
    })
    .catch(error => {
        console.error('Error changing user role:', error);
        alert(error.message || 'Failed to change user role');
        
        // Reset button state
        saveButton.disabled = false;
        saveButton.textContent = originalText;
    });
}

// Confirm delete user
function confirmDeleteUser(userId, username) {
    if (confirm(`Are you sure you want to delete user "${username}"? This action cannot be undone.`)) {
        deleteUser(userId, username);
    }
}

// Delete user
function deleteUser(userId, username) {
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
            if (response.status === 401) {
                localStorage.removeItem('token');
                window.location.href = '/';
                throw new Error('Unauthorized');
            }
            return response.json().then(data => {
                throw new Error(data.detail || 'Failed to delete user');
            });
        }
        return response.json();
    })
    .then(data => {
        // Show success alert
        alert(data.message || 'User deleted successfully');
        
        // Remove user row from the table
        const userRow = document.getElementById(`user-row-${userId}`);
        if (userRow) {
            userRow.remove();
        }
    })
    .catch(error => {
        console.error('Error deleting user:', error);
        alert(error.message || 'Failed to delete user');
    });
}

// Setup article management
function setupArticleManagement() {
    const articleSearchForm = document.getElementById('article-search-form');
    
    if (articleSearchForm) {
        articleSearchForm.addEventListener('submit', function(e) {
            e.preventDefault();
            loadArticles();
        });
    }
}

// Load articles
function loadArticles() {
    const articleTableContainer = document.getElementById('articles-table-container');
    const token = localStorage.getItem('token');
    
    if (!articleTableContainer || !token) return;
    
    // Show loading state
    articleTableContainer.innerHTML = '<div class="loading-spinner"></div>';
    
    // Get search params
    const searchInput = document.getElementById('article-search');
    const statusFilter = document.getElementById('status-filter');
    
    let search = searchInput ? searchInput.value : '';
    let status = statusFilter ? statusFilter.value : '';
    
    // Build API url
    let apiUrl = '/api/admin/articles?limit=20';
    if (search) apiUrl += `&search=${encodeURIComponent(search)}`;
    if (status) apiUrl += `&status=${encodeURIComponent(status)}`;
    
    // Fetch articles
    fetch(apiUrl, {
        headers: {
            'Authorization': `Bearer ${token}`
        }
    })
    .then(response => {
        if (!response.ok) {
            if (response.status === 401) {
                localStorage.removeItem('token');
                window.location.href = '/';
                throw new Error('Unauthorized');
            }
            throw new Error('Failed to load articles');
        }
        return response.json();
    })
    .then(data => {
        renderArticlesTable(data.articles || []);
    })
    .catch(error => {
        console.error('Error loading articles:', error);
        articleTableContainer.innerHTML = '<div class="error-message">Error loading articles</div>';
    });
}

// Render articles table
function renderArticlesTable(articles) {
    const articleTableContainer = document.getElementById('articles-table-container');
    
    if (!articles || articles.length === 0) {
        articleTableContainer.innerHTML = '<p>No articles found</p>';
        return;
    }
    
    let html = `
        <table class="admin-table">
            <thead>
                <tr>
                    <th>Title</th>
                    <th>Author</th>
                    <th>Date Created</th>
                    <th>Status</th>
                    <th>Views</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
    `;
    
    articles.forEach(article => {
        // Format date
        const createdAt = article.createdAt ? new Date(article.createdAt) : new Date();
        const formattedDate = createdAt.toLocaleDateString();
        
        // Get status badge class
        let statusBadgeClass = '';
        if (article.status === 'published') {
            statusBadgeClass = 'status-published';
        } else if (article.status === 'draft') {
            statusBadgeClass = 'status-draft';
        } else if (article.status === 'hidden') {
            statusBadgeClass = 'status-hidden';
        } else if (article.status === 'archived') {
            statusBadgeClass = 'status-archived';
        }
        
        html += `
            <tr id="article-row-${article._id}">
                <td><a href="/articles/${article.slug}">${article.title}</a></td>
                <td>${article.creatorUsername || 'Unknown'}</td>
                <td>${formattedDate}</td>
                <td><span class="status-badge ${statusBadgeClass}">${article.status}</span></td>
                <td>${article.views || 0}</td>
                <td class="table-actions">
                    <a href="/articles/${article.slug}" class="view-btn">View</a>
                    <a href="/edit-article/${article._id}" class="edit-btn">Edit</a>
                    <a href="/articles/${article._id}/history" class="history-btn">History</a>
                    <button class="delete-btn" data-articleid="${article._id}" data-title="${article.title}">Delete</button>
                </td>
            </tr>
        `;
    });
    
    html += `
            </tbody>
        </table>
    `;
    
    articleTableContainer.innerHTML = html;
    
    // Setup delete article buttons
    const deleteArticleButtons = document.querySelectorAll('.delete-btn');
    deleteArticleButtons.forEach(button => {
        button.addEventListener('click', function() {
            const articleId = this.getAttribute('data-articleid');
            const title = this.getAttribute('data-title');
            
            confirmDeleteArticle(articleId, title);
        });
    });
}

// Confirm delete article
function confirmDeleteArticle(articleId, title) {
    if (confirm(`Are you sure you want to delete article "${title}"? This action cannot be undone.`)) {
        deleteArticle(articleId);
    }
}

// Delete article
function deleteArticle(articleId) {
    const token = localStorage.getItem('token');
    if (!token) return;
    
    fetch(`/api/articles/${articleId}?permanent=true`, {
        method: 'DELETE',
        headers: {
            'Authorization': `Bearer ${token}`
        }
    })
    .then(response => {
        if (!response.ok) {
            if (response.status === 401) {
                localStorage.removeItem('token');
                window.location.href = '/';
                throw new Error('Unauthorized');
            }
            return response.json().then(data => {
                throw new Error(data.detail || 'Failed to delete article');
            });
        }
        return response.json();
    })
    .then(data => {
        // Show success alert
        alert(data.message || 'Article deleted successfully');
        
        // Remove article row from the table
        const articleRow = document.getElementById(`article-row-${articleId}`);
        if (articleRow) {
            articleRow.remove();
        }
    })
    .catch(error => {
        console.error('Error deleting article:', error);
        alert(error.message || 'Failed to delete article');
    });
}

// Setup proposal management
function setupProposalManagement() {
    const proposalFilterForm = document.getElementById('proposal-filter-form');
    
    if (proposalFilterForm) {
        proposalFilterForm.addEventListener('submit', function(e) {
            e.preventDefault();
            loadProposals();
        });
    }
}

// Load proposals
function loadProposals() {
    const proposalsManagement = document.getElementById('proposals-management');
    const token = localStorage.getItem('token');
    
    if (!proposalsManagement || !token) return;
    
    // Show loading state
    proposalsManagement.innerHTML = '<div class="loading-spinner"></div>';
    
    // Get filter params
    const statusFilter = document.getElementById('proposal-status-filter');
    let status = statusFilter ? statusFilter.value : 'pending';
    
    // Build API url
    let apiUrl = '/api/proposals?limit=20';
    if (status) apiUrl += `&status=${encodeURIComponent(status)}`;
    
    // Fetch proposals
    fetch(apiUrl, {
        headers: {
            'Authorization': `Bearer ${token}`
        }
    })
    .then(response => {
        if (!response.ok) {
            if (response.status === 401) {
                localStorage.removeItem('token');
                window.location.href = '/';
                throw new Error('Unauthorized');
            }
            throw new Error('Failed to load proposals');
        }
        return response.json();
    })
    .then(data => {
        renderProposalsTable(data.proposals || [], status);
    })
    .catch(error => {
        console.error('Error loading proposals:', error);
        proposalsManagement.innerHTML = '<div class="error-message">Error loading proposals</div>';
    });
}

// Render proposals table
function renderProposalsTable(proposals, currentStatus) {
    const proposalsManagement = document.getElementById('proposals-management');
    
    if (!proposals || proposals.length === 0) {
        proposalsManagement.innerHTML = '<p>No proposals found</p>';
        return;
    }
    
    let html = `
        <table class="admin-table">
            <thead>
                <tr>
                    <th>Date</th>
                    <th>Article</th>
                    <th>Proposed By</th>
                    <th>Summary</th>
                    <th>Status</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
    `;
    
    proposals.forEach(proposal => {
        // Format date
        const proposedAt = proposal.proposedAt ? new Date(proposal.proposedAt) : new Date();
        const formattedDate = proposedAt.toLocaleDateString();
        
        // Get status badge class
        let statusBadgeClass = '';
        if (proposal.status === 'pending') {
            statusBadgeClass = 'status-pending';
        } else if (proposal.status === 'approved') {
            statusBadgeClass = 'status-approved';
        } else if (proposal.status === 'rejected') {
            statusBadgeClass = 'status-rejected';
        }
        
        html += `
            <tr id="proposal-row-${proposal._id}">
                <td>${formattedDate}</td>
                <td><a href="/articles/${proposal.articleId}">${proposal.articleTitle || 'Unknown Article'}</a></td>
                <td>${proposal.proposerUsername || 'Unknown'}</td>
                <td>${proposal.summary || ''}</td>
                <td><span class="status-badge ${statusBadgeClass}">${proposal.status}</span></td>
                <td class="table-actions">
                    <a href="/articles/${proposal.articleId}/proposals/${proposal._id}" class="view-btn">View</a>
        `;
        
        // Add approve/reject buttons if pending
        if (proposal.status === 'pending') {
            html += `
                    <button class="approve-btn" data-proposalid="${proposal._id}" data-articleid="${proposal.articleId}">Approve</button>
                    <button class="reject-btn" data-proposalid="${proposal._id}" data-articleid="${proposal.articleId}">Reject</button>
            `;
        }
        
        html += `
                </td>
            </tr>
        `;
    });
    
    html += `
            </tbody>
        </table>
    `;
    
    proposalsManagement.innerHTML = html;
    
    // Setup approve/reject buttons
    const approveButtons = document.querySelectorAll('.approve-btn');
    approveButtons.forEach(button => {
        button.addEventListener('click', function() {
            const proposalId = this.getAttribute('data-proposalid');
            const articleId = this.getAttribute('data-articleid');
            
            handleProposalAction(proposalId, articleId, 'approve');
        });
    });
    
    const rejectButtons = document.querySelectorAll('.reject-btn');
    rejectButtons.forEach(button => {
        button.addEventListener('click', function() {
            const proposalId = this.getAttribute('data-proposalid');
            const articleId = this.getAttribute('data-articleid');
            
            handleProposalAction(proposalId, articleId, 'reject');
        });
    });
}

// Handle proposal action
function handleProposalAction(proposalId, articleId, action) {
    const comment = prompt(`Please provide a comment for ${action}ing this proposal:`);
    
    if (comment === null) {
        // User cancelled
        return;
    }
    
    const token = localStorage.getItem('token');
    if (!token) return;
    
    fetch(`/api/articles/${articleId}/proposals/${proposalId}?status=${action}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
            comment: comment
        })
    })
    .then(response => {
        if (!response.ok) {
            if (response.status === 401) {
                localStorage.removeItem('token');
                window.location.href = '/';
                throw new Error('Unauthorized');
            }
            return response.json().then(data => {
                throw new Error(data.detail || `Failed to ${action} proposal`);
            });
        }
        return response.json();
    })
    .then(data => {
        // Show success alert
        alert(`Proposal ${action}ed successfully`);
        
        // Update proposal row status or remove if filtering
        const proposalRow = document.getElementById(`proposal-row-${proposalId}`);
        if (proposalRow) {
            const statusFilter = document.getElementById('proposal-status-filter');
            const currentFilter = statusFilter ? statusFilter.value : '';
            
            if (currentFilter && currentFilter !== 'all' && currentFilter !== action) {
                // Remove row if filtering
                proposalRow.remove();
            } else {
                // Update status
                const statusCell = proposalRow.querySelector('td:nth-child(5)');
                const actionsCell = proposalRow.querySelector('td:nth-child(6)');
                
                if (statusCell) {
                    let statusBadgeClass = action === 'approve' ? 'status-approved' : 'status-rejected';
                    statusCell.innerHTML = `<span class="status-badge ${statusBadgeClass}">${action}d</span>`;
                }
                
                if (actionsCell) {
                    actionsCell.innerHTML = `<a href="/articles/${articleId}/proposals/${proposalId}" class="view-btn">View</a>`;
                }
            }
        }
    })
    .catch(error => {
        console.error(`Error ${action}ing proposal:`, error);
        alert(error.message || `Failed to ${action} proposal`);
    });
}

// Setup system tools
function setupSystemTools() {
    const clearCacheBtn = document.getElementById('clear-cache-btn');
    
    if (clearCacheBtn) {
        clearCacheBtn.addEventListener('click', function() {
            clearCache();
        });
    }
}

// Clear cache
function clearCache() {
    const token = localStorage.getItem('token');
    if (!token) return;
    
    // Show loading state
    const clearCacheBtn = document.getElementById('clear-cache-btn');
    const originalText = clearCacheBtn.textContent;
    clearCacheBtn.disabled = true;
    clearCacheBtn.textContent = 'Clearing...';
    
    fetch('/api/admin/cache/clear', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`
        }
    })
    .then(response => {
        if (!response.ok) {
            if (response.status === 401) {
                localStorage.removeItem('token');
                window.location.href = '/';
                throw new Error('Unauthorized');
            }
            return response.json().then(data => {
                throw new Error(data.detail || 'Failed to clear cache');
            });
        }
        return response.json();
    })
    .then(data => {
        // Show success alert
        alert(data.message || 'Cache cleared successfully');
        
        // Refresh dashboard stats
        loadDashboardStats(true);
    })
    .catch(error => {
        console.error('Error clearing cache:', error);
        alert(error.message || 'Failed to clear cache');
    })
    .finally(() => {
        // Reset button state
        clearCacheBtn.disabled = false;
        clearCacheBtn.textContent = originalText;
    });
}
