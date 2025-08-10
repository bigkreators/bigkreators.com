#!/bin/bash

# BigKreators Token Backend Integration Setup Script
# This script adds Solana token functionality to your existing FastAPI backend

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print section headers
print_section() {
    echo -e "\n${YELLOW}==============================================${NC}"
    echo -e "${YELLOW}$1${NC}"
    echo -e "${YELLOW}==============================================${NC}\n"
}

# Function to check if a command was successful
check_success() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Success${NC}"
    else
        echo -e "${RED}✗ Failed${NC}"
        exit 1
    fi
}

# Welcome message
print_section "BigKreators Token Backend Integration Setup"
echo "This script will:"
echo "1. Install Python Solana dependencies"
echo "2. Create token service files"
echo "3. Extend your existing models"
echo "4. Add token routes"
echo "5. Set up Solana devnet token creation"
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

# Add Solana dependencies
echo -n "Adding Solana dependencies to requirements.txt... "
cat >> requirements.txt << EOF

# Solana integration dependencies
solana==0.32.1
solders==0.20.1
anchorpy==0.19.1
base58==2.1.1
construct==2.10.68
borsh-construct==0.1.0
EOF
check_success

# Install new dependencies
echo -n "Installing new dependencies... "
pip install -r requirements.txt
check_success

print_section "Step 2: Creating Solana Service"

# Create services directory if it doesn't exist
mkdir -p services

# Create Solana service
cat > services/solana_service.py << 'EOF'
"""
Solana blockchain service for token operations
"""
import asyncio
import json
from typing import List, Optional, Dict, Any
from decimal import Decimal
import logging

from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Confirmed
from solana.rpc.types import TxOpts
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.system_program import CreateAccountParams, create_account
from solders.transaction import Transaction
from spl.token.async_client import AsyncToken
from spl.token.constants import TOKEN_PROGRAM_ID, ASSOCIATED_TOKEN_PROGRAM_ID
from spl.token.instructions import (
    create_associated_token_account,
    get_associated_token_address,
    transfer_checked,
    TransferCheckedParams
)
import base58

logger = logging.getLogger(__name__)

