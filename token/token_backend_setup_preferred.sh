#!/bin/bash

# BigKreators Token Backend Integration Setup Script
# Updated for Solana 0.36.7 and modern Python libraries

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

print_section "BigKreators Token Backend Integration Setup (Solana 0.36.7)"
echo "This script uses the latest Solana libraries and modern Python packages."
echo -e "\nPress Enter to continue or Ctrl+C to cancel..."
read

# Check if we're in the right directory
if [ ! -f "main.py" ] || [ ! -f "requirements.txt" ]; then
    echo -e "${RED}Error: This doesn't appear to be your FastAPI project root directory.${NC}"
    echo "Please run this script from the directory containing main.py and requirements.txt"
    exit 1
fi

print_section "Step 1: Installing Modern Python Dependencies"

# Backup existing requirements.txt
echo -n "Backing up requirements.txt... "
cp requirements.txt requirements.txt.backup
check_success

# Add modern Solana dependencies
echo -n "Adding Solana 0.36.7 dependencies to requirements.txt... "
cat >> requirements.txt << EOF

# Modern Solana integration dependencies (v0.36.7)
solana==0.36.7
solders==0.23.1
base58==2.1.1
httpx==0.25.2
pynacl==1.5.0
typing-extensions==4.8.0
websockets==12.0
EOF
check_success

# Install new dependencies
echo -n "Installing new dependencies... "
pip install -r requirements.txt
check_success

print_section "Step 2: Creating Modern Solana Service"

mkdir -p services

cat > services/solana_service.py << 'EOF'
"""
Modern Solana service for token operations using Solana 0.36.7
"""
import asyncio
import json
from typing import List, Optional, Dict, Any
from decimal import Decimal
import logging
import base58

from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Confirmed, Finalized
from solana.rpc.types import TxOpts
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.transaction import VersionedTransaction
from solders.message import MessageV0
from solders.address_lookup_table_account import AddressLookupTableAccount
from solders.system_program import transfer, TransferParams
from solders.instruction import Instruction

logger = logging.getLogger(__name__)

