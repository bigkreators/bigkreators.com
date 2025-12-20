// File: static/kontrib-integration.js
// K̡̓ONTRIB Token Integration for Kryptopedia

(function() {
    'use strict';
    
    // Configuration from global scope
    const config = window.kontribConfig || {};
    
    // K̡̓ONTRIB Integration Class
    class KontribIntegration {
        constructor() {
            this.userBalance = config.userBalance || 0;
            this.isLoggedIn = config.isLoggedIn || false;
            this.tokenSymbol = config.tokenSymbol || 'K̡̓ontrib';
            
            this.init();
        }
        
        init() {
            this.setupEditRewardPreview();
            this.setupSaveButtonEnhancement();
            this.setupTokenNotifications();
            this.setupBalanceUpdates();
            this.setupEarningTracking();
            
            console.log('K̡̓ONTRIB integration initialized');
        }
        
        // Show potential token rewards while editing
        setupEditRewardPreview() {
            const editForm = document.querySelector('form[action*="/edit"]');
            const textarea = document.querySelector('textarea[name="content"]');
            
            if (editForm && textarea && this.isLoggedIn) {
                this.createRewardPreview(editForm, textarea);
            }
        }
        
        createRewardPreview(form, textarea) {
            // Create reward preview container
            const previewContainer = document.createElement('div');
            previewContainer.className = 'kontrib-reward-preview';
            previewContainer.innerHTML = `
                <div style="background: #ffe6e6; border: 1px solid #fcc; padding: 12px; margin: 8px 0; border-radius: 4px;">
                    <strong>💰 Potential K̡̓ontrib Earnings:</strong>
                    <span id="kontrib-earning-estimate">Calculating...</span>
                </div>
            `;
            
            // Insert before submit button
            const submitButton = form.querySelector('input[type="submit"], button[type="submit"]');
            if (submitButton) {
                submitButton.parentNode.insertBefore(previewContainer, submitButton);
            }
            
            // Update estimate on content change
            let timeout;
            textarea.addEventListener('input', () => {
                clearTimeout(timeout);
                timeout = setTimeout(() => {
                    this.updateEarningEstimate(textarea.value);
                }, 500);
            });
            
            // Initial calculation
            this.updateEarningEstimate(textarea.value);
        }
        
        updateEarningEstimate(content) {
            const estimateElement = document.getElementById('kontrib-earning-estimate');
            if (!estimateElement) return;
            
            const wordCount = content.trim().split(/\s+/).filter(word => word.length > 0).length;
            const isNewArticle = window.location.pathname.includes('/create') || 
                               window.location.pathname.includes('/edit/') && 
                               content.trim().length < 50; // Assume new if very short
            
            let baseReward = isNewArticle ? 50 : 10;
            let lengthBonus = Math.min(Math.floor(wordCount / 25), 50);
            let qualityBonus = this.estimateQualityBonus(content);
            
            let totalEstimate = baseReward + lengthBonus + qualityBonus;
            
            estimateElement.innerHTML = `
                <span style="font-size: 16px; color: #d33; font-weight: bold;">
                    ~${totalEstimate} ${this.tokenSymbol}
                </span>
                <div style="font-size: 12px; margin-top: 4px; color: #666;">
                    Base: ${baseReward} + Length: ${lengthBonus} + Quality: ${qualityBonus}
                </div>
            `;
        }
        
        estimateQualityBonus(content) {
            let bonus = 0;
            
            // Check for references/links
            if (content.match(/\[.*?\]|\bhttps?:\/\/\S+/g)) {
                bonus += 15;
            }
            
            // Check for structured content (headers, lists)
            if (content.match(/^#+\s/gm) || content.match(/^\s*[\*\-\+]\s/gm)) {
                bonus += 10;
            }
            
            // Check for categories or tags
            if (content.match(/\[\[Category:.*?\]\]|\#\w+/g)) {
                bonus += 10;
            }
            
            return Math.min(bonus, 35);
        }
        
        // Enhance save button to show token reward
        setupSaveButtonEnhancement() {
            const saveButtons = document.querySelectorAll('input[type="submit"], button[type="submit"]');
            
            saveButtons.forEach(button => {
                if (button.value && (button.value.includes('Save') || button.value.includes('Create'))) {
                    const originalText = button.value;
                    
                    // Update button text periodically with estimated reward
                    setInterval(() => {
                        const estimate = this.getCurrentEstimate();
                        if (estimate > 0 && this.isLoggedIn) {
                            button.value = `${originalText} (+${estimate} ${this.tokenSymbol})`;
                            button.style.background = '#14866d';
                            button.style.color = 'white';
                            button.style.fontWeight = 'bold';
                        }
                    }, 1000);
                }
            });
        }
        
        getCurrentEstimate() {
            const estimateElement = document.getElementById('kontrib-earning-estimate');
            if (estimateElement) {
                const match = estimateElement.textContent.match(/~(\d+)/);
                return match ? parseInt(match[1]) : 0;
            }
            return 0;
        }
        
        // Show notifications for token earnings
        setupTokenNotifications() {
            // Listen for form submissions to show earning notifications
            document.addEventListener('submit', (e) => {
                const form = e.target;
                if (form.action && (form.action.includes('/edit') || form.action.includes('/create'))) {
                    this.showEarningNotification();
                }
            });
        }
        
        showEarningNotification(amount) {
            if (!this.isLoggedIn) return;
            
            const notification = document.createElement('div');
            notification.className = 'kontrib-notification';
            notification.innerHTML = `
                <strong>🎉 K̡̓ontrib Earned!</strong><br>
                You earned ${amount || 'tokens'} for your contribution!
            `;
            
            document.body.appendChild(notification);
            
            // Auto-remove after 5 seconds
            setTimeout(() => {
                notification.style.animation = 'slideOut 0.3s ease-in';
                setTimeout(() => {
                    if (notification.parentNode) {
                        notification.parentNode.removeChild(notification);
                    }
                }, 300);
            }, 5000);
        }
        
        // Update balance display in real-time
        setupBalanceUpdates() {
            const balanceElement = document.querySelector('.kontrib-balance');
            if (balanceElement && this.isLoggedIn) {
                // Periodically check for balance updates
                setInterval(() => {
                    this.fetchBalanceUpdate();
                }, 30000); // Check every 30 seconds
            }
        }
        
        async fetchBalanceUpdate() {
            try {
                const response = await fetch('/api/kontrib/balance', {
                    headers: {
                        'Authorization': `Bearer ${this.getAuthToken()}`
                    }
                });
                
                if (response.ok) {
                    const data = await response.json();
                    this.updateBalanceDisplay(data.balance);
                }
            } catch (error) {
                console.log('Could not fetch balance update:', error);
            }
        }
        
        updateBalanceDisplay(newBalance) {
            const balanceElement = document.querySelector('.kontrib-balance');
            if (balanceElement) {
                const oldBalance = this.userBalance;
                this.userBalance = newBalance;
                
                balanceElement.textContent = `${newBalance.toFixed(2)} ${this.tokenSymbol}`;
                
                // Animate if balance increased
                if (newBalance > oldBalance) {
                    balanceElement.style.animation = 'flash 0.5s ease-in-out';
                    setTimeout(() => {
                        balanceElement.style.animation = '';
                    }, 500);
                }
            }
        }
        
        getAuthToken() {
            // Get JWT token from localStorage or cookie
            return localStorage.getItem('auth_token') || 
                   document.cookie.split('; ').find(row => row.startsWith('auth_token='))?.split('=')[1];
        }
        
        // Track user interactions for analytics
        setupEarningTracking() {
            // Track edit sessions
            let editStartTime = null;
            
            document.addEventListener('focus', (e) => {
                if (e.target.tagName === 'TEXTAREA' && e.target.name === 'content') {
                    editStartTime = Date.now();
                }
            });
            
            document.addEventListener('blur', (e) => {
                if (e.target.tagName === 'TEXTAREA' && e.target.name === 'content' && editStartTime) {
                    const editDuration = Date.now() - editStartTime;
                    this.trackEditSession(editDuration, e.target.value.length);
                    editStartTime = null;
                }
            });
        }
        
        trackEditSession(duration, contentLength) {
            // Could send analytics data to backend
            console.log(`Edit session: ${duration}ms, content length: ${contentLength}`);
        }
        
        // Public methods for external use
        showSuccessNotification(message, amount) {
            this.showEarningNotification(amount);
        }
        
        updateBalance(newBalance) {
            this.updateBalanceDisplay(newBalance);
        }
    }
    
    // CSS animations
    const style = document.createElement('style');
    style.textContent = `
        @keyframes flash {
            0%, 100% { background: inherit; }
            50% { background: #d5fdf4; }
        }
        
        @keyframes slideOut {
            from { transform: translateX(0); opacity: 1; }
            to { transform: translateX(100%); opacity: 0; }
        }
        
        .kontrib-reward-preview {
            animation: fadeIn 0.3s ease-out;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(-10px); }
            to { opacity: 1; transform: translateY(0); }
        }
    `;
    document.head.appendChild(style);
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            window.KontribIntegration = new KontribIntegration();
        });
    } else {
        window.KontribIntegration = new KontribIntegration();
    }
    
    // Global utility functions
    window.kontrib = {
        showNotification: (message, amount) => {
            if (window.KontribIntegration) {
                window.KontribIntegration.showSuccessNotification(message, amount);
            }
        },
        
        updateBalance: (newBalance) => {
            if (window.KontribIntegration) {
                window.KontribIntegration.updateBalance(newBalance);
            }
        }
    };
    
})();