class SolanaService:
    def __init__(self, rpc_url: str, private_key: str, token_mint: str):
        """
        Initialize Solana service
        
        Args:
            rpc_url: Solana RPC endpoint
            private_key: Base58 encoded private key for authority wallet
            token_mint: Token mint address
        """
        self.client = AsyncClient(rpc_url)
        self.authority = Keypair.from_bytes(base58.b58decode(private_key))
        self.token_mint = Pubkey.from_string(token_mint)
        self.token_decimals = 9  # Standard for SPL tokens
        
    async def get_token_balance(self, wallet_address: str) -> float:
        """
        Get token balance for a wallet address
        
        Args:
            wallet_address: Wallet address to check
            
        Returns:
            Token balance as float
        """
        try:
            wallet_pubkey = Pubkey.from_string(wallet_address)
            
            # Get associated token account
            token_account = get_associated_token_address(
                owner=wallet_pubkey,
                mint=self.token_mint
            )
            
            # Get account info
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
    
    async def transfer_tokens(self, 
                             recipient_address: str, 
                             amount: float, 
                             memo: Optional[str] = None) -> Optional[str]:
        """
        Transfer tokens to a recipient
        
        Args:
            recipient_address: Recipient wallet address
            amount: Amount to transfer (in tokens, not raw units)
            memo: Optional transaction memo
            
        Returns:
            Transaction signature if successful, None otherwise
        """
        try:
            recipient_pubkey = Pubkey.from_string(recipient_address)
            
            # Convert amount to raw units
            raw_amount = int(amount * (10 ** self.token_decimals))
            
            # Get or create associated token accounts
            authority_token_account = get_associated_token_address(
                owner=self.authority.pubkey(),
                mint=self.token_mint
            )
            
            recipient_token_account = get_associated_token_address(
                owner=recipient_pubkey,
                mint=self.token_mint
            )
            
            # Check if recipient token account exists
            account_info = await self.client.get_account_info(
                recipient_token_account, commitment=Confirmed
            )
            
            transaction = Transaction()
            
            # Create recipient token account if it doesn't exist
            if account_info.value is None:
                create_account_ix = create_associated_token_account(
                    payer=self.authority.pubkey(),
                    owner=recipient_pubkey,
                    mint=self.token_mint
                )
                transaction.add(create_account_ix)
            
            # Add transfer instruction
            transfer_ix = transfer_checked(
                TransferCheckedParams(
                    program_id=TOKEN_PROGRAM_ID,
                    source=authority_token_account,
                    mint=self.token_mint,
                    dest=recipient_token_account,
                    owner=self.authority.pubkey(),
                    amount=raw_amount,
                    decimals=self.token_decimals,
                    signers=[self.authority]
                )
            )
            transaction.add(transfer_ix)
            
            # Send transaction
            response = await self.client.send_transaction(
                transaction, 
                self.authority,
                opts=TxOpts(skip_preflight=False, preflight_commitment=Confirmed)
            )
            
            logger.info(f"Token transfer successful: {response.value}")
            return response.value
            
        except Exception as e:
            logger.error(f"Error transferring tokens: {e}")
            return None
    
    async def batch_transfer_tokens(self, transfers: List[Dict[str, Any]]) -> List[Optional[str]]:
        """
        Batch transfer tokens to multiple recipients
        
        Args:
            transfers: List of transfer dictionaries with 'address' and 'amount' keys
            
        Returns:
            List of transaction signatures
        """
        results = []
        
        # Process transfers in batches to avoid rate limits
        batch_size = 5
        for i in range(0, len(transfers), batch_size):
            batch = transfers[i:i + batch_size]
            
            # Create tasks for concurrent processing
            tasks = []
            for transfer in batch:
                task = self.transfer_tokens(
                    recipient_address=transfer['address'],
                    amount=transfer['amount'],
                    memo=transfer.get('memo')
                )
                tasks.append(task)
            
            # Execute batch
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"Batch transfer error: {result}")
                    results.append(None)
                else:
                    results.append(result)
            
            # Small delay between batches
            await asyncio.sleep(0.1)
        
        return results
    
    async def get_transaction_history(self, 
                                    wallet_address: str, 
                                    limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get transaction history for a wallet
        
        Args:
            wallet_address: Wallet address
            limit: Number of transactions to return
            
        Returns:
            List of transaction details
        """
        try:
            wallet_pubkey = Pubkey.from_string(wallet_address)
            
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
    
    async def close(self):
        """Close the async client"""
        await self.client.close()
EOF
check_success

print_section "Step 3: Creating Token Models"

# Create token models
cat > models/token.py << 'EOF'
"""
Token-related models for the BigKreators token system
"""
from models.base import DBModel, DateTimeModelMixin
from typing import Optional, List
from pydantic import Field
from datetime import datetime

class Contribution(DBModel, DateTimeModelMixin):
    """Model for tracking user contributions"""
    user_id: str = Field(..., description="User who made the contribution")
    article_id: str = Field(..., description="Article that was contributed to")
    type: str = Field(..., description="Type of contribution", 
                     pattern="^(creation|major_edit|minor_edit|review)$")
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
    status: str = Field("pending", description="Reward status",
                       pattern="^(pending|processing|completed|failed)$")

class WeeklyDistribution(DBModel, DateTimeModelMixin):
    """Model for weekly token distribution records"""
    week_start: datetime = Field(..., description="Start of distribution week")
    week_end: datetime = Field(..., description="End of distribution week")
    total_points: int = Field(..., description="Total points across all users")
    total_tokens: float = Field(..., description="Total tokens distributed")
    point_to_token_ratio: float = Field(..., description="Conversion ratio")
    distribution_tx_hash: Optional[str] = Field(None, description="Main distribution transaction")
    status: str = Field("pending", description="Distribution status")
    user_count: int = Field(0, description="Number of users in distribution")

class ContributionCreate(BaseModel):
    """Model for creating new contributions"""
    article_id: str = Field(..., description="Article ID")
    type: str = Field(..., description="Contribution type",
                     pattern="^(creation|major_edit|minor_edit|review)$")
    description: Optional[str] = Field(None, description="Description")

class TokenTransfer(BaseModel):
    """Model for token transfer requests"""
    recipient_address: str = Field(..., description="Recipient wallet address")
    amount: float = Field(..., gt=0, description="Amount to transfer")
    memo: Optional[str] = Field(None, description="Transfer memo")
EOF
check_success

print_section "Step 4: Extending User Model"

# Backup existing user model
echo -n "Backing up existing user model... "
cp models/user.py models/user.py.backup
check_success

# Add token fields to user model
echo -n "Adding token fields to user model... "
cat >> models/user.py << 'EOF'

# Token-related fields added by token integration
class UserTokenExtension(BaseModel):
    """Extension fields for token system"""
    wallet_address: Optional[str] = Field(None, description="Solana wallet address")
    reputation_score: float = Field(1.0, description="User reputation multiplier")
    total_contributions: int = Field(0, description="Total contributions made")
    total_tokens_earned: float = Field(0.0, description="Total tokens earned")
    staked_tokens: float = Field(0.0, description="Currently staked tokens")

# Note: You'll need to manually merge these fields into your existing User model
EOF
check_success

print_section "Step 5: Creating Token Routes"

# Create token routes
cat > routes/token.py << 'EOF'
"""
Token-related API routes
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import List, Optional
from datetime import datetime, timedelta
import logging

from models.token import Contribution, TokenReward, WeeklyDistribution, ContributionCreate, TokenTransfer
from models.user import User
from dependencies.database import get_db
from dependencies.auth import get_current_user
from services.solana_service import SolanaService
import config

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize Solana service
solana_service = None

def get_solana_service():
    global solana_service
    if solana_service is None:
        solana_service = SolanaService(
            rpc_url=config.SOLANA_RPC_URL,
            private_key=config.SOLANA_PRIVATE_KEY,
            token_mint=config.TOKEN_MINT_ADDRESS
        )
    return solana_service

@router.post("/contributions", response_model=dict)
async def track_contribution(
    contribution_data: ContributionCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Track a user contribution and calculate points
    """
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
            "quality_multiplier": 1.0,  # TODO: Implement quality assessment
            "reputation_multiplier": reputation_multiplier,
            "demand_multiplier": 1.0,   # TODO: Implement demand calculation
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
                    "total_contributions": 1,
                    "total_points": total_points
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

@router.get("/balance/{wallet_address}")
async def get_token_balance(wallet_address: str):
    """
    Get token balance for a wallet address
    """
    try:
        service = get_solana_service()
        balance = await service.get_token_balance(wallet_address)
        return {"wallet_address": wallet_address, "balance": balance}
    except Exception as e:
        logger.error(f"Error getting token balance: {e}")
        raise HTTPException(status_code=500, detail="Failed to get token balance")

@router.get("/rewards/user/{user_id}")
async def get_user_rewards(
    user_id: str,
    skip: int = 0,
    limit: int = 10,
    db = Depends(get_db)
):
    """
    Get user's token rewards history
    """
    try:
        # Get user's contributions
        contributions = await db.contributions.find(
            {"user_id": user_id}
        ).sort("created_at", -1).skip(skip).limit(limit).to_list(None)
        
        # Get user's rewards
        rewards = await db.token_rewards.find(
            {"user_id": user_id}
        ).sort("created_at", -1).skip(skip).limit(limit).to_list(None)
        
        # Get user stats
        user = await db.users.find_one({"_id": user_id})
        
        return {
            "user_id": user_id,
            "total_contributions": user.get('total_contributions', 0) if user else 0,
            "total_tokens_earned": user.get('total_tokens_earned', 0.0) if user else 0.0,
            "wallet_address": user.get('wallet_address') if user else None,
            "contributions": contributions,
            "rewards": rewards
        }
        
    except Exception as e:
        logger.error(f"Error getting user rewards: {e}")
        raise HTTPException(status_code=500, detail="Failed to get user rewards")

@router.post("/transfer")
async def transfer_tokens(
    transfer_data: TokenTransfer,
    current_user: User = Depends(get_current_user),
):
    """
    Transfer tokens to another wallet
    """
    try:
        service = get_solana_service()
        signature = await service.transfer_tokens(
            recipient_address=transfer_data.recipient_address,
            amount=transfer_data.amount,
            memo=transfer_data.memo
        )
        
        if signature:
            return {
                "success": True,
                "transaction_signature": signature,
                "message": f"Successfully transferred {transfer_data.amount} tokens"
            }
        else:
            raise HTTPException(status_code=500, detail="Transfer failed")
            
    except Exception as e:
        logger.error(f"Error transferring tokens: {e}")
        raise HTTPException(status_code=500, detail="Failed to transfer tokens")

@router.post("/distribute-weekly-rewards")
async def distribute_weekly_rewards(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Distribute weekly token rewards to users (admin only)
    """
    try:
        # TODO: Add admin permission check
        
        # Calculate week boundaries
        now = datetime.utcnow()
        week_start = now - timedelta(days=7)
        
        # Get all contributions from this week
        weekly_contributions = await db.contributions.find({
            "created_at": {"$gte": week_start, "$lt": now}
        }).to_list(None)
        
        # Calculate total points
        total_points = sum(contrib['total_points'] for contrib in weekly_contributions)
        
        if total_points == 0:
            return {"message": "No contributions this week"}
        
        # Weekly token allocation (configurable)
        weekly_token_pool = float(config.WEEKLY_TOKEN_POOL)
        point_to_token_ratio = weekly_token_pool / total_points
        
        # Group contributions by user
        user_points = {}
        for contrib in weekly_contributions:
            user_id = contrib['user_id']
            user_points[user_id] = user_points.get(user_id, 0) + contrib['total_points']
        
        # Prepare batch transfers
        transfers = []
        for user_id, points in user_points.items():
            user = await db.users.find_one({"_id": user_id})
            if user and user.get('wallet_address'):
                token_amount = points * point_to_token_ratio
                transfers.append({
                    'user_id': user_id,
                    'address': user['wallet_address'],
                    'amount': token_amount,
                    'points': points,
                    'memo': f'Weekly reward for {points} points'
                })
        
        # Execute batch transfer in background
        background_tasks.add_task(execute_batch_transfer, transfers, db, week_start, now)
        
        return {
            "message": f"Queued rewards for {len(transfers)} users",
            "total_points": total_points,
            "total_tokens": weekly_token_pool,
            "point_to_token_ratio": point_to_token_ratio
        }
        
    except Exception as e:
        logger.error(f"Error distributing weekly rewards: {e}")
        raise HTTPException(status_code=500, detail="Failed to distribute rewards")

async def execute_batch_transfer(transfers: List[dict], db, week_start: datetime, week_end: datetime):
    """
    Background task to execute batch token transfers
    """
    try:
        service = get_solana_service()
        
        # Execute blockchain transfers
        signatures = await service.batch_transfer_tokens(transfers)
        
        # Record rewards in database
        for i, transfer in enumerate(transfers):
            reward_record = {
                "user_id": transfer.get('user_id'),
                "week_start": week_start,
                "week_end": week_end,
                "total_points": transfer.get('points', 0),
                "token_amount": transfer['amount'],
                "transaction_signature": signatures[i] if i < len(signatures) else None,
                "status": "completed" if (i < len(signatures) and signatures[i]) else "failed",
                "created_at": datetime.utcnow()
            }
            await db.token_rewards.insert_one(reward_record)
            
            # Update user total tokens earned
            if signatures[i]:
                await db.users.update_one(
                    {"_id": transfer['user_id']},
                    {"$inc": {"total_tokens_earned": transfer['amount']}}
                )
        
        logger.info(f"Batch transfer completed: {len(transfers)} transfers")
        
    except Exception as e:
        logger.error(f"Error in batch transfer: {e}")
EOF
check_success

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
from routes import token
app.include_router(token.router, prefix="/api/token", tags=["Token"])
EOF
check_success

print_section "Step 8: Creating Environment Variables Template"

# Create .env template
cat > .env.token.template << 'EOF'
# Add these variables to your existing .env file:

# Solana Configuration
SOLANA_RPC_URL=https://api.devnet.solana.com
SOLANA_PRIVATE_KEY=your_base58_encoded_private_key_here
TOKEN_MINT_ADDRESS=your_token_mint_address_here

# Token System Settings
WEEKLY_TOKEN_POOL=10000.0
MIN_TOKENS_PER_USER=1.0
EOF
check_success

print_section "Step 9: Creating Token Creation Script"

# Create token creation script
cat > create_token.py << 'EOF'
"""
Script to create KONTRIB token on Solana devnet
"""
import asyncio
import base58
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solana.rpc.async_api import AsyncClient
from spl.token.async_client import AsyncToken
from spl.token.constants import TOKEN_PROGRAM_ID
import os
from dotenv import load_dotenv

load_dotenv()

async def create_token():
    """Create the KONTRIB token on Solana devnet"""
    
    # Connect to devnet
    client = AsyncClient("https://api.devnet.solana.com")
    
    # Create or load authority keypair
    authority_keypair = Keypair()
    print(f"Authority wallet: {authority_keypair.pubkey()}")
    print(f"Authority private key (base58): {base58.b58encode(authority_keypair.secret()).decode()}")
    
    # Request airdrop for gas fees
    print("Requesting airdrop...")
    airdrop_response = await client.request_airdrop(authority_keypair.pubkey(), 2_000_000_000)  # 2 SOL
    print(f"Airdrop transaction: {airdrop_response.value}")
    
    # Wait for airdrop confirmation
    await asyncio.sleep(5)
    
    # Create token
    print("Creating token...")
    token = AsyncToken(
        conn=client,
        pubkey=Pubkey.default(),  # Will be set after creation
        program_id=TOKEN_PROGRAM_ID,
        payer=authority_keypair
    )
    
    # Create mint
    mint_keypair = Keypair()
    mint_response = await token.create_mint(
        mint=mint_keypair,
        mint_authority=authority_keypair.pubkey(),
        decimals=9,
        freeze_authority=authority_keypair.pubkey()
    )
    
    token_mint = mint_keypair.pubkey()
    print(f"Token mint created: {token_mint}")
    
    # Create associated token account for authority
    authority_token_account = await token.create_associated_token_account(
        owner=authority_keypair.pubkey(),
        mint=token_mint
    )
    print(f"Authority token account: {authority_token_account}")
    
    # Mint initial supply (100M tokens)
    initial_supply = 100_000_000 * (10 ** 9)  # 100M tokens with 9 decimals
    mint_to_response = await token.mint_to(
        dest=authority_token_account,
        mint_authority=authority_keypair,
        amount=initial_supply
    )
    print(f"Minted {initial_supply / (10**9)} tokens to authority")
    
    # Print configuration for .env
    print("\n" + "="*50)
    print("Add these to your .env file:")
    print("="*50)
    print(f"SOLANA_PRIVATE_KEY={base58.b58encode(authority_keypair.secret()).decode()}")
    print(f"TOKEN_MINT_ADDRESS={token_mint}")
    print(f"SOLANA_RPC_URL=https://api.devnet.solana.com")
    print("="*50)
    
    # Save to file
    with open('.env.token.generated', 'w') as f:
        f.write(f"SOLANA_PRIVATE_KEY={base58.b58encode(authority_keypair.secret()).decode()}\n")
        f.write(f"TOKEN_MINT_ADDRESS={token_mint}\n")
        f.write(f"SOLANA_RPC_URL=https://api.devnet.solana.com\n")
    
    print(f"\nToken configuration saved to .env.token.generated")
    
    await client.close()

if __name__ == "__main__":
    asyncio.run(create_token())
EOF
check_success

print_section "Step 10: Creating Test Script"

# Create test script
cat > test_token_integration.py << 'EOF'
"""
Test script for token integration
"""
import asyncio
import os
from dotenv import load_dotenv
from services.solana_service import SolanaService

load_dotenv()

async def test_token_integration():
    """Test the token integration"""
    
    # Check environment variables
    rpc_url = os.getenv("SOLANA_RPC_URL")
    private_key = os.getenv("SOLANA_PRIVATE_KEY")
    token_mint = os.getenv("TOKEN_MINT_ADDRESS")
    
    if not all([rpc_url, private_key, token_mint]):
        print("❌ Missing environment variables. Please run create_token.py first.")
        return
    
    print("✅ Environment variables found")
    
    # Test Solana service
    try:
        service = SolanaService(rpc_url, private_key, token_mint)
        print("✅ Solana service initialized")
        
        # Test getting balance
        authority_address = service.authority.pubkey()
        balance = await service.get_token_balance(str(authority_address))
        print(f"✅ Authority wallet balance: {balance} tokens")
        
        # Test transaction history
        history = await service.get_transaction_history(str(authority_address), limit=5)
        print(f"✅ Transaction history: {len(history)} transactions")
        
        await service.close()
        print("✅ All tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_token_integration())
EOF
check_success

print_section "Setup Complete!"

echo -e "${GREEN}✅ Token backend integration setup complete!${NC}"
echo
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Run the token creation script:"
echo "   python create_token.py"
echo
echo "2. Add the generated environment variables to your .env file"
echo
echo "3. Test the integration:"
echo "   python test_token_integration.py"
echo
echo "4. Manually merge the token fields into your existing User model"
echo "   (Check models/user.py.backup for your original file)"
echo
echo "5. Update your database indices:"
echo "   Add token collections to your database service"
echo
echo "6. Test the API endpoints:"
echo "   curl http://localhost:8000/api/token/balance/YOUR_WALLET_ADDRESS"
echo
echo -e "${BLUE}Files created:${NC}"
echo "- services/solana_service.py"
echo "- models/token.py"
echo "- routes/token.py"
echo "- create_token.py"
echo "- test_token_integration.py"
echo "- .env.token.template"
echo "- .env.token.generated (after running create_token.py)"
echo
echo -e "${BLUE}Files modified:${NC}"
echo "- requirements.txt (backup: requirements.txt.backup)"
echo "- config.py (backup: config.py.backup)"
echo "- main.py (backup: main.py.backup)"
echo "- models/user.py (backup: models/user.py.backup)"
echo
echo -e "${YELLOW}Ready to create your token on Solana devnet!${NC}"