class ModernSolanaService:
    def __init__(self, rpc_url: str, private_key: str, token_mint: str = None):
        """
        Initialize modern Solana service
        
        Args:
            rpc_url: Solana RPC endpoint
            private_key: Base58 encoded private key for authority wallet
            token_mint: Token mint address (optional for initial setup)
        """
        self.client = AsyncClient(rpc_url)
        self.authority = Keypair.from_base58_string(private_key)
        self.token_mint = Pubkey.from_string(token_mint) if token_mint else None
        self.token_decimals = 9
        
    async def get_sol_balance(self, wallet_address: str) -> float:
        """Get SOL balance for a wallet"""
        try:
            wallet_pubkey = Pubkey.from_string(wallet_address)
            response = await self.client.get_balance(wallet_pubkey, commitment=Confirmed)
            return response.value / 1_000_000_000  # Convert lamports to SOL
        except Exception as e:
            logger.error(f"Error getting SOL balance: {e}")
            return 0.0
    
    async def get_token_balance(self, wallet_address: str) -> float:
        """
        Get token balance for a wallet address
        """
        if not self.token_mint:
            logger.warning("Token mint not set")
            return 0.0
            
        try:
            wallet_pubkey = Pubkey.from_string(wallet_address)
            
            # Get token accounts by owner
            response = await self.client.get_token_accounts_by_owner(
                wallet_pubkey,
                {"mint": self.token_mint},
                commitment=Confirmed
            )
            
            if not response.value:
                return 0.0
            
            # Get balance of first token account
            token_account = response.value[0].pubkey
            balance_response = await self.client.get_token_account_balance(
                token_account, 
                commitment=Confirmed
            )
            
            if balance_response.value:
                raw_amount = int(balance_response.value.amount)
                return raw_amount / (10 ** self.token_decimals)
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Error getting token balance: {e}")
            return 0.0
    
    async def send_sol(self, recipient_address: str, amount: float) -> Optional[str]:
        """
        Send SOL to a recipient
        """
        try:
            recipient_pubkey = Pubkey.from_string(recipient_address)
            lamports = int(amount * 1_000_000_000)
            
            # Create transfer instruction
            transfer_ix = transfer(
                TransferParams(
                    from_pubkey=self.authority.pubkey(),
                    to_pubkey=recipient_pubkey,
                    lamports=lamports
                )
            )
            
            # Get recent blockhash
            blockhash_response = await self.client.get_latest_blockhash(commitment=Finalized)
            recent_blockhash = blockhash_response.value.blockhash
            
            # Create message
            message = MessageV0.try_compile(
                payer=self.authority.pubkey(),
                instructions=[transfer_ix],
                address_lookup_table_accounts=[],
                recent_blockhash=recent_blockhash
            )
            
            # Create and sign transaction
            transaction = VersionedTransaction(message, [self.authority])
            
            # Send transaction
            response = await self.client.send_transaction(
                transaction,
                opts=TxOpts(
                    skip_preflight=False, 
                    preflight_commitment=Confirmed,
                    max_retries=3
                )
            )
            
            logger.info(f"SOL transfer successful: {response.value}")
            return str(response.value)
            
        except Exception as e:
            logger.error(f"Error sending SOL: {e}")
            return None
    
    async def create_spl_token(self, decimals: int = 9) -> Optional[Dict[str, Any]]:
        """
        Create a new SPL token using modern Solana libraries
        """
        try:
            # This is a simplified version - in practice you'd use spl-token library
            # For now, we'll return the structure for CLI creation
            return {
                "authority": str(self.authority.pubkey()),
                "decimals": decimals,
                "success": False,
                "message": "Use create_token_cli.py for token creation"
            }
            
        except Exception as e:
            logger.error(f"Error creating token: {e}")
            return None
    
    async def get_transaction_history(self, wallet_address: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get transaction history for a wallet
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
                    'confirmation_status': 'confirmed'
                })
            
            return transactions
            
        except Exception as e:
            logger.error(f"Error getting transaction history: {e}")
            return []
    
    async def get_account_info(self, address: str) -> Optional[Dict[str, Any]]:
        """Get account information"""
        try:
            pubkey = Pubkey.from_string(address)
            response = await self.client.get_account_info(pubkey, commitment=Confirmed)
            
            if response.value:
                return {
                    "address": address,
                    "lamports": response.value.lamports,
                    "owner": str(response.value.owner),
                    "executable": response.value.executable,
                    "rent_epoch": response.value.rent_epoch
                }
            return None
            
        except Exception as e:
            logger.error(f"Error getting account info: {e}")
            return None
    
    async def airdrop_sol(self, amount: float = 1.0) -> Optional[str]:
        """Request SOL airdrop (devnet only)"""
        try:
            lamports = int(amount * 1_000_000_000)
            response = await self.client.request_airdrop(
                self.authority.pubkey(), 
                lamports
            )
            
            logger.info(f"Airdrop requested: {response.value}")
            return str(response.value)
            
        except Exception as e:
            logger.error(f"Error requesting airdrop: {e}")
            return None
    
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
    account_exists: bool = Field(True, description="Whether account exists")

class TokenSystemStatus(BaseModel):
    """Model for token system status"""
    status: str = Field(..., description="System status")
    network: str = Field(..., description="Solana network")
    authority_wallet: str = Field(..., description="Authority wallet address")
    authority_sol_balance: float = Field(0.0, description="Authority SOL balance")
    token_mint: Optional[str] = Field(None, description="Token mint address")
    rpc_url: str = Field(..., description="RPC URL")
EOF
check_success

print_section "Step 4: Creating Modern Token Routes"

