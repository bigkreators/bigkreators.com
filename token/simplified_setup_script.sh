#!/bin/bash

# BigKreators Token Backend Integration Setup Script (Simplified)
# This version avoids dependency conflicts by using only core Solana libraries

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_section() {
    echo -e "\n${YELLOW}==============================================${NC}"
    echo -e "${YELLOW}$1${NC}"
    echo -e "${YELLOW}==============================================${NC}\n"
}

check_success() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Success${NC}"
    else
        echo -e "${RED}✗ Failed${NC}"
        exit 1
    fi
}

print_section "BigKreators Token Backend Integration Setup (Simplified)"
echo "This version uses only core Solana libraries to avoid dependency conflicts."
echo -e "\nPress Enter to continue or Ctrl+C to cancel..."
read

# Check if we're in the right directory
if [ ! -f "main.py" ] || [ ! -f "requirements.txt" ]; then
    echo -e "${RED}Error: This doesn't appear to be your FastAPI project root directory.${NC}"
    echo "Please run this script from the directory containing main.py and requirements.txt"
    exit 1
fi

print_section "Step 1: Installing Python Dependencies"

# Backup existing requirements.txt
echo -n "Backing up requirements.txt... "
cp requirements.txt requirements.txt.backup
check_success

# Add simplified Solana dependencies
echo -n "Adding Solana dependencies to requirements.txt... "
cat >> requirements.txt << EOF

# Solana integration dependencies (simplified to avoid conflicts)
solana==0.32.1
base58==2.1.1
httpx==0.25.2
pynacl==1.5.0
EOF
check_success

# Install new dependencies
echo -n "Installing new dependencies... "
pip install -r requirements.txt
check_success

print_section "Step 2: Creating Simplified Solana Service"

mkdir -p services

cat > services/solana_service.py << 'EOF'
"""
Simplified Solana service for token operations
Uses only core Solana libraries to avoid dependency conflicts
"""
import asyncio
import json
from typing import List, Optional, Dict, Any
import logging
import base58
import httpx

from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Confirmed
from solana.rpc.types import TxOpts
from solana.keypair import Keypair
from solana.publickey import PublicKey
from solana.transaction import Transaction
from solana.system_program import transfer, TransferParams
from spl.token.constants import TOKEN_PROGRAM_ID
from spl.token.instructions import (
    transfer_checked,
    TransferCheckedParams,
    get_associated_token_address
)

logger = logging.getLogger(__name__)

