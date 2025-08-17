# File: pages/crypto_admin.py

"""
Crypto Admin page routes for managing token system, rewards, and blockchain operations.
Self-contained version that doesn't rely on external admin functions.
"""
from fastapi import APIRouter, Request, Depends, Query, HTTPException
from fastapi.responses import HTMLResponse
from typing import Dict, Any, Optional
import logging
from datetime import datetime, timedelta

from dependencies import get_db, get_cache
from dependencies.auth import get_current_admin  # Use the standard auth dependency
import config

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/admin/crypto", response_class=HTMLResponse)
async def crypto_dashboard_page(
    request: Request,
    db=Depends(get_db),
    cache=Depends(get_cache)
):
    """
    Render the crypto administration dashboard.
    """
    templates = request.app.state.templates
    
    # Check admin authentication using standard method
    try:
        # Try to get token from cookie or header
        token = request.cookies.get("token")
        if not token:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.replace("Bearer ", "")
        
        if not token:
            return templates.TemplateResponse(
                "login_required.html",
                {
                    "request": request,
                    "redirect_to": "/admin/crypto",
                    "active_page": "admin"
                }
            )
        
        # Verify admin user
        from dependencies.auth import get_current_user
        admin_user = await get_current_user(token=token, db=db)
        
        if not admin_user or admin_user.get("role") != "admin":
            return templates.TemplateResponse(
                "login_required.html",
                {
                    "request": request,
                    "redirect_to": "/admin/crypto",
                    "active_page": "admin",
                    "message": "Admin access required"
                }
            )
    except Exception as e:
        logger.error(f"Auth error: {e}")
        return templates.TemplateResponse(
            "login_required.html",
            {
                "request": request,
                "redirect_to": "/admin/crypto",
                "active_page": "admin"
            }
        )
    
    # Try to get crypto dashboard data from cache
    cache_key = "crypto_admin_dashboard"
    dashboard_data = await cache.get(cache_key)
    
    if not dashboard_data:
        # Initialize default data
        dashboard_data = {
            "token_status": {"status": "checking", "message": "Checking connection..."},
            "contributions": {
                "weekly_contributions": 0,
                "weekly_points": 0,
                "active_contributors": 0
            },
            "rewards": {
                "total_distributed": 0,
                "pending_distributions": 0,
                "failed_distributions": 0
            },
            "recent_transactions": [],
            "weekly_pool": 10000
        }
        
        # Try to fetch token system status
        try:
            from routes.token import get_solana_service
            service = get_solana_service()
            
            if service:
                # Get the authority public key properly
                if hasattr(service, 'authority'):
                    if hasattr(service.authority, 'public_key'):
                        authority_address = str(service.authority.public_key)
                    elif hasattr(service.authority, 'pubkey'):
                        authority_address = str(service.authority.pubkey())
                    else:
                        authority_address = "Unknown"
                else:
                    authority_address = "Unknown"
                
                # Try to get balance
                try:
                    sol_balance = await service.get_sol_balance(authority_address)
                except:
                    sol_balance = 0
                
                dashboard_data["token_status"] = {
                    "status": "active",
                    "network": "devnet" if "devnet" in config.SOLANA_RPC_URL else "mainnet",
                    "authority_wallet": authority_address,
                    "authority_sol_balance": sol_balance,
                    "token_mint": getattr(config, 'TOKEN_MINT_ADDRESS', None)
                }
            else:
                dashboard_data["token_status"] = {
                    "status": "offline",
                    "message": "Solana service not initialized"
                }
        except ImportError:
            dashboard_data["token_status"] = {
                "status": "error",
                "message": "Token routes not available. Please set up token integration."
            }
        except Exception as e:
            logger.error(f"Error fetching token status: {e}")
            dashboard_data["token_status"] = {
                "status": "error",
                "message": str(e)
            }
        
        # Fetch contribution statistics
        try:
            dashboard_data["contributions"] = await get_contribution_stats(db)
        except:
            pass
        
        # Fetch reward distribution stats
        try:
            dashboard_data["rewards"] = await get_rewards_stats(db)
        except:
            pass
        
        # Fetch recent transactions
        try:
            dashboard_data["recent_transactions"] = await get_recent_transactions(db)
        except:
            pass
        
        # Get weekly pool from config
        dashboard_data["weekly_pool"] = getattr(config, 'WEEKLY_TOKEN_POOL', 10000)
        
        # Cache for 2 minutes
        await cache.set(cache_key, dashboard_data, 120)
    
    return templates.TemplateResponse(
        "crypto_admin_dashboard.html",
        {
            "request": request,
            "current_user": admin_user,
            "active_page": "admin",
            "dashboard_data": dashboard_data
        }
    )

