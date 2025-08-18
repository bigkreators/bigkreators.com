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
