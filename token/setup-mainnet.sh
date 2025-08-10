#!/bin/bash

# ============================================
# Kontrib Token - Mainnet Production Deployment
# ============================================
# CAUTION: This script deploys to MAINNET with REAL MONEY
# Ensure you have thoroughly tested on devnet first!

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/kontrib-mainnet-config.json"
ENV_FILE="$SCRIPT_DIR/.env.mainnet"
BACKUP_DIR="$SCRIPT_DIR/backups/$(date +%Y%m%d_%H%M%S)"

# Token Configuration
TOKEN_NAME="Kontrib"
TOKEN_SYMBOL="KONTRIB"
TOKEN_DECIMALS=9
INITIAL_SUPPLY=100000000

# Liquidity Configuration (Raydium)
LIQUIDITY_TOKENS=50000000  # 50M tokens (50% of supply)
LIQUIDITY_SOL=100          # 100 SOL initial liquidity
FEE_TIER="0.25"           # 0.25% trading fee

# Functions
print_header() {
    echo -e "${MAGENTA}========================================${NC}"
    echo -e "${MAGENTA}$1${NC}"
    echo -e "${MAGENTA}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

confirm_action() {
    echo -e "${YELLOW}$1${NC}"
    read -p "Type 'YES' to confirm: " confirmation
    if [ "$confirmation" != "YES" ]; then
        print_error "Action cancelled"
        exit 1
    fi
}

# Pre-flight checks
print_header "MAINNET DEPLOYMENT - PRODUCTION"
print_warning "This script will deploy to Solana MAINNET"
print_warning "This involves REAL SOL and creates a PERMANENT token"
echo ""
confirm_action "Are you sure you want to proceed with MAINNET deployment?"

# Check prerequisites
print_header "Checking Prerequisites"

command -v solana >/dev/null 2>&1 || { print_error "solana CLI not installed"; exit 1; }
command -v spl-token >/dev/null 2>&1 || { print_error "spl-token CLI not installed"; exit 1; }
command -v jq >/dev/null 2>&1 || { print_error "jq not installed"; exit 1; }

print_success "All prerequisites installed"

# Check devnet deployment
print_header "Checking Devnet Deployment"

DEVNET_CONFIG="$SCRIPT_DIR/kontrib-devnet-config.json"
if [ ! -f "$DEVNET_CONFIG" ]; then
    print_warning "No devnet deployment found"
    confirm_action "Deploy to mainnet without devnet testing?"
else
    print_success "Devnet deployment found"
    DEVNET_MINT=$(jq -r '.token_mint' "$DEVNET_CONFIG")
    print_info "Devnet token: $DEVNET_MINT"
fi

# Backup existing configurations
print_header "Creating Backups"

mkdir -p "$BACKUP_DIR"
if [ -f "$CONFIG_FILE" ]; then
    cp "$CONFIG_FILE" "$BACKUP_DIR/"
    print_success "Backed up existing mainnet config"
fi
if [ -f "$ENV_FILE" ]; then
    cp "$ENV_FILE" "$BACKUP_DIR/"
    print_success "Backed up existing environment file"
fi

# Setup Solana for mainnet
print_header "Configuring Solana for Mainnet"

print_info "Current configuration:"
solana config get

confirm_action "Switch to mainnet-beta?"
solana config set --url https://api.mainnet-beta.solana.com
print_success "Connected to Solana mainnet"

# Wallet setup
print_header "Wallet Configuration"

echo "Select wallet option:"
echo "1) Use existing wallet keypair"
echo "2) Create new wallet (NOT RECOMMENDED for production)"
read -p "Enter choice (1 or 2): " wallet_choice

if [ "$wallet_choice" == "1" ]; then
    read -p "Enter path to keypair file: " KEYPAIR_FILE
    if [ ! -f "$KEYPAIR_FILE" ]; then
        print_error "Keypair file not found: $KEYPAIR_FILE"
        exit 1
    fi
    solana config set --keypair "$KEYPAIR_FILE"
else
    print_warning "Creating new wallet for MAINNET"
    confirm_action "Are you SURE you want to create a new wallet?"
    KEYPAIR_FILE="$SCRIPT_DIR/kontrib-mainnet-authority.json"
    solana-keygen new --no-bip39-passphrase -o "$KEYPAIR_FILE"
    solana config set --keypair "$KEYPAIR_FILE"
    print_warning "SAVE THIS KEYPAIR SECURELY: $KEYPAIR_FILE"
fi

WALLET_ADDRESS=$(solana address)
print_success "Wallet address: $WALLET_ADDRESS"

# Check wallet balance
print_header "Checking Wallet Balance"

BALANCE=$(solana balance | awk '{print $1}')
print_info "Current balance: $BALANCE SOL"

MIN_BALANCE=2  # Minimum SOL needed for deployment
if (( $(echo "$BALANCE < $MIN_BALANCE" | bc -l) )); then
    print_error "Insufficient balance. Need at least $MIN_BALANCE SOL"
    print_info "Current balance: $BALANCE SOL"
    print_info "Please fund your wallet: $WALLET_ADDRESS"
    exit 1
fi

# Final confirmation
print_header "Deployment Summary"

echo "Network: MAINNET-BETA"
echo "Token Name: $TOKEN_NAME"
echo "Token Symbol: $TOKEN_SYMBOL"
echo "Decimals: $TOKEN_DECIMALS"
echo "Initial Supply: $INITIAL_SUPPLY"
echo "Authority Wallet: $WALLET_ADDRESS"
echo "Wallet Balance: $BALANCE SOL"
echo ""
echo "Liquidity Pool Configuration:"
echo "  Tokens for LP: $LIQUIDITY_TOKENS $TOKEN_SYMBOL"
echo "  SOL for LP: $LIQUIDITY_SOL SOL"
echo "  Fee Tier: $FEE_TIER%"
echo ""

print_warning "THIS IS YOUR LAST CHANCE TO CANCEL"
confirm_action "Deploy KONTRIB token to MAINNET?"

# Create Token
print_header "Creating KONTRIB Token on Mainnet"

print_info "Creating token with $TOKEN_DECIMALS decimals..."
CREATE_OUTPUT=$(spl-token create-token --decimals $TOKEN_DECIMALS 2>&1)
TOKEN_MINT=$(echo "$CREATE_OUTPUT" | grep "Creating token" | awk '{print $3}')

if [ -z "$TOKEN_MINT" ]; then
    print_error "Failed to create token"
    echo "$CREATE_OUTPUT"
    exit 1
fi

print_success "Token created: $TOKEN_MINT"

# Create token account
print_info "Creating token account..."
TOKEN_ACCOUNT=$(spl-token create-account "$TOKEN_MINT" | grep "Creating account" | awk '{print $3}')
print_success "Token account created: $TOKEN_ACCOUNT"

# Mint initial supply
print_header "Minting Initial Supply"

print_info "Minting $INITIAL_SUPPLY $TOKEN_SYMBOL tokens..."
spl-token mint "$TOKEN_MINT" $INITIAL_SUPPLY > /dev/null
print_success "Minted $INITIAL_SUPPLY tokens"

# Verify balance
TOKEN_BALANCE=$(spl-token balance "$TOKEN_MINT" | awk '{print $1}')
print_success "Token balance: $TOKEN_BALANCE $TOKEN_SYMBOL"

# Disable further minting (optional but recommended)
print_header "Securing Token"

confirm_action "Disable further minting? (Recommended for fixed supply)"
spl-token authorize "$TOKEN_MINT" mint --disable > /dev/null
print_success "Minting disabled - supply is now fixed at $INITIAL_SUPPLY"

# Save configuration
print_header "Saving Configuration"

cat > "$CONFIG_FILE" << EOF
{
  "network": "mainnet-beta",
  "token_name": "$TOKEN_NAME",
  "token_symbol": "$TOKEN_SYMBOL",
  "token_mint": "$TOKEN_MINT",
  "token_account": "$TOKEN_ACCOUNT",
  "decimals": $TOKEN_DECIMALS,
  "initial_supply": $INITIAL_SUPPLY,
  "wallet_address": "$WALLET_ADDRESS",
  "keypair_path": "$KEYPAIR_FILE",
  "minting_disabled": true,
  "created_at": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "explorer_url": "https://explorer.solana.com/address/$TOKEN_MINT",
  "liquidity": {
    "tokens_allocated": $LIQUIDITY_TOKENS,
    "sol_allocated": $LIQUIDITY_SOL,
    "fee_tier": "$FEE_TIER"
  }
}
EOF

print_success "Configuration saved to: $CONFIG_FILE"

# Generate .env file
cat > "$ENV_FILE" << EOF
# Kontrib Token - Mainnet Configuration
# PRODUCTION - HANDLE WITH CARE
SOLANA_NETWORK=mainnet-beta
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com
TOKEN_MINT_ADDRESS=$TOKEN_MINT
TOKEN_ACCOUNT=$TOKEN_ACCOUNT
WALLET_ADDRESS=$WALLET_ADDRESS
TOKEN_DECIMALS=$TOKEN_DECIMALS
INITIAL_SUPPLY=$INITIAL_SUPPLY

# For backend integration - KEEP SECURE
SOLANA_PRIVATE_KEY=$(cat "$KEYPAIR_FILE" | jq -c .)
WEEKLY_TOKEN_POOL=10000
MIN_TOKENS_PER_USER=1

# Liquidity Pool Configuration
LP_TOKEN_AMOUNT=$LIQUIDITY_TOKENS
LP_SOL_AMOUNT=$LIQUIDITY_SOL
LP_FEE_TIER=$FEE_TIER
EOF

chmod 600 "$ENV_FILE"  # Restrict permissions
print_success "Environment variables saved to: $ENV_FILE"

# Liquidity Pool Instructions
print_header "Liquidity Pool Setup Instructions"

echo -e "${YELLOW}IMPORTANT: Manual steps required for liquidity pool${NC}"
echo ""
echo "1. Go to Raydium: https://raydium.io/liquidity/create-pool/"
echo ""
echo "2. Connect your wallet (must be: $WALLET_ADDRESS)"
echo ""
echo "3. Create pool with these parameters:"
echo "   - Base Token: $TOKEN_MINT"
echo "   - Quote Token: So11111111111111111111111111111111111111112 (SOL)"
echo "   - Base Amount: $LIQUIDITY_TOKENS $TOKEN_SYMBOL"
echo "   - Quote Amount: $LIQUIDITY_SOL SOL"
echo "   - Fee Tier: $FEE_TIER%"
echo ""
echo "4. After pool creation, save the pool address"
echo ""
echo "5. Update $CONFIG_FILE with pool address"
echo ""

# Token Information
print_header "Token Successfully Deployed!"

echo -e "${GREEN}✨ KONTRIB token is now LIVE on Solana Mainnet! ✨${NC}"
echo ""
echo "Token Details:"
echo "  Name: $TOKEN_NAME"
echo "  Symbol: $TOKEN_SYMBOL"
echo "  Mint Address: $TOKEN_MINT"
echo "  Decimals: $TOKEN_DECIMALS"
echo "  Total Supply: $INITIAL_SUPPLY (FIXED)"
echo ""
echo "View on Explorer:"
echo "  https://explorer.solana.com/address/$TOKEN_MINT"
echo ""
echo "View on Solscan:"
echo "  https://solscan.io/token/$TOKEN_MINT"
echo ""
echo "Configuration Files:"
echo "  Config: $CONFIG_FILE"
echo "  Environment: $ENV_FILE (KEEP SECURE)"
echo "  Backup: $BACKUP_DIR"
echo ""

# Security reminders
print_header "🔒 SECURITY REMINDERS"

echo -e "${RED}CRITICAL SECURITY NOTES:${NC}"
echo "1. BACKUP your keypair file: $KEYPAIR_FILE"
echo "2. NEVER share your private key"
echo "3. Store configuration files securely"
echo "4. Monitor your token on block explorers"
echo "5. Set up monitoring alerts for unusual activity"
echo ""

# Next steps
print_header "Next Steps"

echo "1. ✅ Create liquidity pool on Raydium (see instructions above)"
echo "2. ✅ Verify token on Solscan and other explorers"
echo "3. ✅ Update your website with token information"
echo "4. ✅ Configure backend with mainnet settings"
echo "5. ✅ Test token transfers and integrations"
echo "6. ✅ Announce token launch to community"
echo "7. ✅ Monitor liquidity and trading activity"
echo ""

print_success "Mainnet deployment completed successfully!"
print_warning "Remember to create the liquidity pool manually on Raydium"