@router.get("/admin/crypto/contributions", response_class=HTMLResponse)
async def contributions_management_page(
    request: Request,
    user_id: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db=Depends(get_db)
):
    """
    Manage user contributions and point calculations.
    """
    templates = request.app.state.templates
    
    # Check admin authentication
    try:
        token = request.cookies.get("token") or None
        if not token:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.replace("Bearer ", "")
        
        if not token:
            return templates.TemplateResponse(
                "login_required.html",
                {
                    "request": request,
                    "redirect_to": "/admin/crypto/contributions",
                    "active_page": "admin"
                }
            )
        
        from dependencies.auth import get_current_user
        admin_user = await get_current_user(token=token, db=db)
        
        if not admin_user or admin_user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")
            
    except:
        return templates.TemplateResponse(
            "login_required.html",
            {
                "request": request,
                "redirect_to": "/admin/crypto/contributions",
                "active_page": "admin"
            }
        )
    
    # Build query filters
    query = {}
    if user_id:
        query["user_id"] = user_id
    if status:
        query["status"] = status
    
    # Initialize empty results
    contributions = []
    total_count = 0
    
    # Try to fetch contributions (check if collection exists)
    try:
        if "contributions" in await db.list_collection_names():
            contributions = await db.contributions.find(query)\
                .sort("created_at", -1)\
                .skip(skip)\
                .limit(limit)\
                .to_list(None)
            
            total_count = await db.contributions.count_documents(query)
            
            # Enrich with user data
            for contrib in contributions:
                user = await db.users.find_one({"_id": contrib["user_id"]})
                if user:
                    contrib["username"] = user.get("username", "Unknown")
                    contrib["wallet_address"] = user.get("wallet_address")
    except Exception as e:
        logger.warning(f"Could not fetch contributions: {e}")
    
    return templates.TemplateResponse(
        "crypto_contributions.html",
        {
            "request": request,
            "current_user": admin_user,
            "active_page": "admin",
            "contributions": contributions,
            "total_count": total_count,
            "skip": skip,
            "limit": limit,
            "filters": {"user_id": user_id, "status": status}
        }
    )

@router.get("/admin/crypto/rewards", response_class=HTMLResponse)
async def rewards_distribution_page(
    request: Request,
    week: Optional[str] = None,
    db=Depends(get_db)
):
    """
    Manage token reward distributions.
    """
    templates = request.app.state.templates
    
    # Check admin authentication
    try:
        token = request.cookies.get("token") or None
        if not token:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.replace("Bearer ", "")
        
        if not token:
            return templates.TemplateResponse(
                "login_required.html",
                {
                    "request": request,
                    "redirect_to": "/admin/crypto/rewards",
                    "active_page": "admin"
                }
            )
        
        from dependencies.auth import get_current_user
        admin_user = await get_current_user(token=token, db=db)
        
        if not admin_user or admin_user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")
            
    except:
        return templates.TemplateResponse(
            "login_required.html",
            {
                "request": request,
                "redirect_to": "/admin/crypto/rewards",
                "active_page": "admin"
            }
        )
    
    # Calculate week range
    if week:
        week_start = datetime.strptime(week, "%Y-%W-%w")
    else:
        now = datetime.utcnow()
        week_start = now - timedelta(days=now.weekday())
    
    week_end = week_start + timedelta(days=7)
    
    # Initialize empty results
    rewards = []
    stats = {
        "total_distributed": 0,
        "total_recipients": 0,
        "avg_reward": 0,
        "pending_rewards": 0,
        "weekly_pool": getattr(config, 'WEEKLY_TOKEN_POOL', 10000)
    }
    
    # Try to fetch rewards (check if collection exists)
    try:
        if "token_rewards" in await db.list_collection_names():
            rewards = await db.token_rewards.find({
                "week_start": {"$gte": week_start, "$lt": week_end}
            }).sort("token_amount", -1).to_list(None)
            
            # Calculate statistics
            if rewards:
                stats["total_distributed"] = sum(r.get("token_amount", 0) for r in rewards)
                stats["total_recipients"] = len(rewards)
                stats["avg_reward"] = stats["total_distributed"] / stats["total_recipients"] if stats["total_recipients"] > 0 else 0
            
            # Get pending distributions
            stats["pending_rewards"] = await db.token_rewards.count_documents({"status": "pending"})
            
            # Enrich with user data
            for reward in rewards:
                user = await db.users.find_one({"_id": reward["user_id"]})
                if user:
                    reward["username"] = user.get("username", "Unknown")
                    reward["wallet_address"] = user.get("wallet_address")
    except Exception as e:
        logger.warning(f"Could not fetch rewards: {e}")
    
    return templates.TemplateResponse(
        "crypto_rewards.html",
        {
            "request": request,
            "current_user": admin_user,
            "active_page": "admin",
            "rewards": rewards,
            "week_start": week_start,
            "week_end": week_end,
            "stats": stats
        }
    )

