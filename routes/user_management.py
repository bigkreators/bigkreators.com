# File: routes/user_management.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import HTMLResponse, JSONResponse
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from bson import ObjectId
import logging
from pydantic import BaseModel

from dependencies.auth import get_current_admin, get_current_user
from dependencies.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter()

# Pydantic models for request validation
class UserBlockRequest(BaseModel):
    reason: str
    duration_hours: Optional[int] = None  # None = indefinite block
    block_type: str = "full"  # "full", "edit_only", "comment_only"
    admin_note: Optional[str] = None

class UserUnblockRequest(BaseModel):
    reason: str
    admin_note: Optional[str] = None

# Block types and their permissions
BLOCK_TYPES = {
    "full": {
        "can_login": False,
        "can_edit": False, 
        "can_comment": False,
        "can_propose": False,
        "can_vote": False,
        "description": "Complete account suspension"
    },
    "edit_only": {
        "can_login": True,
        "can_edit": False,
        "can_comment": True,
        "can_propose": False,
        "can_vote": True,
        "description": "Cannot edit articles or propose changes"
    },
    "comment_only": {
        "can_login": True,
        "can_edit": True,
        "can_comment": False,
        "can_propose": True,
        "can_vote": True,
        "description": "Cannot post comments or participate in discussions"
    }
}

@router.post("/api/admin/users/{user_id}/block")
async def block_user(
    user_id: str,
    block_request: UserBlockRequest,
    current_user: Dict[str, Any] = Depends(get_current_admin),
    db = Depends(get_db)
):
    """
    Block a user with specified restrictions and duration.
    """
    try:
        # Validate user ID
        if not ObjectId.is_valid(user_id):
            raise HTTPException(status_code=400, detail="Invalid user ID")
        
        # Check if user exists
        user = await db["users"].find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Prevent blocking self
        if str(user["_id"]) == str(current_user["_id"]):
            raise HTTPException(status_code=400, detail="Cannot block yourself")
        
        # Prevent blocking other admins (unless super admin)
        if user.get("role") == "admin" and current_user.get("role") != "super_admin":
            raise HTTPException(status_code=403, detail="Cannot block another admin")
        
        # Validate block type
        if block_request.block_type not in BLOCK_TYPES:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid block type. Must be one of: {list(BLOCK_TYPES.keys())}"
            )
        
        # Calculate expiration if duration specified
        expires_at = None
        if block_request.duration_hours:
            expires_at = datetime.utcnow() + timedelta(hours=block_request.duration_hours)
        
        # Create block record
        block_data = {
            "user_id": ObjectId(user_id),
            "username": user["username"],
            "blocked_by": current_user["_id"],
            "blocked_by_username": current_user["username"],
            "block_type": block_request.block_type,
            "reason": block_request.reason,
            "admin_note": block_request.admin_note,
            "created_at": datetime.utcnow(),
            "expires_at": expires_at,
            "is_active": True
        }
        
        # Insert block record
        block_result = await db["user_blocks"].insert_one(block_data)
        
        # Update user status
        user_update = {
            "isBlocked": True,
            "blockType": block_request.block_type,
            "blockReason": block_request.reason,
            "blockedAt": datetime.utcnow(),
            "blockedBy": current_user["_id"],
            "blockExpiresAt": expires_at
        }
        
        # If full block, also deactivate account
        if block_request.block_type == "full":
            user_update["isActive"] = False
        
        await db["users"].update_one(
            {"_id": ObjectId(user_id)},
            {"$set": user_update}
        )
        
        # Log the action
        logger.warning(
            f"User blocked: {user['username']} (ID: {user_id}) by {current_user['username']} "
            f"(Block type: {block_request.block_type}, Duration: {block_request.duration_hours or 'indefinite'} hours, "
            f"Reason: {block_request.reason})"
        )
        
        # Send notification to blocked user (if they can still login)
        if block_request.block_type != "full":
            notification_data = {
                "user_id": ObjectId(user_id),
                "type": "account_restricted",
                "title": f"Account Restricted - {BLOCK_TYPES[block_request.block_type]['description']}",
                "message": f"Your account has been restricted. Reason: {block_request.reason}",
                "created_at": datetime.utcnow(),
                "read": False
            }
            await db["notifications"].insert_one(notification_data)
        
        return {
            "message": f"User {user['username']} blocked successfully",
            "block_id": str(block_result.inserted_id),
            "block_type": block_request.block_type,
            "expires_at": expires_at.isoformat() if expires_at else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error blocking user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to block user: {str(e)}"
        )

