#!/bin/bash

# ============================================
# Kontrib Token - Devnet Setup & Testing Script
# ============================================
# This script sets up the Kontrib token on Solana devnet for testing
# Includes token creation, wallet setup, and liquidity pool preparation

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/kontrib-devnet-config.json"
ENV_FILE="$SCRIPT_DIR/.env.devnet"
KEYPAIR_FILE="$HOME/.config/solana/kontrib-devnet.json"

# Token Configuration
TOKEN_NAME="Kontrib"
TOKEN_SYMBOL="KONTRIB"
TOKEN_DECIMALS=9
INITIAL_SUPPLY=100000000
TEST_LIQUIDITY_TOKENS=10000000  # 10M tokens for test pool
TEST_LIQUIDITY_SOL=10           # 10 SOL for test pool

# Functions
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

check_command() {
    if ! command -v $1 &> /dev/null; then
        print_error "$1 is not installed. Please install it first."
        exit 1
    fi
}

# Check prerequisites
print_header "Checking Prerequisites"

check_command "solana"
check_command "spl-token"
check_command "jq"

print_success "All prerequisites installed"

# Setup Solana for devnet
print_header "Configuring Solana for Devnet"

solana config set --url https://api.devnet.solana.com
print_success "Connected to Solana devnet"

# Create or use existing keypair
if [ -f "$KEYPAIR_FILE" ]; then
    print_info "Using existing keypair: $KEYPAIR_FILE"
    solana config set --keypair "$KEYPAIR_FILE"
else
    print_info "Creating new keypair for devnet..."
    solana-keygen new --no-bip39-passphrase -o "$KEYPAIR_FILE"
    solana config set --keypair "$KEYPAIR_FILE"
    print_success "New keypair created: $KEYPAIR_FILE"
fi

WALLET_ADDRESS=$(solana address)
print_success "Wallet address: $WALLET_ADDRESS"

# Get wallet balance
print_header "Checking Wallet Balance"

BALANCE=$(solana balance | awk '{print $1}')
print_info "Current balance: $BALANCE SOL"