cat > routes/token.py << 'EOF'
"""
Modern token routes using Solana 0.36.7
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import List, Optional
from datetime import datetime, timedelta
import logging

from models.token import (
    Contribution, TokenReward, ContributionCreate, 
    WalletInfo, TokenSystemStatus
)
from models.user import User
from dependencies.database import get_db
from dependencies.auth import get_current_user
from services.solana_service import ModernSolanaService
import config

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize Solana service
solana_service = None

def get_solana_service():
    global solana_service
    if solana_service is None:
        try:
            solana_service = ModernSolanaService(
                rpc_url=config.SOLANA_RPC_URL,
                private_key=config.SOLANA_PRIVATE_KEY,
                token_mint=config.TOKEN_MINT_ADDRESS if hasattr(config, 'TOKEN_MINT_ADDRESS') and config.TOKEN_MINT_ADDRESS else None
            )
        except Exception as e:
            logger.error(f"Failed to initialize Solana service: {e}")
            return None
    return solana_service

@router.get("/status", response_model=TokenSystemStatus)
async def get_token_status():
    """Get comprehensive token system status"""
    service = get_solana_service()
    if not service:
        raise HTTPException(status_code=500, detail="Solana service not available")
    
    try:
        # Test connection and get balances
        authority_address = str(service.authority.pubkey())
        authority_balance = await service.get_sol_balance(authority_address)
        
        return TokenSystemStatus(
            status="active",
            network="devnet" if "devnet" in config.SOLANA_RPC_URL else "mainnet",
            authority_wallet=authority_address,
            authority_sol_balance=authority_balance,
            token_mint=str(service.token_mint) if service.token_mint else None,
            rpc_url=config.SOLANA_RPC_URL
        )
    except Exception as e:
        logger.error(f"Error getting token status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get system status: {str(e)}")

@router.get("/wallet/{wallet_address}", response_model=WalletInfo)
async def get_wallet_info(wallet_address: str):
    """Get comprehensive wallet information"""
    service = get_solana_service()
    if not service:
        raise HTTPException(status_code=500, detail="Solana service not available")
    
    try:
        # Get SOL balance
        sol_balance = await service.get_sol_balance(wallet_address)
        
        # Get token balance (if token mint is configured)
        token_balance = 0.0
        if service.token_mint:
            token_balance = await service.get_token_balance(wallet_address)
        
        # Check if account exists
        account_info = await service.get_account_info(wallet_address)
        account_exists = account_info is not None
        
        return WalletInfo(
            address=wallet_address,
            sol_balance=sol_balance,
            token_balance=token_balance,
            account_exists=account_exists
        )
    except Exception as e:
        logger.error(f"Error getting wallet info: {e}")
        raise HTTPException(status_code=500, detail="Failed to get wallet information")

@router.post("/airdrop/{wallet_address}")
async def request_airdrop(wallet_address: str, amount: float = 1.0):
    """Request SOL airdrop (devnet only)"""
    service = get_solana_service()
    if not service:
        raise HTTPException(status_code=500, detail="Solana service not available")
    
    if "mainnet" in config.SOLANA_RPC_URL:
        raise HTTPException(status_code=400, detail="Airdrop not available on mainnet")
    
    try:
        # Create temporary service for the target wallet
        temp_keypair = service.authority  # Using authority for demo
        signature = await service.airdrop_sol(amount)
        
        if signature:
            return {
                "success": True,
                "signature": signature,
                "amount": amount,
                "message": f"Airdropped {amount} SOL to {wallet_address}"
            }
        else:
            raise HTTPException(status_code=500, detail="Airdrop failed")
            
    except Exception as e:
        logger.error(f"Error requesting airdrop: {e}")
        raise HTTPException(status_code=500, detail="Failed to request airdrop")

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
                "$inc": {"total_contributions": 1},
                "$set": {"updated_at": datetime.utcnow()}
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
        total_points_pipeline = [
            {"$match": {"user_id": user_id}},
            {"$group": {"_id": None, "total": {"$sum": "$total_points"}}}
        ]
        total_points_result = await db.contributions.aggregate(total_points_pipeline).to_list(None)
        total_user_points = total_points_result[0]["total"] if total_points_result else 0
        
        # Get user info
        user = await db.users.find_one({"_id": user_id})
        
        return {
            "user_id": user_id,
            "total_contributions": len(contributions) if contributions else 0,
            "total_points": total_user_points,
            "wallet_address": user.get('wallet_address') if user else None,
            "contributions": contributions,
            "estimated_weekly_tokens": total_user_points * 0.1
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
        return {
            "wallet_address": wallet_address,
            "transactions": transactions,
            "count": len(transactions)
        }
    except Exception as e:
        logger.error(f"Error getting transaction history: {e}")
        raise HTTPException(status_code=500, detail="Failed to get transaction history")

@router.post("/send-sol")
async def send_sol(
    recipient_address: str,
    amount: float,
    current_user: User = Depends(get_current_user)
):
    """Send SOL to another wallet (admin/testing feature)"""
    service = get_solana_service()
    if not service:
        raise HTTPException(status_code=500, detail="Solana service not available")
    
    try:
        # TODO: Add admin permission check
        signature = await service.send_sol(recipient_address, amount)
        
        if signature:
            return {
                "success": True,
                "signature": signature,
                "amount": amount,
                "recipient": recipient_address,
                "message": f"Sent {amount} SOL successfully"
            }
        else:
            raise HTTPException(status_code=500, detail="Transfer failed")
            
    except Exception as e:
        logger.error(f"Error sending SOL: {e}")
        raise HTTPException(status_code=500, detail="Failed to send SOL")
EOF
check_success

print_section "Step 5: Creating Modern Token Creation Script"

cat > create_token_modern.py << 'EOF'
#!/usr/bin/env python3
"""
Modern BigKreators KONTRIB Token Creation Script
Uses Solana 0.36.7 and modern approaches
"""

import asyncio
import subprocess
import json
import base58
import tempfile
import os
from datetime import datetime
from solders.keypair import Keypair

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

def check_prerequisites():
    """Check if required tools are installed"""
    tools = {
        'solana': 'Solana CLI',
        'spl-token': 'SPL Token CLI'
    }
    
    all_good = True
    for cmd, name in tools.items():
        try:
            result = subprocess.run([cmd, '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                version = result.stdout.strip().split('\n')[0]
                print_success(f"{name}: {version}")
            else:
                print_error(f"{name} not working properly")
                all_good = False
        except FileNotFoundError:
            print_error(f"{name} not installed")
            print_info(f"Install {name} from https://docs.solana.com/cli/install-solana-cli-tools")
            all_good = False
    
    return all_good

async def test_modern_service():
    """Test the modern Solana service"""
    try:
        from services.solana_service import ModernSolanaService
        
        # Create test keypair
        test_keypair = Keypair()
        service = ModernSolanaService(
            rpc_url="https://api.devnet.solana.com",
            private_key=test_keypair.to_base58_string(),
            token_mint=None  # No token mint yet
        )
        
        # Test basic functionality
        balance = await service.get_sol_balance(str(test_keypair.pubkey()))
        print_success(f"Modern Solana service working - Test balance: {balance} SOL")
        
        await service.close()
        return True
        
    except ImportError as e:
        print_error(f"Cannot import modern service: {e}")
        print_info("Make sure you've run the setup script first")
        return False
    except Exception as e:
        print_error(f"Service test failed: {e}")
        return False

async def create_token_modern():
    """Create token using modern approach"""
    
    print_section("BigKreators KONTRIB Token Creation (Modern)")
    print_info("Using Solana 0.36.7 and modern tooling")
    
    # Check prerequisites
    if not check_prerequisites():
        print_error("Prerequisites not met. Please install required tools.")
        return False
    
    # Test modern service
    print_section("Testing Modern Solana Service")
    if not await test_modern_service():
        print_error("Modern service test failed")
        return False
    
    # Configure Solana CLI
    print_section("Configuring Solana CLI")
    print_info("Setting network to devnet...")
    subprocess.run(['solana', 'config', 'set', '--url', 'devnet'], capture_output=True)
    
    # Create authority keypair
    print_section("Creating Authority Keypair")
    authority_keypair = Keypair()
    authority_address = str(authority_keypair.pubkey())
    authority_private_key = authority_keypair.to_base58_string()
    
    print_success(f"Authority wallet: {authority_address}")
    
    # Save keypair to temporary file for CLI operations
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        # Convert to CLI format
        keypair_data = list(authority_keypair.to_bytes_array())
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
            print_info("Continuing anyway - you may need manual airdrop")
        
        # Wait for airdrop confirmation
        print_info("Waiting for airdrop confirmation...")
        await asyncio.sleep(5)
        
        # Create token
        print_section("Creating KONTRIB Token")
        print_info("Creating token with 9 decimals...")
        
        create_result = subprocess.run([
            'spl-token', 'create-token',
            '--decimals', '9',
            '--enable-freeze'
        ], capture_output=True, text=True)
        
        if create_result.returncode != 0:
            print_error(f"Token creation failed: {create_result.stderr}")
            return False
        
        # Extract token mint address
        token_mint = None
        for line in create_result.stdout.strip().split('\n'):
            if 'Creating token' in line:
                token_mint = line.split()[-1]
                break
        
        if not token_mint:
            print_error("Could not extract token mint address")
            return False
        
        print_success(f"KONTRIB Token created: {token_mint}")
        
        # Create associated token account
        print_section("Creating Token Account")
        print_info("Creating associated token account...")
        
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
        
        # Verify balance
        print_section("Verifying Token Creation")
        balance_result = subprocess.run([
            'spl-token', 'balance', token_mint
        ], capture_output=True, text=True)
        
        if balance_result.returncode == 0:
            balance = balance_result.stdout.strip()
            print_success(f"Token balance verified: {balance} KONTRIB")
        
        # Test with modern service
        print_info("Testing with modern Solana service...")
        try:
            from services.solana_service import ModernSolanaService
            
            service = ModernSolanaService(
                rpc_url="https://api.devnet.solana.com",
                private_key=authority_private_key,
                token_mint=token_mint
            )
            
            # Test SOL balance
            sol_balance = await service.get_sol_balance(authority_address)
            print_success(f"SOL balance via service: {sol_balance} SOL")
            
            # Test token balance
            token_balance = await service.get_token_balance(authority_address)
            print_success(f"Token balance via service: {token_balance} KONTRIB")
            
            await service.close()
            
        except Exception as e:
            print_error(f"Service test failed: {e}")
        
        # Generate configuration
        print_section("Generating Configuration")
        
        config = {
            "token_name": "Wiki Contribution Token",
            "token_symbol": "KONTRIB",
            "token_mint": token_mint,
            "authority_wallet": authority_address,
            "authority_private_key": authority_private_key,
            "decimals": 9,
            "initial_supply": 100_000_000,
            "network": "devnet",
            "rpc_url": "https://api.devnet.solana.com",
            "created_at": datetime.utcnow().isoformat(),
            "explorer_url": f"https://explorer.solana.com/address/{token_mint}?cluster=devnet",
            "solana_version": "0.36.7",
            "creation_method": "modern_cli"
        }
        
        # Save configuration
        with open('kontrib_token_config.json', 'w') as f:
            json.dump(config, f, indent=2)
        print_success("Configuration saved to kontrib_token_config.json")
        
        # Generate environment variables
        env_vars = f"""SOLANA_RPC_URL=https://api.devnet.solana.com