@router.post("/api/admin/users/{user_id}/unblock")
async def unblock_user(
    user_id: str,
    unblock_request: UserUnblockRequest,
    current_user: Dict[str, Any] = Depends(get_current_admin),
    db = Depends(get_db)
):
    """
    Unblock a user and restore their access.
    """
    try:
        # Validate user ID
        if not ObjectId.is_valid(user_id):
            raise HTTPException(status_code=400, detail="Invalid user ID")
        
        # Check if user exists
        user = await db["users"].find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check if user is actually blocked
        if not user.get("isBlocked"):
            raise HTTPException(status_code=400, detail="User is not currently blocked")
        
        # Deactivate current block records
        await db["user_blocks"].update_many(
            {"user_id": ObjectId(user_id), "is_active": True},
            {
                "$set": {
                    "is_active": False,
                    "unblocked_at": datetime.utcnow(),
                    "unblocked_by": current_user["_id"],
                    "unblocked_by_username": current_user["username"],
                    "unblock_reason": unblock_request.reason,
                    "unblock_admin_note": unblock_request.admin_note
                }
            }
        )
        
        # Restore user account
        user_update = {
            "isBlocked": False,
            "isActive": True,  # Restore access
            "blockType": None,
            "blockReason": None,
            "blockedAt": None,
            "blockedBy": None,
            "blockExpiresAt": None,
            "unblockedAt": datetime.utcnow(),
            "unblockedBy": current_user["_id"]
        }
        
        await db["users"].update_one(
            {"_id": ObjectId(user_id)},
            {"$set": user_update}
        )
        
        # Log the action
        logger.info(
            f"User unblocked: {user['username']} (ID: {user_id}) by {current_user['username']} "
            f"(Reason: {unblock_request.reason})"
        )
        
        # Send notification to user
        notification_data = {
            "user_id": ObjectId(user_id),
            "type": "account_restored",
            "title": "Account Access Restored",
            "message": f"Your account restrictions have been lifted. Reason: {unblock_request.reason}",
            "created_at": datetime.utcnow(),
            "read": False
        }
        await db["notifications"].insert_one(notification_data)
        
        return {
            "message": f"User {user['username']} unblocked successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unblocking user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to unblock user: {str(e)}"
        )

@router.get("/api/admin/users/{user_id}/blocks")
async def get_user_block_history(
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_admin),
    db = Depends(get_db)
):
    """
    Get block history for a specific user.
    """
    try:
        if not ObjectId.is_valid(user_id):
            raise HTTPException(status_code=400, detail="Invalid user ID")
        
        # Get block history
        blocks = await db["user_blocks"].find(
            {"user_id": ObjectId(user_id)},
            {"_id": 1, "block_type": 1, "reason": 1, "admin_note": 1, 
             "blocked_by_username": 1, "created_at": 1, "expires_at": 1,
             "is_active": 1, "unblocked_at": 1, "unblocked_by_username": 1,
             "unblock_reason": 1, "unblock_admin_note": 1}
        ).sort("created_at", -1).to_list(100)
        
        # Convert ObjectIds to strings
        for block in blocks:
            block["_id"] = str(block["_id"])
            if block.get("expires_at"):
                block["expires_at"] = block["expires_at"].isoformat()
            if block.get("created_at"):
                block["created_at"] = block["created_at"].isoformat()
            if block.get("unblocked_at"):
                block["unblocked_at"] = block["unblocked_at"].isoformat()
        
        return {"blocks": blocks, "total": len(blocks)}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting block history: {e}")
        raise HTTPException(status_code=500, detail="Failed to get block history")