@router.get("/admin/crypto/wallets", response_class=HTMLResponse)
async def wallet_management_page(
    request: Request,
    search: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db=Depends(get_db)
):
    """
    Manage user wallets and balances.
    """
    templates = request.app.state.templates
    
    # Check admin authentication
    try:
        token = request.cookies.get("token") or None
        if not token:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.replace("Bearer ", "")
        
        if not token:
            return templates.TemplateResponse(
                "login_required.html",
                {
                    "request": request,
                    "redirect_to": "/admin/crypto/wallets",
                    "active_page": "admin"
                }
            )
        
        from dependencies.auth import get_current_user
        admin_user = await get_current_user(token=token, db=db)
        
        if not admin_user or admin_user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")
            
    except:
        return templates.TemplateResponse(
            "login_required.html",
            {
                "request": request,
                "redirect_to": "/admin/crypto/wallets",
                "active_page": "admin"
            }
        )
    
    # Build query
    query = {"wallet_address": {"$exists": True, "$ne": None}}
    if search:
        query["$or"] = [
            {"username": {"$regex": search, "$options": "i"}},
            {"wallet_address": {"$regex": search, "$options": "i"}}
        ]
    
    # Fetch users with wallets
    users_with_wallets = await db.users.find(query)\
        .skip(skip)\
        .limit(limit)\
        .to_list(None)
    
    # Get total count
    total_count = await db.users.count_documents(query)
    
    # Try to fetch wallet balances from Solana (optional)
    try:
        from routes.token import get_solana_service
        service = get_solana_service()
        
        if service:
            for user in users_with_wallets:
                wallet = user.get("wallet_address")
                if wallet:
                    try:
                        user["sol_balance"] = await service.get_sol_balance(wallet)
                        user["token_balance"] = await service.get_token_balance(wallet)
                    except:
                        user["sol_balance"] = 0
                        user["token_balance"] = 0
    except:
        # If token service not available, just show stored data
        for user in users_with_wallets:
            user["sol_balance"] = 0
            user["token_balance"] = 0
    
    # Get total tokens earned from rewards collection
    for user in users_with_wallets:
        try:
            if "token_rewards" in await db.list_collection_names():
                total_earned = await db.token_rewards.aggregate([
                    {"$match": {"user_id": str(user["_id"]), "status": "completed"}},
                    {"$group": {"_id": None, "total": {"$sum": "$token_amount"}}}
                ]).to_list(None)
                
                user["total_earned"] = total_earned[0]["total"] if total_earned else 0
            else:
                user["total_earned"] = 0
        except:
            user["total_earned"] = 0
    
    return templates.TemplateResponse(
        "crypto_wallets.html",
        {
            "request": request,
            "current_user": admin_user,
            "active_page": "admin",
            "users": users_with_wallets,
            "total_count": total_count,
            "skip": skip,
            "limit": limit,
            "search": search
        }
    )

# Helper functions

async def get_contribution_stats(db):
    """Get contribution statistics for dashboard."""
    now = datetime.utcnow()
    week_start = now - timedelta(days=now.weekday())
    
    stats = {
        "weekly_contributions": 0,
        "weekly_points": 0,
        "active_contributors": 0
    }
    
    try:
        # Check if contributions collection exists
        if "contributions" in await db.list_collection_names():
            # Total contributions this week
            stats["weekly_contributions"] = await db.contributions.count_documents({
                "created_at": {"$gte": week_start}
            })
            
            # Total points this week
            weekly_points = await db.contributions.aggregate([
                {"$match": {"created_at": {"$gte": week_start}}},
                {"$group": {"_id": None, "total": {"$sum": "$total_points"}}}
            ]).to_list(None)
            
            stats["weekly_points"] = weekly_points[0]["total"] if weekly_points else 0
            
            # Active contributors this week
            active_contributors = await db.contributions.distinct(
                "user_id",
                {"created_at": {"$gte": week_start}}
            )
            
            stats["active_contributors"] = len(active_contributors)
    except Exception as e:
        logger.warning(f"Could not get contribution stats: {e}")
    
    return stats

async def get_rewards_stats(db):
    """Get reward distribution statistics."""
    stats = {
        "total_distributed": 0,
        "pending_distributions": 0,
        "failed_distributions": 0
    }
    
    try:
        # Check if token_rewards collection exists
        if "token_rewards" in await db.list_collection_names():
            # Total tokens distributed
            total_distributed = await db.token_rewards.aggregate([
                {"$match": {"status": "completed"}},
                {"$group": {"_id": None, "total": {"$sum": "$token_amount"}}}
            ]).to_list(None)
            
            stats["total_distributed"] = total_distributed[0]["total"] if total_distributed else 0
            
            # Pending distributions
            stats["pending_distributions"] = await db.token_rewards.count_documents({"status": "pending"})
            
            # Failed distributions
            stats["failed_distributions"] = await db.token_rewards.count_documents({"status": "failed"})
    except Exception as e:
        logger.warning(f"Could not get reward stats: {e}")
    
    return stats

async def get_recent_transactions(db, limit=10):
    """Get recent token transactions."""
    transactions = []
    
    try:
        # Check if token_rewards collection exists
        if "token_rewards" in await db.list_collection_names():
            transactions = await db.token_rewards.find(
                {"transaction_signature": {"$exists": True, "$ne": None}}
            ).sort("created_at", -1).limit(limit).to_list(None)
    except Exception as e:
        logger.warning(f"Could not get recent transactions: {e}")
    
    return transactions