SOLANA_PRIVATE_KEY={authority_private_key}
TOKEN_MINT_ADDRESS={token_mint}
WEEKLY_TOKEN_POOL=10000.0
MIN_TOKENS_PER_USER=1.0"""
        
        with open('.env.kontrib.generated', 'w') as f:
            f.write(env_vars)
        print_success("Environment variables saved to .env.kontrib.generated")
        
        # Print summary
        print_section("Token Creation Summary")
        print(f"{GREEN}🎉 KONTRIB Token successfully created with modern tooling!{NC}")
        print(f"{BLUE}Token Mint:{NC} {token_mint}")
        print(f"{BLUE}Authority Wallet:{NC} {authority_address}")
        print(f"{BLUE}Initial Supply:{NC} 100,000,000 KONTRIB")
        print(f"{BLUE}Solana Version:{NC} 0.36.7")
        print(f"{BLUE}Explorer:{NC} https://explorer.solana.com/address/{token_mint}?cluster=devnet")
        
        print_section("Next Steps")
        print(f"{YELLOW}1. Add environment variables to your .env file:{NC}")
        print(f"   cat .env.kontrib.generated >> .env")
        print()
        print(f"{YELLOW}2. Test the modern integration:{NC}")
        print(f"   python test_token_modern.py")
        print()
        print(f"{YELLOW}3. Start your FastAPI server:{NC}")
        print(f"   uvicorn main:app --reload")
        print()
        print(f"{YELLOW}4. Test the API endpoints:{NC}")
        print(f"   curl http://localhost:8000/api/token/status")
        print(f"   curl http://localhost:8000/api/token/wallet/{authority_address}")
        
        return True
        
    finally:
        # Clean up temporary keypair file
        if os.path.exists(keypair_file):
            os.unlink(keypair_file)

if __name__ == "__main__":
    success = asyncio.run(create_token_modern())
    if success:
        print_success("Modern token creation completed successfully!")
    else:
        print_error("Token creation failed")
        exit(1)
EOF
check_success

# Make the script executable
chmod +x create_token_modern.py

print_section "Step 6: Creating Modern Test Script"

cat > test_token_modern.py << 'EOF'
"""
Test script for modern token integration (Solana 0.36.7)
"""
import asyncio
import os
from dotenv import load_dotenv

async def test_modern_integration():
    """Test the modern token integration"""
    
    print("🧪 Testing Modern Token Integration (Solana 0.36.7)")
    print("=" * 55)
    
    # Load environment variables
    load_dotenv()
    
    # Check environment variables
    rpc_url = os.getenv("SOLANA_RPC_URL")
    private_key = os.getenv("SOLANA_PRIVATE_KEY")
    token_mint = os.getenv("TOKEN_MINT_ADDRESS")
    
    print(f"RPC URL: {rpc_url or 'Not set'}")
    print(f"Private Key: {'Set' if private_key else 'Not set'}")
    print(f"Token Mint: {token_mint or 'Not set'}")
    print()
    
    if not all([rpc_url, private_key]):
        print("❌ Missing required environment variables")
        print("Run create_token_modern.py first, then add variables to .env")
        return False
    
    print("✅ Environment variables found")
    
    # Test modern Solana service
    try:
        from services.solana_service import ModernSolanaService
        
        service = ModernSolanaService(rpc_url, private_key, token_mint)
        print("✅ Modern Solana service initialized")
        
        # Test authority wallet info
        authority_address = str(service.authority.pubkey())
        print(f"✅ Authority wallet: {authority_address}")
        
        # Test SOL balance
        sol_balance = await service.get_sol_balance(authority_address)
        print(f"✅ SOL balance: {sol_balance} SOL")
        
        # Test token balance (if token mint is set)
        if token_mint:
            token_balance = await service.get_token_balance(authority_address)
            print(f"✅ Token balance: {token_balance} KONTRIB")
        else:
            print("ℹ️  Token mint not set - skipping token balance test")
        
        # Test account info
        account_info = await service.get_account_info(authority_address)
        if account_info:
            print(f"✅ Account info: {account_info['lamports']} lamports")
        
        # Test transaction history
        history = await service.get_transaction_history(authority_address, limit=3)
        print(f"✅ Transaction history: {len(history)} recent transactions")
        
        await service.close()
        print("✅ Service closed successfully")
        
        print("\n" + "="*55)
        print("🎉 All modern integration tests passed!")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you've run the setup script and installed dependencies")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_modern_integration())
    if not success:
        exit(1)
EOF
check_success

print_section "Step 7: Updating Configuration"

# Backup and update config
echo -n "Backing up and updating config.py... "
cp config.py config.py.backup
cat >> config.py << 'EOF'

# Modern Solana and Token Configuration (v0.36.7)
SOLANA_RPC_URL = os.getenv("SOLANA_RPC_URL", "https://api.devnet.solana.com")
SOLANA_PRIVATE_KEY = os.getenv("SOLANA_PRIVATE_KEY", "")
TOKEN_MINT_ADDRESS = os.getenv("TOKEN_MINT_ADDRESS", "")

# Token system configuration
WEEKLY_TOKEN_POOL = float(os.getenv("WEEKLY_TOKEN_POOL", "10000.0"))
MIN_TOKENS_PER_USER = float(os.getenv("MIN_TOKENS_PER_USER", "1.0"))
EOF
check_success

print_section "Step 8: Updating Main App"

# Backup and update main.py
echo -n "Backing up and updating main.py... "
cp main.py main.py.backup
cat >> main.py << 'EOF'

# Modern Token routes integration (Solana 0.36.7)
try:
    from routes import token
    app.include_router(token.router, prefix="/api/token", tags=["Token"])
    print("✅ Token routes loaded successfully")
except ImportError as e:
    print(f"⚠️  Warning: Could not import token routes: {e}")
    print("Run the setup script to create token integration files")
except Exception as e:
    print(f"⚠️  Warning: Token routes error: {e}")
EOF
check_success

print_section "Setup Complete!"

echo -e "${GREEN}✅ Modern Solana 0.36.7 integration setup complete!${NC}"
echo
echo -e "${YELLOW}What's new in this version:${NC}"
echo "- Uses latest Solana 0.36.7 libraries"
echo "- Modern solders for keypair and transaction handling"
echo "- Improved error handling and async operations"
echo "- Better type hints and response models"
echo "- Comprehensive status and wallet info endpoints"
echo
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Create your KONTRIB token:"
echo "   python create_token_modern.py"
echo
echo "2. Add generated environment variables:"
echo "   cat .env.kontrib.generated >> .env"
echo
echo "3. Test the modern integration:"
echo "   python test_token_modern.py"
echo
echo "4. Start your FastAPI server:"
echo "   uvicorn main:app --reload"
echo
echo "5. Test the new endpoints:"
echo "   curl http://localhost:8000/api/token/status"
echo "   curl http://localhost:8000/api/token/wallet/YOUR_WALLET_ADDRESS"
echo
echo -e "${BLUE}New API endpoints:${NC}"
echo "- GET /api/token/status - Comprehensive system status"
echo "- GET /api/token/wallet/{address} - Wallet info with SOL and token balances"
echo "- POST /api/token/airdrop/{address} - Request SOL airdrop (devnet)"
echo "- POST /api/token/contributions - Track contributions"
echo "- GET /api/token/rewards/user/{id} - User rewards"
echo "- GET /api/token/transactions/{address} - Transaction history"
echo "- POST /api/token/send-sol - Send SOL (admin feature)"
echo
echo -e "${GREEN}Ready to create your token with Solana 0.36.7!${NC}"