@router.get("/api/admin/blocks/active")
async def get_active_blocks(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    block_type: Optional[str] = Query(None),
    current_user: Dict[str, Any] = Depends(get_current_admin),
    db = Depends(get_db)
):
    """
    Get all currently active user blocks.
    """
    try:
        # Build query
        query = {"is_active": True}
        if block_type and block_type in BLOCK_TYPES:
            query["block_type"] = block_type
        
        # Get total count
        total = await db["user_blocks"].count_documents(query)
        
        # Get active blocks
        blocks = await db["user_blocks"].find(
            query,
            {"_id": 1, "username": 1, "user_id": 1, "block_type": 1, "reason": 1,
             "blocked_by_username": 1, "created_at": 1, "expires_at": 1}
        ).sort("created_at", -1).skip(offset).limit(limit).to_list(limit)
        
        # Convert ObjectIds and dates to strings
        for block in blocks:
            block["_id"] = str(block["_id"])
            block["user_id"] = str(block["user_id"])
            if block.get("expires_at"):
                block["expires_at"] = block["expires_at"].isoformat()
            if block.get("created_at"):
                block["created_at"] = block["created_at"].isoformat()
        
        return {
            "blocks": blocks,
            "total": total,
            "limit": limit,
            "offset": offset,
            "block_types": BLOCK_TYPES
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting active blocks: {e}")
        raise HTTPException(status_code=500, detail="Failed to get active blocks")

@router.get("/api/user/block-status")
async def check_user_block_status(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Check if the current user is blocked and what restrictions apply.
    This can be used by the frontend to adjust UI based on user permissions.
    """
    try:
        user_id = current_user["_id"]
        
        # Check if user is blocked
        user_data = await db["users"].find_one(
            {"_id": ObjectId(user_id)},
            {"isBlocked": 1, "blockType": 1, "blockReason": 1, "blockExpiresAt": 1}
        )
        
        if not user_data.get("isBlocked"):
            return {
                "is_blocked": False,
                "permissions": {
                    "can_login": True,
                    "can_edit": True,
                    "can_comment": True,
                    "can_propose": True,
                    "can_vote": True
                }
            }
        
        block_type = user_data.get("blockType", "full")
        expires_at = user_data.get("blockExpiresAt")
        
        # Check if block has expired
        if expires_at and datetime.utcnow() >= expires_at:
            # Auto-unblock expired blocks
            await db["users"].update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$set": {
                        "isBlocked": False,
                        "isActive": True,
                        "blockType": None,
                        "blockReason": None,
                        "blockedAt": None,
                        "blockedBy": None,
                        "blockExpiresAt": None
                    }
                }
            )
            
            # Deactivate block records
            await db["user_blocks"].update_many(
                {"user_id": ObjectId(user_id), "is_active": True},
                {"$set": {"is_active": False, "unblocked_at": datetime.utcnow()}}
            )
            
            return {
                "is_blocked": False,
                "permissions": {
                    "can_login": True,
                    "can_edit": True,
                    "can_comment": True,
                    "can_propose": True,
                    "can_vote": True
                }
            }
        
        return {
            "is_blocked": True,
            "block_type": block_type,
            "block_reason": user_data.get("blockReason"),
            "expires_at": expires_at.isoformat() if expires_at else None,
            "permissions": BLOCK_TYPES.get(block_type, BLOCK_TYPES["full"])
        }
        
    except Exception as e:
        logger.error(f"Error checking block status: {e}")
        raise HTTPException(status_code=500, detail="Failed to check block status")

# Utility function to check if user can perform specific actions
async def check_user_permission(user_id: str, action: str, db) -> bool:
    """
    Check if a user has permission to perform a specific action.
    
    Args:
        user_id: User ID to check
        action: Action to check (login, edit, comment, propose, vote)
        db: Database connection
    
    Returns:
        bool: True if user has permission, False otherwise
    """
    try:
        user = await db["users"].find_one(
            {"_id": ObjectId(user_id)},
            {"isBlocked": 1, "blockType": 1, "blockExpiresAt": 1}
        )
        
        if not user or not user.get("isBlocked"):
            return True
        
        # Check if block has expired
        expires_at = user.get("blockExpiresAt")
        if expires_at and datetime.utcnow() >= expires_at:
            return True
        
        block_type = user.get("blockType", "full")
        permissions = BLOCK_TYPES.get(block_type, BLOCK_TYPES["full"])
        
        return permissions.get(f"can_{action}", False)
        
    except Exception as e:
        logger.error(f"Error checking user permission: {e}")
        return False
