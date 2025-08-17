# Crypto Admin Setup Instructions

## Files Created:
- pages/crypto_admin.py - Main crypto admin routes
- templates/crypto_admin_dashboard.html - Main dashboard template
- templates/crypto_contributions.html - Contributions page
- templates/crypto_rewards.html - Rewards page
- templates/crypto_wallets.html - Wallets page

## Manual Steps Required:

### 1. Update main.py
Add these lines to your main.py:

```python
# Add with other imports
from pages import crypto_admin

# Add after other routers
app.include_router(crypto_admin.router, tags=["Crypto Admin"])
```

### 2. Update admin_dashboard.html
Add this link to your admin navigation:

```html
<a href="/admin/crypto" class="admin-link">
    <span>🪙 Crypto Management</span>
</a>
```

### 3. Environment Variables
Add to your .env file:

```
SOLANA_RPC_URL=https://api.devnet.solana.com
SOLANA_PRIVATE_KEY=your_private_key_here
TOKEN_MINT_ADDRESS=your_token_mint_address
WEEKLY_TOKEN_POOL=10000
MIN_TOKENS_PER_USER=1
```

### 4. Install Dependencies
```bash
pip install solana>=0.36.7 solders>=0.23.1
```

### 5. Restart Application
```bash
uvicorn main:app --reload
```

## Access Points:
- Main Dashboard: http://localhost:8000/admin/crypto
- Contributions: http://localhost:8000/admin/crypto/contributions
- Rewards: http://localhost:8000/admin/crypto/rewards
- Wallets: http://localhost:8000/admin/crypto/wallets