# Request airdrop if needed
if (( $(echo "$BALANCE < 2" | bc -l) )); then
    print_info "Balance low. Requesting airdrop..."
    
    MAX_RETRIES=3
    RETRY_COUNT=0
    
    while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
        if solana airdrop 2 "$WALLET_ADDRESS" --url https://api.devnet.solana.com 2>/dev/null; then
            print_success "Airdrop successful!"
            sleep 5  # Wait for confirmation
            break
        else
            RETRY_COUNT=$((RETRY_COUNT + 1))
            if [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
                print_info "Airdrop failed. Retrying ($RETRY_COUNT/$MAX_RETRIES)..."
                sleep 10
            else
                print_error "Airdrop failed after $MAX_RETRIES attempts"
                print_info "Please try: https://faucet.solana.com/"
                exit 1
            fi
        fi
    done
fi

# Create Token
print_header "Creating KONTRIB Token"

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

# Save configuration
print_header "Saving Configuration"

cat > "$CONFIG_FILE" << EOF
{
  "network": "devnet",
  "token_name": "$TOKEN_NAME",
  "token_symbol": "$TOKEN_SYMBOL",
  "token_mint": "$TOKEN_MINT",
  "token_account": "$TOKEN_ACCOUNT",
  "decimals": $TOKEN_DECIMALS,
  "initial_supply": $INITIAL_SUPPLY,
  "wallet_address": "$WALLET_ADDRESS",
  "keypair_path": "$KEYPAIR_FILE",
  "created_at": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "explorer_url": "https://explorer.solana.com/address/$TOKEN_MINT?cluster=devnet"
}
EOF

print_success "Configuration saved to: $CONFIG_FILE"

# Generate .env file
cat > "$ENV_FILE" << EOF
# Kontrib Token - Devnet Configuration
SOLANA_NETWORK=devnet
SOLANA_RPC_URL=https://api.devnet.solana.com
TOKEN_MINT_ADDRESS=$TOKEN_MINT
TOKEN_ACCOUNT=$TOKEN_ACCOUNT
WALLET_ADDRESS=$WALLET_ADDRESS
TOKEN_DECIMALS=$TOKEN_DECIMALS
INITIAL_SUPPLY=$INITIAL_SUPPLY

# For backend integration
SOLANA_PRIVATE_KEY=$(cat "$KEYPAIR_FILE" | jq -c .)
WEEKLY_TOKEN_POOL=10000
MIN_TOKENS_PER_USER=1
EOF

print_success "Environment variables saved to: $ENV_FILE"

# Test transactions
print_header "Testing Token Transactions"

# Create a test recipient wallet
print_info "Creating test recipient wallet..."
TEST_KEYPAIR="$SCRIPT_DIR/test-recipient.json"
solana-keygen new --no-bip39-passphrase -o "$TEST_KEYPAIR" --force > /dev/null 2>&1
TEST_WALLET=$(solana address -k "$TEST_KEYPAIR")
print_success "Test wallet created: $TEST_WALLET"

# Fund test wallet with SOL
print_info "Funding test wallet with SOL..."
solana transfer "$TEST_WALLET" 0.1 --allow-unfunded-recipient > /dev/null
print_success "Sent 0.1 SOL to test wallet"

# Create token account for test wallet
print_info "Creating token account for test wallet..."
TEST_TOKEN_ACCOUNT=$(spl-token create-account "$TOKEN_MINT" --owner "$TEST_WALLET" --fee-payer "$KEYPAIR_FILE" | grep "Creating account" | awk '{print $3}')
print_success "Test token account created"

# Transfer tokens
print_info "Testing token transfer..."
spl-token transfer "$TOKEN_MINT" 100 "$TEST_WALLET" --fund-recipient > /dev/null
print_success "Successfully transferred 100 $TOKEN_SYMBOL to test wallet"

# Verify transfer
TEST_BALANCE=$(spl-token balance "$TOKEN_MINT" --owner "$TEST_WALLET" | awk '{print $1}')
print_success "Test wallet balance: $TEST_BALANCE $TOKEN_SYMBOL"

# Liquidity Pool Preparation
print_header "Preparing for Liquidity Pool"

print_info "Token is ready for liquidity pool creation"
print_info "To create a liquidity pool on devnet:"
echo ""
echo "  1. Visit a devnet-compatible DEX (if available)"
echo "  2. Or use the Raydium devnet UI (if available)"
echo "  3. Token Mint Address: $TOKEN_MINT"
echo "  4. Suggested initial liquidity:"
echo "     - $TOKEN_SYMBOL: $TEST_LIQUIDITY_TOKENS"
echo "     - SOL: $TEST_LIQUIDITY_SOL"
echo ""

# Summary
print_header "Setup Complete!"

echo -e "${GREEN}Token successfully created and tested on devnet!${NC}"
echo ""
echo "Token Details:"
echo "  Name: $TOKEN_NAME"
echo "  Symbol: $TOKEN_SYMBOL"
echo "  Mint Address: $TOKEN_MINT"
echo "  Decimals: $TOKEN_DECIMALS"
echo "  Total Supply: $INITIAL_SUPPLY"
echo ""
echo "View on Explorer:"
echo "  https://explorer.solana.com/address/$TOKEN_MINT?cluster=devnet"
echo ""
echo "Configuration Files:"
echo "  Config: $CONFIG_FILE"
echo "  Environment: $ENV_FILE"
echo ""
echo "Next Steps:"
echo "  1. Test wallet integration with your frontend"
echo "  2. Create test liquidity pool"
echo "  3. Run integration tests"
echo "  4. When ready, use setup-mainnet.sh for production"

# Cleanup test files
rm -f "$TEST_KEYPAIR"

print_success "Devnet setup completed successfully!"