class SimplifiedSolanaService:
    def __init__(self, rpc_url: str, private_key: str, token_mint: str):
        """
        Initialize simplified Solana service
        
        Args:
            rpc_url: Solana RPC endpoint
            private_key: Base58 encoded private key for authority wallet
            token_mint: Token mint address
        """
        self.client = AsyncClient(rpc_url)
        self.authority = Keypair.from_secret_key(base58.b58decode(private_key))
        self.token_mint = PublicKey(token_mint)
        self.token_decimals = 9
        
    async def get_sol_balance(self, wallet_address: str) -> float:
        """Get SOL balance for a wallet"""
        try:
            wallet_pubkey = PublicKey(wallet_address)
            response = await self.client.get_balance(wallet_pubkey)
            return response.value / 1_000_000_000  # Convert lamports to SOL
        except Exception as e:
            logger.error(f"Error getting SOL balance: {e}")
            return 0.0
    
    async def get_token_balance(self, wallet_address: str) -> float:
        """
        Get token balance for a wallet address using RPC calls
        """
        try:
            wallet_pubkey = PublicKey(wallet_address)
            
            # Get associated token account address
            token_account = get_associated_token_address(
                owner=wallet_pubkey,
                mint=self.token_mint
            )
            
            # Get token account balance
            response = await self.client.get_token_account_balance(
                token_account, commitment=Confirmed
            )
            
            if response.value is None:
                return 0.0
                
            # Convert from raw amount to decimal
            raw_amount = int(response.value.amount)
            return raw_amount / (10 ** self.token_decimals)
            
        except Exception as e:
            logger.error(f"Error getting token balance: {e}")
            return 0.0
    
    async def send_sol(self, recipient_address: str, amount: float) -> Optional[str]:
        """
        Send SOL to a recipient (for testing purposes)
        """
        try:
            recipient_pubkey = PublicKey(recipient_address)
            lamports = int(amount * 1_000_000_000)
            
            transfer_ix = transfer(
                TransferParams(
                    from_pubkey=self.authority.public_key,
                    to_pubkey=recipient_pubkey,
                    lamports=lamports
                )
            )
            
            transaction = Transaction()
            transaction.add(transfer_ix)
            
            response = await self.client.send_transaction(
                transaction,
                self.authority,
                opts=TxOpts(skip_preflight=False, preflight_commitment=Confirmed)
            )
            
            logger.info(f"SOL transfer successful: {response.value}")
            return response.value
            
        except Exception as e:
            logger.error(f"Error sending SOL: {e}")
            return None
    
    async def get_transaction_history(self, wallet_address: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get transaction history for a wallet using simplified RPC calls
        """
        try:
            wallet_pubkey = PublicKey(wallet_address)
            
            # Get signatures for address
            response = await self.client.get_signatures_for_address(
                wallet_pubkey, 
                limit=limit,
                commitment=Confirmed
            )
            
            transactions = []
            for sig_info in response.value:
                transactions.append({
                    'signature': str(sig_info.signature),
                    'slot': sig_info.slot,
                    'block_time': sig_info.block_time,
                    'success': not sig_info.err,
                })
            
            return transactions
            
        except Exception as e:
            logger.error(f"Error getting transaction history: {e}")
            return []
    
    async def create_token_with_cli(self, name: str = "Wiki Contribution Token", symbol: str = "KONTRIB") -> Dict[str, Any]:
        """
        Create token using Solana CLI commands via subprocess
        This avoids complex library dependencies
        """
        import subprocess
        import tempfile
        import os
        
        try:
            # Create temporary keypair file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                keypair_data = list(self.authority.secret_key)
                json.dump(keypair_data, f)
                keypair_file = f.name
            
            # Create token mint using CLI
            result = subprocess.run([
                'spl-token', 'create-token',
                '--decimals', '9',
                '--mint-authority', str(self.authority.public_key),
                '--keypair', keypair_file
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                # Extract mint address from output
                lines = result.stdout.strip().split('\n')
                mint_address = None
                for line in lines:
                    if 'Creating token' in line:
                        mint_address = line.split()[-1]
                        break
                
                if mint_address:
                    # Create token account
                    account_result = subprocess.run([
                        'spl-token', 'create-account', mint_address,
                        '--keypair', keypair_file
                    ], capture_output=True, text=True)
                    
                    # Mint initial supply
                    mint_result = subprocess.run([
                        'spl-token', 'mint', mint_address, '100000000',
                        '--keypair', keypair_file
                    ], capture_output=True, text=True)
                    
                    # Clean up
                    os.unlink(keypair_file)
                    
                    return {
                        'mint_address': mint_address,
                        'authority': str(self.authority.public_key),
                        'success': True,
                        'message': 'Token created successfully using CLI'
                    }
            
            # Clean up on failure
            os.unlink(keypair_file)
            return {
                'success': False,
                'error': result.stderr,
                'message': 'Token creation failed'
            }
            
        except Exception as e:
            logger.error(f"Error creating token with CLI: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Token creation failed'
            }
    
    async def close(self):
        """Close the async client"""
        await self.client.close()
EOF
check_success

print_section "Step 3: Creating Token Models"

cat > models/token.py << 'EOF'
"""
Token-related models for the BigKreators token system
"""
from models.base import DBModel, DateTimeModelMixin
from typing import Optional
from pydantic import Field, BaseModel
from datetime import datetime

class Contribution(DBModel, DateTimeModelMixin):
    """Model for tracking user contributions"""
    user_id: str = Field(..., description="User who made the contribution")
    article_id: str = Field(..., description="Article that was contributed to")
    type: str = Field(..., description="Type of contribution")
    base_points: int = Field(..., description="Base points for this contribution type")
    quality_multiplier: float = Field(1.0, description="Quality multiplier (0.5-3.0)")
    reputation_multiplier: float = Field(1.0, description="User reputation multiplier")
    demand_multiplier: float = Field(1.0, description="Content demand multiplier")
    total_points: int = Field(..., description="Total points after all multipliers")
    description: Optional[str] = Field(None, description="Description of contribution")

class TokenReward(DBModel, DateTimeModelMixin):
    """Model for individual token rewards"""
    user_id: str = Field(..., description="User receiving reward")
    week_start: datetime = Field(..., description="Start of reward week")
    week_end: datetime = Field(..., description="End of reward week")
    total_points: int = Field(..., description="Total points earned this week")
    token_amount: float = Field(..., description="Tokens awarded")
    transaction_signature: Optional[str] = Field(None, description="Blockchain transaction signature")
    status: str = Field("pending", description="Reward status")

class ContributionCreate(BaseModel):
    """Model for creating new contributions"""
    article_id: str = Field(..., description="Article ID")
    type: str = Field(..., description="Contribution type")
    description: Optional[str] = Field(None, description="Description")

class WalletInfo(BaseModel):
    """Model for wallet information"""
    address: str = Field(..., description="Wallet address")
    sol_balance: float = Field(0.0, description="SOL balance")
    token_balance: float = Field(0.0, description="Token balance")
EOF
check_success

print_section "Step 4: Creating Token Routes"

cat > routes/token.py << 'EOF'
"""
Simplified token routes using basic Solana functionality
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import List, Optional
from datetime import datetime, timedelta
import logging

from models.token import Contribution, TokenReward, ContributionCreate, WalletInfo
from models.user import User
from dependencies.database import get_db
from dependencies.auth import get_current_user
from services.solana_service import SimplifiedSolanaService
import config

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize Solana service
solana_service = None

def get_solana_service():
    global solana_service
    if solana_service is None:
        try:
            solana_service = SimplifiedSolanaService(
                rpc_url=config.SOLANA_RPC_URL,
                private_key=config.SOLANA_PRIVATE_KEY,
                token_mint=config.TOKEN_MINT_ADDRESS
            )
        except Exception as e:
            logger.error(f"Failed to initialize Solana service: {e}")
            return None
    return solana_service

@router.get("/status")
async def get_token_status():
    """Get token system status"""
    service = get_solana_service()
    if not service:
        return {"status": "error", "message": "Solana service not available"}
    
    try:
        # Test connection
        authority_balance = await service.get_sol_balance(str(service.authority.public_key))
        return {
            "status": "active",
            "network": "devnet",
            "authority_wallet": str(service.authority.public_key),
            "authority_sol_balance": authority_balance,
            "token_mint": str(service.token_mint)
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.get("/wallet/{wallet_address}")
async def get_wallet_info(wallet_address: str):
    """Get wallet information including SOL and token balances"""
    service = get_solana_service()
    if not service:
        raise HTTPException(status_code=500, detail="Solana service not available")
    
    try:
        sol_balance = await service.get_sol_balance(wallet_address)
        token_balance = await service.get_token_balance(wallet_address)
        
        return WalletInfo(
            address=wallet_address,
            sol_balance=sol_balance,
            token_balance=token_balance
        )
    except Exception as e:
        logger.error(f"Error getting wallet info: {e}")
        raise HTTPException(status_code=500, detail="Failed to get wallet information")

@router.post("/contributions", response_model=dict)
async def track_contribution(
    contribution_data: ContributionCreate,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Track a user contribution and calculate points"""
    try:
        # Calculate points based on contribution type
        points_mapping = {
            'creation': 100,
            'major_edit': 50,
            'minor_edit': 20,
            'review': 10
        }
        
        base_points = points_mapping.get(contribution_data.type, 0)
        
        # Get user reputation multiplier
        user_doc = await db.users.find_one({"_id": current_user.id})
        reputation_multiplier = user_doc.get('reputation_score', 1.0) if user_doc else 1.0
        
        # Calculate total points
        total_points = int(base_points * reputation_multiplier)
        
        # Create contribution record
        contribution = {
            "user_id": str(current_user.id),
            "article_id": contribution_data.article_id,
            "type": contribution_data.type,
            "base_points": base_points,
            "quality_multiplier": 1.0,
            "reputation_multiplier": reputation_multiplier,
            "demand_multiplier": 1.0,
            "total_points": total_points,
            "description": contribution_data.description,
            "created_at": datetime.utcnow()
        }
        
        # Save to database
        result = await db.contributions.insert_one(contribution)
        
        # Update user stats
        await db.users.update_one(
            {"_id": current_user.id},
            {
                "$inc": {
                    "total_contributions": 1
                },
                "$set": {
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        return {
            "success": True,
            "contribution_id": str(result.inserted_id),
            "points_earned": total_points,
            "message": f"Contribution tracked! Earned {total_points} points."
        }
        
    except Exception as e:
        logger.error(f"Error tracking contribution: {e}")
        raise HTTPException(status_code=500, detail="Failed to track contribution")

@router.get("/rewards/user/{user_id}")
async def get_user_rewards(
    user_id: str,
    skip: int = 0,
    limit: int = 10,
    db = Depends(get_db)
):
    """Get user's contribution and reward history"""
    try:
        # Get user's contributions
        contributions = await db.contributions.find(
            {"user_id": user_id}
        ).sort("created_at", -1).skip(skip).limit(limit).to_list(None)
        
        # Get total points
        total_points = await db.contributions.aggregate([
            {"$match": {"user_id": user_id}},
            {"$group": {"_id": None, "total": {"$sum": "$total_points"}}}
        ]).to_list(None)
        
        total_user_points = total_points[0]["total"] if total_points else 0
        
        # Get user info
        user = await db.users.find_one({"_id": user_id})
        
        return {
            "user_id": user_id,
            "total_contributions": len(contributions) if contributions else 0,
            "total_points": total_user_points,
            "wallet_address": user.get('wallet_address') if user else None,
            "contributions": contributions,
            "estimated_weekly_tokens": total_user_points * 0.1  # Rough estimate
        }
        
    except Exception as e:
        logger.error(f"Error getting user rewards: {e}")
        raise HTTPException(status_code=500, detail="Failed to get user rewards")

@router.get("/transactions/{wallet_address}")
async def get_transaction_history(wallet_address: str, limit: int = 10):
    """Get transaction history for a wallet"""
    service = get_solana_service()
    if not service:
        raise HTTPException(status_code=500, detail="Solana service not available")
    
    try:
        transactions = await service.get_transaction_history(wallet_address, limit)
        return {"wallet_address": wallet_address, "transactions": transactions}
    except Exception as e:
        logger.error(f"Error getting transaction history: {e}")
        raise HTTPException(status_code=500, detail="Failed to get transaction history")

@router.post("/create-token")
async def create_token_mint(current_user: User = Depends(get_current_user)):
    """Create a new token mint (admin only)"""
    service = get_solana_service()
    if not service:
        raise HTTPException(status_code=500, detail="Solana service not available")
    
    try:
        # TODO: Add admin check
        result = await service.create_token_with_cli()
        return result
    except Exception as e:
        logger.error(f"Error creating token: {e}")
        raise HTTPException(status_code=500, detail="Failed to create token")
EOF
check_success

print_section "Step 5: Creating Simplified Token Creation Script"

cat > create_token_simple.py << 'EOF'
#!/usr/bin/env python3
"""
Simplified BigKreators KONTRIB Token Creation Script
Uses Solana CLI commands to avoid library conflicts
"""

import subprocess
import json
import base58
import tempfile
import os
from datetime import datetime
from solana.keypair import Keypair

# Colors for output
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
RED = '\033[0;31m'
BLUE = '\033[0;34m'
NC = '\033[0m'

def print_section(title):
    print(f"\n{YELLOW}{'='*50}{NC}")
    print(f"{YELLOW}{title}{NC}")
    print(f"{YELLOW}{'='*50}{NC}\n")

def print_success(message):
    print(f"{GREEN}✅ {message}{NC}")

def print_error(message):
    print(f"{RED}❌ {message}{NC}")

def print_info(message):
    print(f"{BLUE}ℹ️  {message}{NC}")

def check_solana_cli():
    """Check if Solana CLI is installed"""
    try:
        result = subprocess.run(['solana', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print_success(f"Solana CLI found: {result.stdout.strip()}")
            return True
        else:
            print_error("Solana CLI not found")
            return False
    except FileNotFoundError:
        print_error("Solana CLI not installed")
        print_info("Install with: sh -c \"$(curl -sSfL https://release.solana.com/v1.16.0/install)\"")
        return False

def check_spl_token_cli():
    """Check if SPL Token CLI is installed"""
    try:
        result = subprocess.run(['spl-token', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print_success(f"SPL Token CLI found: {result.stdout.strip()}")
            return True
        else:
            print_error("SPL Token CLI not found")
            return False
    except FileNotFoundError:
        print_error("SPL Token CLI not installed")
        print_info("Install with: cargo install spl-token-cli")
        return False

def create_token_simple():
    """Create token using CLI commands"""
    
    print_section("BigKreators KONTRIB Token Creation (Simplified)")
    
    # Check prerequisites
    if not check_solana_cli():
        return False
    
    if not check_spl_token_cli():
        return False
    
    # Configure Solana to use devnet
    print_info("Configuring Solana CLI for devnet...")
    subprocess.run(['solana', 'config', 'set', '--url', 'devnet'], capture_output=True)
    
    # Create new keypair
    print_section("Creating Authority Keypair")
    
    # Create keypair programmatically
    authority_keypair = Keypair()
    print_success(f"Authority wallet: {authority_keypair.public_key}")
    
    # Save keypair to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        keypair_data = list(authority_keypair.secret_key)
        json.dump(keypair_data, f)
        keypair_file = f.name
    
    try:
        # Set CLI to use this keypair
        subprocess.run(['solana', 'config', 'set', '--keypair', keypair_file], capture_output=True)
        
        # Request airdrop
        print_section("Requesting Airdrop")
        print_info("Requesting 2 SOL airdrop...")
        airdrop_result = subprocess.run([
            'solana', 'airdrop', '2'
        ], capture_output=True, text=True)
        
        if airdrop_result.returncode == 0:
            print_success("Airdrop successful")
        else:
            print_error(f"Airdrop failed: {airdrop_result.stderr}")
            print_info("You may need to request airdrop manually or wait and retry")
        
        # Create token
        print_section("Creating Token")
        print_info("Creating KONTRIB token with 9 decimals...")
        
        create_result = subprocess.run([
            'spl-token', 'create-token',
            '--decimals', '9'
        ], capture_output=True, text=True)
        
        if create_result.returncode != 0:
            print_error(f"Token creation failed: {create_result.stderr}")
            return False
        
        # Extract token mint address
        lines = create_result.stdout.strip().split('\n')
        token_mint = None
        for line in lines:
            if 'Creating token' in line:
                token_mint = line.split()[-1]
                break
        
        if not token_mint:
            print_error("Could not extract token mint address")
            return False
        
        print_success(f"Token created: {token_mint}")
        
        # Create token account
        print_section("Creating Token Account")
        account_result = subprocess.run([
            'spl-token', 'create-account', token_mint
        ], capture_output=True, text=True)
        
        if account_result.returncode != 0:
            print_error(f"Token account creation failed: {account_result.stderr}")
            return False
        
        print_success("Token account created")
        
        # Mint initial supply
        print_section("Minting Initial Supply")
        print_info("Minting 100,000,000 KONTRIB tokens...")
        
        mint_result = subprocess.run([
            'spl-token', 'mint', token_mint, '100000000'
        ], capture_output=True, text=True)
        
        if mint_result.returncode != 0:
            print_error(f"Token minting failed: {mint_result.stderr}")
            return False
        
        print_success("100M KONTRIB tokens minted successfully")
        
        # Get balance to verify
        balance_result = subprocess.run([
            'spl-token', 'balance', token_mint
        ], capture_output=True, text=True)
        
        if balance_result.returncode == 0:
            balance = balance_result.stdout.strip()
            print_success(f"Token balance verified: {balance} KONTRIB")
        
        # Generate configuration
        print_section("Generating Configuration")
        
        config = {
            "token_name": "Wiki Contribution Token",
            "token_symbol": "KONTRIB",
            "token_mint": token_mint,
            "authority_wallet": str(authority_keypair.public_key),
            "authority_private_key": base58.b58encode(authority_keypair.secret_key).decode(),
            "decimals": 9,
            "initial_supply": 100_000_000,
            "network": "devnet",
            "rpc_url": "https://api.devnet.solana.com",
            "created_at": datetime.utcnow().isoformat(),
            "explorer_url": f"https://explorer.solana.com/address/{token_mint}?cluster=devnet"
        }
        
        # Save configuration
        with open('wct_token_config.json', 'w') as f:
            json.dump(config, f, indent=2)
        
        print_success("Configuration saved to wct_token_config.json")
        
        # Generate .env variables
        env_vars = f"""SOLANA_RPC_URL=https://api.devnet.solana.com
SOLANA_PRIVATE_KEY={base58.b58encode(authority_keypair.secret_key).decode()}
TOKEN_MINT_ADDRESS={token_mint}
WEEKLY_TOKEN_POOL=10000.0
MIN_TOKENS_PER_USER=1.0"""
        
        with open('.env.wct.generated', 'w') as f:
            f.write(env_vars)
        
        print_success("Environment variables saved to .env.wct.generated")
        
        # Print summary
        print_section("Token Creation Summary")
        print(f"{GREEN}🎉 KONTRIB Token successfully created!{NC}")
        print(f"{BLUE}Token Mint:{NC} {token_mint}")
        print(f"{BLUE}Authority Wallet:{NC} {authority_keypair.public_key}")
        print(f"{BLUE}Initial Supply:{NC} 100,000,000 KONTRIB")
        print(f"{BLUE}Explorer:{NC} https://explorer.solana.com/address/{token_mint}?cluster=devnet")
        
        return True
        
    finally:
        # Clean up temporary keypair file
        if os.path.exists(keypair_file):
            os.unlink(keypair_file)

if __name__ == "__main__":
    success = create_token_simple()
    if success:
        print_success("Token creation completed successfully!")
        print_info("Next: Add the variables from .env.wct.generated to your .env file")
    else:
        print_error("Token creation failed")
        exit(1)
EOF
check_success

# Make the token creation script executable
chmod +x create_token_simple.py

print_section "Step 6: Updating Configuration"

# Backup existing config
echo -n "Backing up existing config... "
cp config.py config.py.backup
check_success

# Add token configuration
echo -n "Adding token configuration... "
cat >> config.py << 'EOF'

# Solana and Token Configuration
SOLANA_RPC_URL = os.getenv("SOLANA_RPC_URL", "https://api.devnet.solana.com")
SOLANA_PRIVATE_KEY = os.getenv("SOLANA_PRIVATE_KEY", "")
TOKEN_MINT_ADDRESS = os.getenv("TOKEN_MINT_ADDRESS", "")

# Token system configuration
WEEKLY_TOKEN_POOL = float(os.getenv("WEEKLY_TOKEN_POOL", "10000.0"))
MIN_TOKENS_PER_USER = float(os.getenv("MIN_TOKENS_PER_USER", "1.0"))
EOF
check_success

print_section "Step 7: Adding Token Routes to Main App"

# Create a backup of main.py
echo -n "Backing up main.py... "
cp main.py main.py.backup
check_success

# Add token routes to main.py
echo -n "Adding token routes to main.py... "
cat >> main.py << 'EOF'

# Token routes integration
try:
    from routes import token
    app.include_router(token.router, prefix="/api/token", tags=["Token"])
except ImportError as e:
    print(f"Warning: Could not import token routes: {e}")
EOF
check_success

print_section "Step 8: Creating Test Script"

cat > test_token_simple.py << 'EOF'
"""
Test script for simplified token integration
"""
import asyncio
import os
from dotenv import load_dotenv

async def test_token_integration():
    """Test the simplified token integration"""
    
    print("🧪 Testing Token Integration")
    print("=" * 40)
    
    # Load environment variables
    load_dotenv()
    
    # Check environment variables
    rpc_url = os.getenv("SOLANA_RPC_URL")
    private_key = os.getenv("SOLANA_PRIVATE_KEY")
    token_mint = os.getenv("TOKEN_MINT_ADDRESS")
    
    print(f"RPC URL: {rpc_url or 'Not set'}")
    print(f"Private Key: {'Set' if private_key else 'Not set'}")
    print(f"Token Mint: {token_mint or 'Not set'}")
    
    if not all([rpc_url, private_key, token_mint]):
        print("❌ Missing environment variables. Run create_token_simple.py first.")
        return False
    
    print("✅ Environment variables found")
    
    # Test Solana service
    try:
        from services.solana_service import SimplifiedSolanaService
        
        service = SimplifiedSolanaService(rpc_url, private_key, token_mint)
        print("✅ Solana service initialized")
        
        # Test getting SOL balance
        authority_address = str(service.authority.public_key)
        sol_balance = await service.get_sol_balance(authority_address)
        print(f"✅ Authority SOL balance: {sol_balance} SOL")
        
        # Test getting token balance
        token_balance = await service.get_token_balance(authority_address)
        print(f"✅ Authority token balance: {token_balance} KONTRIB")
        
        # Test transaction history
        history = await service.get_transaction_history(authority_address, limit=3)
        print(f"✅ Recent transactions: {len(history)} found")
        
        await service.close()
        print("✅ All tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_token_integration())
    if not success:
        exit(1)
EOF
check_success

print_section "Setup Complete!"

echo -e "${GREEN}✅ Simplified token backend integration setup complete!${NC}"
echo
echo -e "${YELLOW}This version avoids dependency conflicts by:${NC}"
echo "- Using older, compatible Solana library versions"
echo "- Providing CLI-based token creation as backup"
echo "- Simplified service with core functionality"
echo
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Install Solana CLI (if not already installed):"
echo "   sh -c \"\$(curl -sSfL https://release.solana.com/v1.16.0/install)\""
echo
echo "2. Install SPL Token CLI:"
echo "   cargo install spl-token-cli"
echo
echo "3. Create your token:"
echo "   python create_token_simple.py"
echo
echo "4. Add generated environment variables to your .env file:"
echo "   cat .env.wct.generated >> .env"
echo
echo "5. Test the integration:"
echo "   python test_token_simple.py"
echo
echo "6. Start your server and test:"
echo "   uvicorn main:app --reload"
echo "   curl http://localhost:8000/api/token/status"
echo
echo -e "${BLUE}Files created:${NC}"
echo "- services/solana_service.py (simplified version)"
echo "- models/token.py"
echo "- routes/token.py (simplified)"
echo "- create_token_simple.py"
echo "- test_token_simple.py"
echo
echo -e "${YELLOW}Ready to create your token with no dependency conflicts!${NC}"
