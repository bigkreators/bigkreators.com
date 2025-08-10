# BigKreators Contribution Token (KONTRIB) - Complete Documentation

## Table of Contents

1. [Overview](#overview)
2. [Token Economics](#token-economics)
3. [Architecture](#architecture)
4. [API Reference](#api-reference)
5. [Smart Contracts](#smart-contracts)
6. [Contribution System](#contribution-system)
7. [Staking & Rewards](#staking--rewards)
8. [Governance](#governance)
9. [Installation & Setup](#installation--setup)
10. [Deployment Guide](#deployment-guide)
11. [Troubleshooting](#troubleshooting)
12. [FAQ](#faq)
13. [Roadmap](#roadmap)

---

## Overview

### What is KONTRIB?

The **BigKreators Contribution Token (KONTRIB)** is a Solana-based SPL token that incentivizes and rewards high-quality contributions to the BigKreators wiki platform. KONTRIB creates a tokenized economy where contributors earn rewards for creating, editing, and reviewing wiki content.

**Visual Identity:** The token uses creative Unicode styling (K̡̓ontrib, ᶄ̓ontrib) for branding while maintaining the professional ASCII symbol "KONTRIB" for technical compatibility.

### Key Features

- 🪙 **SPL Token on Solana** - Fast, low-cost transactions
- 📊 **Contribution Tracking** - Automated point calculation
- 🏆 **Weekly Rewards** - Regular token distribution
- 🔒 **Staking System** - Lock tokens for additional rewards
- 🗳️ **Governance** - Token-weighted voting on platform decisions
- 📈 **Reputation System** - User reputation affects reward multipliers

### Token Specifications

| Property | Value |
|----------|-------|
| **Name** | BigKreators Contribution Token |
| **Symbol** | KONTRIB |
| **Decimals** | 9 |
| **Total Supply** | 100,000,000 KONTRIB |
| **Blockchain** | Solana |
| **Token Standard** | SPL Token |
| **Network** | Devnet (MVP) → Mainnet |

### Branding Strategy

**Official Token Identity:**
- **Symbol**: `KONTRIB` (SPL compliant, works everywhere)
- **Name**: `BigKreators Contribution Token`
- **Purpose**: Professional DeFi integration

**Visual Branding Identity:**
- **Stylized Logos**: K̡̓ontrib and ᶄ̓ontrib (Unicode styling)
- **Community Name**: ᶄ̓ontrib Community
- **Social Media**: #K̡̓ontrib #ᶄ̓ontrib hashtags
- **Website Headers**: K̡̓ontrib Token branding

**Why This Dual Strategy:**
- ✅ **Maximum Compatibility**: ASCII symbol works in all wallets, exchanges, DeFi
- ✅ **Unique Identity**: Unicode variants create distinctive visual brand
- ✅ **Professional Standards**: Follows established DeFi token conventions
- ✅ **Creative Freedom**: Unicode styling for marketing and community

---

## Token Economics

### Distribution Model

| Allocation | Percentage | Amount | Purpose |
|------------|------------|--------|---------|
| **Community Rewards** | 60% | 60M KONTRIB | Weekly contributor rewards |
| **Development Fund** | 15% | 15M KONTRIB | Platform development |
| **Team Allocation** | 10% | 10M KONTRIB | Core team incentives |
| **Liquidity Pool** | 10% | 10M KONTRIB | DEX liquidity |
| **Treasury** | 5% | 5M KONTRIB | Governance and operations |

### Fee Structure

- **Transfer Fee**: 2% on all token transfers
  - **20%** → Token burn (deflationary)
  - **50%** → Community treasury
  - **30%** → Staking rewards pool

### Weekly Reward Distribution

- **Pool Size**: 10,000 KONTRIB per week (adjustable via governance)
- **Distribution Method**: Proportional to points earned
- **Minimum Reward**: 1 KONTRIB per qualifying user
- **Distribution Day**: Every Monday at 00:00 UTC

---

## Architecture

### System Components

```mermaid
graph TB
    A[BigKreators Wiki] --> B[FastAPI Backend]
    B --> C[MongoDB Database]
    B --> D[Solana Service]
    D --> E[KONTRIB Token Contract]
    D --> F[Staking Contract]
    B --> G[Contribution Tracker]
    G --> H[Points Engine]
    H --> I[Weekly Distributor]
    I --> E
    
    J[Frontend] --> B
    K[Wallet Integration] --> D
    L[React Components] --> K
```

### Technology Stack

#### Backend
- **Framework**: FastAPI (Python)
- **Database**: MongoDB with Motor (async)
- **Blockchain**: Solana RPC via Python client
- **Authentication**: JWT + Wallet signatures

#### Database Schema
The system extends your existing MongoDB collections and adds new ones:

**Extended Collections:**
- `users` - Added wallet_address, reputation_score, total_tokens_earned
- `articles` - Added demand_score, quality_score, contribution_count

**New Collections:**
- `contributions` - Track all user contributions and points
- `token_rewards` - Individual user reward records
- `weekly_distributions` - Weekly reward distribution events
- `staking_records` - Token staking activities
- `governance_proposals` - Governance voting and proposals
- `system_config` - Token system configuration

**Migration Strategy:**
- Non-destructive: All existing data preserved
- Backwards compatible: Existing features continue working
- Automated indices: Performance optimized for token queries

#### Frontend
- **Base**: Jinja2 templates (existing wiki)
- **Token Features**: React components
- **Wallet**: Solana wallet adapters
- **Styling**: Tailwind CSS

#### Blockchain
- **Network**: Solana
- **RPC**: QuickNode/Alchemy (production)
- **Token**: SPL Token standard
- **Tools**: Solana CLI, Anchor framework

---

## API Reference

### Base URL
```
Production: https://bigkreators.com/api/token
Development: http://localhost:8000/api/token
```

### Authentication
Most endpoints require JWT authentication:
```http
Authorization: Bearer <your_jwt_token>
```

### Core Endpoints

#### System Status
```http
GET /status
```

**Response:**
```json
{
  "status": "active",
  "network": "devnet",
  "authority_wallet": "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgHDF",
  "authority_sol_balance": 1.5,
  "token_mint": "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
  "rpc_url": "https://api.devnet.solana.com"
}
```

#### Wallet Information
```http
GET /wallet/{wallet_address}
```

**Response:**
```json
{
  "address": "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgHDF",
  "sol_balance": 1.5,
  "token_balance": 1250.0,
  "account_exists": true
}
```

#### Track Contribution
```http
POST /contributions
Content-Type: application/json
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "article_id": "507f1f77bcf86cd799439011",
  "type": "creation",
  "description": "Created comprehensive guide on DeFi protocols"
}
```

**Response:**
```json
{
  "success": true,
  "contribution_id": "507f1f77bcf86cd799439012",
  "points_earned": 120,
  "message": "Contribution tracked! Earned 120 points."
}
```

#### User Rewards
```http
GET /rewards/user/{user_id}?skip=0&limit=10
```

**Response:**
```json
{
  "user_id": "507f1f77bcf86cd799439013",
  "total_contributions": 15,
  "total_points": 1500,
  "wallet_address": "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgHDF",
  "contributions": [...],
  "estimated_weekly_tokens": 150.0
}
```

#### Transaction History
```http
GET /transactions/{wallet_address}?limit=10
```

**Response:**
```json
{
  "wallet_address": "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgHDF",
  "transactions": [
    {
      "signature": "3KqKCKXYrD8...",
      "slot": 12345678,
      "block_time": 1640995200,
      "success": true,
      "confirmation_status": "confirmed"
    }
  ],
  "count": 5
}
```

---

## Smart Contracts

### WCT Token Contract

**Program ID**: `9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM` (Devnet)

#### Key Functions

- `initialize_token()` - Initialize token with supply
- `transfer_with_fee()` - Transfer tokens with fee mechanism
- `burn_tokens()` - Burn tokens for deflation
- `distribute_rewards()` - Batch reward distribution

### Staking Contract

**Program ID**: `StakeR6KqKCKXYrD8ZTbNMqUxvQRAyrZzDsGYdLVL9z` (Devnet)

#### Staking Tiers

| Duration | APY | Multiplier | Lock Period |
|----------|-----|-----------|-------------|
| **30 days** | 5% | 1.1x | 30 days |
| **90 days** | 12% | 1.3x | 90 days |
| **180 days** | 25% | 1.6x | 180 days |
| **365 days** | 50% | 2.0x | 365 days |

#### Staking Functions

- `stake_tokens()` - Lock tokens for rewards
- `unstake_tokens()` - Unlock tokens after period
- `claim_rewards()` - Claim staking rewards
- `get_stake_info()` - Get staking details

---

## Contribution System

### Contribution Types & Base Points

| Type | Base Points | Description |
|------|-------------|-------------|
| **Creation** | 100 | Creating new wiki articles |
| **Major Edit** | 50 | Substantial content additions/improvements |
| **Minor Edit** | 20 | Small fixes, formatting, links |
| **Review** | 10 | Reviewing and approving edit proposals |

### Point Multipliers

#### Quality Multiplier (0.5x - 3.0x)
- **Excellent** (2.5x - 3.0x): Comprehensive, well-sourced, expertly written
- **Good** (1.5x - 2.4x): Solid content with good structure
- **Standard** (1.0x - 1.4x): Basic acceptable quality
- **Poor** (0.5x - 0.9x): Needs improvement

#### Reputation Multiplier (0.8x - 1.5x)
- **New User** (0.8x): < 5 contributions
- **Regular** (1.0x): 5-25 contributions
- **Experienced** (1.2x): 25-100 contributions
- **Expert** (1.5x): 100+ contributions

#### Demand Multiplier (1.0x - 2.5x)
Based on topic popularity and content gaps:
- **High Demand** (2.0x - 2.5x): Trending topics, requested content
- **Medium Demand** (1.3x - 1.9x): Popular topics
- **Standard** (1.0x - 1.2x): Regular content

### Calculation Formula

```
Total Points = Base Points × Quality Multiplier × Reputation Multiplier × Demand Multiplier
```

**Example:**
- Article creation (100 points)
- Excellent quality (2.5x)
- Expert user (1.5x)
- High demand topic (2.0x)
- **Total: 100 × 2.5 × 1.5 × 2.0 = 750 points**

---

## Staking & Rewards

### Weekly Reward Distribution

#### Process
1. **Monday 00:00 UTC**: Distribution process begins
2. **Calculate total points** earned across all users
3. **Determine point-to-token ratio**: `10,000 WCT ÷ Total Points`
4. **Distribute tokens** proportionally to wallets
5. **Update user records** with reward history

#### Eligibility
- Must have earned at least 10 points during the week
- Must have connected Solana wallet
- Account must be in good standing

#### Distribution Formula
```
User Tokens = (User Points ÷ Total Points) × Weekly Pool × Staking Multiplier
```

### Staking Benefits

#### Reward Multipliers
Staked tokens increase weekly reward multipliers:
- **1,000+ WCT staked**: 1.1x multiplier
- **5,000+ WCT staked**: 1.3x multiplier
- **10,000+ WCT staked**: 1.6x multiplier
- **25,000+ WCT staked**: 2.0x multiplier

#### Staking Rewards
Additional APY earned on staked tokens, paid weekly:
```
Weekly Staking Reward = (Staked Amount × APY) ÷ 52
```

---

## Governance

### Voting Power
- **1 KONTRIB = 1 Vote**
- **Staked tokens = 2x voting power**
- **Minimum to propose**: 1,000 KONTRIB staked

### Proposal Types

#### Parameter Changes
- Weekly reward pool size
- Staking APY rates
- Point multipliers
- Fee structure

#### Platform Updates
- New features
- UI/UX changes
- Integration proposals

#### Treasury Management
- Fund allocation
- Partnership investments
- Development grants

### Voting Process
1. **Proposal Creation** (requires 1,000 WCT staked)
2. **Discussion Period** (3 days)
3. **Voting Period** (7 days)
4. **Execution** (if >50% approval + quorum)

---

## Installation & Setup

### Prerequisites

#### System Requirements
- **Node.js**: 16+ (for CLI tools)
- **Python**: 3.8+ (for backend)
- **MongoDB**: 4.4+ (database)
- **Solana CLI**: Latest version

#### Install Solana CLI
```bash
sh -c "$(curl -sSfL https://release.solana.com/v1.16.0/install)"
export PATH="$HOME/.local/share/solana/install/active_release/bin:$PATH"
```

#### Install SPL Token CLI
```bash
cargo install spl-token-cli
```

### Backend Setup

#### 1. Clone Repository
```bash
git clone https://github.com/bigkreators/bigkreators.com.git
cd bigkreators.com
```

#### 2. Install Dependencies
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

#### 3. Run Token Integration Setup
```bash
chmod +x modern_solana_setup.sh
./modern_solana_setup.sh
```

#### 4. Run Database Migration
```bash
# Migrate your existing MongoDB database for token integration
python migrate_database.py

# This will:
# ✅ Preserve all existing data
# ✅ Add token fields to users and articles
# ✅ Create new token-related collections
# ✅ Set up optimized indices
# ✅ Seed initial configuration data
```

#### 4. Run Database Migration
```bash
# Migrate your existing MongoDB database for token integration
python migrate_database.py
```

#### 5. Create KONTRIB Token
```bash
python create_kontrib_token.py
```

#### 5. Configure Environment
```bash
# Add generated variables to .env
cat .env.kontrib.generated >> .env

# Or manually add:
echo "SOLANA_RPC_URL=https://api.devnet.solana.com" >> .env
echo "SOLANA_PRIVATE_KEY=your_base58_private_key" >> .env
echo "TOKEN_MINT_ADDRESS=your_token_mint_address" >> .env
echo "TOKEN_SYMBOL=KONTRIB" >> .env
```

#### 6. Test Integration
```bash
python test_kontrib_integration.py
```

#### 7. Start Server
```bash
uvicorn main:app --reload
```

### Frontend Integration

#### 1. Add Wallet Connection
```javascript
// In your existing templates
<div id="wallet-component"></div>
<script src="/static/wallet-integration.js"></script>
```

#### 2. Test Token Features
```bash
# Check system status
curl http://localhost:8000/api/token/status

# Get wallet info
curl http://localhost:8000/api/token/wallet/YOUR_WALLET_ADDRESS
```

---

## Deployment Guide

### Production Deployment

#### Option 1: Render.com (Recommended)

1. **Prepare Repository**
```bash
git add .
git commit -m "Add token integration"
git push origin main
```

2. **Create Render Service**
- Connect GitHub repository
- Select "Web Service"
- Configure build settings:
  ```yaml
  Build Command: pip install -r requirements.txt
  Start Command: uvicorn main:app --host 0.0.0.0 --port $PORT
  ```

3. **Set Environment Variables**
```
MONGO_URI=mongodb+srv://user:pass@cluster.mongodb.net/bigkreators
JWT_SECRET=your-jwt-secret
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com
SOLANA_PRIVATE_KEY=your-mainnet-private-key
TOKEN_MINT_ADDRESS=your-mainnet-token-address
```

4. **Deploy**
- Click "Create Web Service"
- Wait for deployment
- Test endpoints

#### Option 2: Docker Deployment

1. **Build Image**
```bash
docker build -t bigkreators-token .
```

2. **Run Container**
```bash
docker run -d \
  -p 8000:8000 \
  -e MONGO_URI="your-mongo-uri" \
  -e SOLANA_RPC_URL="https://api.mainnet-beta.solana.com" \
  -e SOLANA_PRIVATE_KEY="your-private-key" \
  -e TOKEN_MINT_ADDRESS="your-token-address" \
  bigkreators-token
```

### Mainnet Migration

#### 1. Create Mainnet Token
```bash
# Configure for mainnet
solana config set --url mainnet-beta

# Create production token
python create_token_modern.py
```

#### 2. Update Configuration
```bash
# Update .env for production
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com
TOKEN_MINT_ADDRESS=your_mainnet_token_address
```

#### 3. Test Production Setup
```bash
python test_token_modern.py
```

---

## Troubleshooting

### Common Issues

#### 1. Dependency Conflicts
**Problem**: Solana library version conflicts
**Solution**:
```bash
pip uninstall solana solders
pip install solana==0.36.7 solders==0.23.1
```

#### 2. Insufficient SOL for Transactions
**Problem**: "Transaction failed: insufficient funds"
**Solutions**:
- **Devnet**: Request airdrop via API or faucet
- **Mainnet**: Fund wallet with SOL

#### 3. Token Account Not Found
**Problem**: "Token account does not exist"
**Solution**:
```bash
# Create associated token account
spl-token create-account YOUR_TOKEN_MINT_ADDRESS
```

#### 4. RPC Rate Limiting
**Problem**: "429 Too Many Requests"
**Solutions**:
- Use premium RPC provider (QuickNode, Alchemy)
- Implement request throttling
- Add retry logic

#### 5. MongoDB Connection Issues
**Problem**: "Connection timeout"
**Solutions**:
- Check MongoDB Atlas whitelist
- Verify connection string
- Test network connectivity

### Debugging Commands

#### Check Token Balance
```bash
spl-token balance YOUR_TOKEN_MINT_ADDRESS
```

#### Verify Transaction
```bash
solana confirm TRANSACTION_SIGNATURE
```

#### Test API Endpoints
```bash
# Health check
curl http://localhost:8000/health

# Token status
curl http://localhost:8000/api/token/status

# User rewards
curl -H "Authorization: Bearer YOUR_JWT" \
     http://localhost:8000/api/token/rewards/user/USER_ID
```

### Log Analysis

#### Backend Logs
```bash
# View FastAPI logs
tail -f logs/api.log

# Filter token-related logs
grep "token" logs/api.log
```

#### Solana Logs
```bash
# View Solana CLI logs
solana logs YOUR_PROGRAM_ID

# View transaction logs
solana transaction-history YOUR_WALLET_ADDRESS
```

---

## FAQ

### General Questions

**Q: What makes KONTRIB different from other tokens?**
A: KONTRIB is specifically designed for wiki contributions with automated point tracking, quality assessment, and reputation-based multipliers. It's not just a payment token - it's a comprehensive contribution incentive system.

**Q: Why is the symbol KONTRIB instead of the stylized versions?**
A: For technical compatibility. The official symbol "KONTRIB" works in all wallets, exchanges, and DeFi protocols. We use the stylized versions (K̡̓ontrib, ᶄ̓ontrib) for visual branding and community identity.

**Q: How are points calculated?**
A: Points use a multi-factor formula: Base Points × Quality × Reputation × Demand. This ensures high-quality content from experienced users on in-demand topics receives maximum rewards.

**Q: Can I trade KONTRIB tokens?**
A: Yes, KONTRIB is a standard SPL token that can be traded on Solana DEXs. However, there's a 2% transfer fee that supports the ecosystem through burns and treasury funding.

### Technical Questions

**Q: Why Solana instead of Ethereum?**
A: Solana offers fast transactions (~400ms) and low fees (~$0.001), making it practical for frequent micro-rewards. Ethereum's gas fees would make small contribution rewards uneconomical.

**Q: How do you prevent gaming the system?**
A: Multiple mechanisms: quality assessment, reputation requirements, contribution verification, and manual review for large rewards. The point system rewards quality over quantity.

**Q: What happens if I lose my wallet?**
A: Unfortunately, blockchain transactions are irreversible. Always backup your seed phrase securely. We recommend using hardware wallets for significant token amounts.

### Rewards & Staking

**Q: When are rewards distributed?**
A: Every Monday at 00:00 UTC. The system calculates the previous week's contributions and distributes tokens proportionally.

**Q: How do staking multipliers work?**
A: Staking tokens gives you higher multipliers on weekly rewards. For example, staking 10,000 KONTRIB gives you a 1.6x multiplier on all contribution rewards.

**Q: Can I unstake early?**
A: No, staking periods are locked. Early unstaking would undermine the incentive structure. Choose your staking period carefully.

### Governance

**Q: How do I participate in governance?**
A: Hold KONTRIB tokens and participate in proposals. You need 1,000 staked KONTRIB to create proposals. All token holders can vote, with staked tokens counting double.

**Q: What can governance change?**
A: Weekly reward pools, staking rates, point multipliers, platform features, and treasury allocation. Major changes require community consensus.

**Q: How is governance enforced?**
A: Smart contracts automatically execute approved proposals. Parameter changes are implemented immediately, while feature changes require development time.

---

## Roadmap

### Phase 1: MVP Launch (Months 1-2)
- ✅ Basic token creation and distribution
- ✅ Contribution tracking system
- ✅ Weekly reward distribution
- 🔄 Frontend wallet integration
- 🔄 Basic staking functionality

### Phase 2: Enhanced Features (Months 3-4)
- 🔄 Advanced quality assessment
- 🔄 Reputation system refinement
- 🔄 Governance implementation
- 🔄 Mobile wallet support
- 🔄 Performance optimization

### Phase 3: Ecosystem Growth (Months 5-6)
- 📋 DEX liquidity provision
- 📋 Cross-platform integration
- 📋 Advanced analytics dashboard
- 📋 Partnership programs
- 📋 Third-party integrations

### Phase 4: Scaling (Months 7-12)
- 📋 Mainnet deployment
- 📋 Multi-language support
- 📋 Advanced governance features
- 📋 Institutional partnerships
- 📋 Global expansion

### Future Considerations
- 📋 Cross-chain bridges
- 📋 NFT integration for achievements
- 📋 DAO structure implementation
- 📋 Machine learning quality assessment
- 📋 Decentralized moderation

---

## Resources

### Links
- **Explorer**: [Solana Explorer](https://explorer.solana.com/)
- **Wallet**: [Phantom](https://phantom.app/), [Solflare](https://solflare.com/)
- **DEX**: [Jupiter](https://jup.ag/), [Raydium](https://raydium.io/)
- **Documentation**: [Solana Docs](https://docs.solana.com/)

### Support
- **Technical Issues**: Create GitHub issue
- **General Questions**: Discord community
- **Partnership Inquiries**: partnerships@bigkreators.com
- **Security Reports**: security@bigkreators.com

### Community
- **Discord**: [BigKreators Community](https://discord.gg/bigkreators)
- **Twitter**: [@BigKreators](https://twitter.com/BigKreators)
- **Telegram**: [KONTRIB Token Group](https://t.me/kontribtoken)
- **GitHub**: [Project Repository](https://github.com/bigkreators/bigkreators.com)

### Brand Assets

#### Official Token Identity
- **Symbol**: KONTRIB
- **Name**: BigKreators Contribution Token
- **Logo**: Standard ASCII styling

#### Community Branding
- **Stylized**: K̡̓ontrib Token
- **Community**: ᶄ̓ontrib Community
- **Hashtags**: #KONTRIB #K̡̓ontrib #ᶄ̓ontrib #BigKreators
- **Visual Identity**: Unicode styling for graphics and social media

---

*Last Updated: December 2024*
*Version: 1.0.0*
*Token: KONTRIB (BigKreators Contribution Token)*
*Network: Solana Devnet (MVP)*