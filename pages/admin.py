# File: routes/admin.py
"""
Admin API routes for the Kryptopedia application.
"""
from fastapi import APIRouter, Depends, Path, Query, HTTPException, Body
from typing import Dict, Any, List, Optional
import logging
from bson import ObjectId
from datetime import datetime, timedelta

from dependencies import get_db, get_current_admin, get_cache
from models.user import UserUpdate

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/dashboard")
async def get_dashboard_stats(
    current_user: Dict[str, Any] = Depends(get_current_admin),
    db=Depends(get_db),
    cache=Depends(get_cache)
):
    """
    Get admin dashboard statistics.
    """
    try:
        # Try to get from cache first
        cache_key = "admin_dashboard_stats"
        cached_stats = await cache.get(cache_key)
        
        if cached_stats:
            return cached_stats
        
        # Calculate stats
        stats = {}
        
        # Article stats
        stats["articles"] = await db["articles"].count_documents({})
        stats["published_articles"] = await db["articles"].count_documents({"status": "published"})
        stats["draft_articles"] = await db["articles"].count_documents({"status": "draft"})
        stats["hidden_articles"] = await db["articles"].count_documents({"status": "hidden"})
        stats["archived_articles"] = await db["articles"].count_documents({"status": "archived"})
        
        # User stats
        stats["users"] = await db["users"].count_documents({})
        stats["admins"] = await db["users"].count_documents({"role": "admin"})
        stats["editors"] = await db["users"].count_documents({"role": "editor"})
        stats["regular_users"] = await db["users"].count_documents({"role": "user"})
        
        # Recent stats (last 7 days)
        one_week_ago = datetime.now() - timedelta(days=7)
        
        stats["new_users_week"] = await db["users"].count_documents({
            "joinDate": {"$gte": one_week_ago}
        })
        
        stats["new_articles_week"] = await db["articles"].count_documents({
            "createdAt": {"$gte": one_week_ago}
        })
        
        stats["edits_week"] = await db["revisions"].count_documents({
            "createdAt": {"$gte": one_week_ago}
        })
        
        stats["proposals_week"] = await db["proposals"].count_documents({
            "proposedAt": {"$gte": one_week_ago}
        })
        
        stats["pending_proposals"] = await db["proposals"].count_documents({
            "status": "pending"
        })
        
        # Get recent activity
        recent_activity = []
        
        # Get recent revisions
        revisions_cursor = db["revisions"].find().sort("createdAt", -1).limit(5)
        revisions = await revisions_cursor.to_list(length=5)
        
        for rev in revisions:
            article = await db["articles"].find_one({"_id": rev["articleId"]})
            user = await db["users"].find_one({"_id": rev["createdBy"]})
            
            if article and user:
                recent_activity.append({
                    "type": "edit",
                    "timestamp": rev["createdAt"],
                    "user": {
                        "id": str(user["_id"]),
                        "username": user["username"],
                        "role": user.get("role", "user")
                    },
                    "article": {
                        "id": str(article["_id"]),
                        "title": article["title"],
                        "slug": article.get("slug", "")
                    },
                    "comment": rev.get("comment", "")
                })
        
        # Get recent proposals
        proposals_cursor = db["proposals"].find().sort("proposedAt", -1).limit(5)
        proposals = await proposals_cursor.to_list(length=5)
        
        for prop in proposals:
            article = await db["articles"].find_one({"_id": prop["articleId"]})
            user = await db["users"].find_one({"_id": prop["proposedBy"]})
            
            if article and user:
                recent_activity.append({
                    "type": "proposal",
                    "timestamp": prop["proposedAt"],
                    "user": {
                        "id": str(user["_id"]),
                        "username": user["username"],
                        "role": user.get("role", "user")
                    },
                    "article": {
                        "id": str(article["_id"]),
                        "title": article["title"],
                        "slug": article.get("slug", "")
                    },
                    "status": prop["status"],
                    "summary": prop.get("summary", "")
                })
        
        # Get new users
        users_cursor = db["users"].find().sort("joinDate", -1).limit(5)
        new_users = await users_cursor.to_list(length=5)
        
        for user in new_users:
            recent_activity.append({
                "type": "new_user",
                "timestamp": user["joinDate"],
                "user": {
                    "id": str(user["_id"]),
                    "username": user["username"],
                    "role": user.get("role", "user")
                }
            })
        
        # Sort by timestamp
        recent_activity.sort(key=lambda x: x["timestamp"], reverse=True)
        
        # Get top 5 items
        recent_activity = recent_activity[:5]
        
        # Store activity in the stats
        stats["recent_activity"] = recent_activity
        
        # Cache the results for 15 minutes
        await cache.set(cache_key, stats, 900)
        
        return stats
    except Exception as e:
        logger.error(f"Error getting admin dashboard stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting dashboard statistics: {str(e)}"
        )

@router.get("/users")
async def get_users(
    search: Optional[str] = None,
    role: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    sort_by: str = Query("joinDate", description="Field to sort by"),
    sort_order: int = Query(-1, description="Sort order: 1 for ascending, -1 for descending"),
    current_user: Dict[str, Any] = Depends(get_current_admin),
    db=Depends(get_db)
):
    """
    Get a list of users with optional filtering.
    """
    try:
        # Build query
        query = {}
        
        # Search filter
        if search:
            query["$or"] = [
                {"username": {"$regex": search, "$options": "i"}},
                {"email": {"$regex": search, "$options": "i"}}
            ]
        
        # Role filter
        if role:
            query["role"] = role
        
        # Get total count
        total = await db["users"].count_documents(query)
        
        # Get users with pagination and sorting
        cursor = db["users"].find(query).sort(sort_by, sort_order).skip(skip).limit(limit)
        users = await cursor.to_list(length=limit)
        
        # Remove sensitive information
        for user in users:
            if "passwordHash" in user:
                del user["passwordHash"]
        
        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "users": users
        }
    except Exception as e:
        logger.error(f"Error getting users: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting users: {str(e)}"
        )

@router.get("/users/{user_id}")
async def get_user(
    user_id: str = Path(..., description="User ID"),
    current_user: Dict[str, Any] = Depends(get_current_admin),
    db=Depends(get_db)
):
    """
    Get a single user by ID.
    """
    try:
        # Check if user ID is valid
        if not ObjectId.is_valid(user_id):
            raise HTTPException(
                status_code=400,
                detail="Invalid user ID format"
            )
        
        # Find user
        user = await db["users"].find_one({"_id": ObjectId(user_id)})
        
        if not user:
            raise HTTPException(
                status_code=404,
                detail=f"User with ID {user_id} not found"
            )
        
        # Remove sensitive information
        if "passwordHash" in user:
            del user["passwordHash"]
        
        # Get user contribution statistics
        stats = {}
        
        # Articles created
        stats["articles_created"] = await db["articles"].count_documents({
            "createdBy": ObjectId(user_id)
        })
        
        # Edits performed
        stats["edits_performed"] = await db["revisions"].count_documents({
            "createdBy": ObjectId(user_id)
        })
        
        # Proposals submitted
        stats["proposals_submitted"] = await db["proposals"].count_documents({
            "proposedBy": ObjectId(user_id)
        })
        
        # Rewards received
        stats["rewards_received"] = await db["rewards"].count_documents({
            "rewardedUser": ObjectId(user_id)
        })
        
        # Add stats to user data
        user["statistics"] = stats
        
        # Get recent activity
        recent_activity = []
        
        # Recent revisions
        revisions_cursor = db["revisions"].find({"createdBy": ObjectId(user_id)}).sort("createdAt", -1).limit(5)
        revisions = await revisions_cursor.to_list(length=5)
        
        for rev in revisions:
            article = await db["articles"].find_one({"_id": rev["articleId"]})
            if article:
                recent_activity.append({
                    "type": "edit",
                    "timestamp": rev["createdAt"],
                    "article": {
                        "id": str(article["_id"]),
                        "title": article["title"],
                        "slug": article.get("slug", "")
                    },
                    "comment": rev.get("comment", "")
                })
        
        # Recent proposals
        proposals_cursor = db["proposals"].find({"proposedBy": ObjectId(user_id)}).sort("proposedAt", -1).limit(5)
        proposals = await proposals_cursor.to_list(length=5)
        
        for prop in proposals:
            article = await db["articles"].find_one({"_id": prop["articleId"]})
            if article:
                recent_activity.append({
                    "type": "proposal",
                    "timestamp": prop["proposedAt"],
                    "article": {
                        "id": str(article["_id"]),
                        "title": article["title"],
                        "slug": article.get("slug", "")
                    },
                    "status": prop["status"],
                    "summary": prop.get("summary", "")
                })
        
        # Sort by timestamp
        recent_activity.sort(key=lambda x: x["timestamp"], reverse=True)
        
        # Get top 5 items
        recent_activity = recent_activity[:5]
        
        # Add activity to user data
        user["recent_activity"] = recent_activity
        
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting user: {str(e)}"
        )

@router.put("/users/{user_id}")
async def update_user(
    user_id: str = Path(..., description="User ID"),
    user_data: UserUpdate = Body(...),
    current_user: Dict[str, Any] = Depends(get_current_admin),
    db=Depends(get_db)
):
    """
    Update a user's information.
    """
    try:
        # Check if user ID is valid
        if not ObjectId.is_valid(user_id):
            raise HTTPException(
                status_code=400,
                detail="Invalid user ID format"
            )
        
        # Find user
        user = await db["users"].find_one({"_id": ObjectId(user_id)})
        
        if not user:
            raise HTTPException(
                status_code=404,
                detail=f"User with ID {user_id} not found"
            )
        
        # Build update data
        update_data = {}
        
        # Update username if provided
        if user_data.username:
            # Check if username is already taken
            existing_user = await db["users"].find_one({
                "username": user_data.username,
                "_id": {"$ne": ObjectId(user_id)}
            })
            
            if existing_user:
                raise HTTPException(
                    status_code=400,
                    detail="Username already taken"
                )
            
            update_data["username"] = user_data.username
        
        # Update email if provided
        if user_data.email:
            # Check if email is already taken
            existing_user = await db["users"].find_one({
                "email": user_data.email,
                "_id": {"$ne": ObjectId(user_id)}
            })
            
            if existing_user:
                raise HTTPException(
                    status_code=400,
                    detail="Email already taken"
                )
            
            update_data["email"] = user_data.email
        
        # Update password if provided (this would typically be done by a user service)
        if user_data.password:
            from utils.security import hash_password
            update_data["passwordHash"] = hash_password(user_data.password)
        
        # Update role if admin is changing another user (not themselves)
        if "role" in user_data.__dict__ and user_data.role and str(current_user["_id"]) != user_id:
            valid_roles = ["user", "editor", "admin"]
            if user_data.role not in valid_roles:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid role. Must be one of: {', '.join(valid_roles)}"
                )
            update_data["role"] = user_data.role
        
        # Only update if there are changes
        if update_data:
            result = await db["users"].update_one(
                {"_id": ObjectId(user_id)},
                {"$set": update_data}
            )
            
            if result.modified_count == 0:
                raise HTTPException(
                    status_code=400,
                    detail="No changes made"
                )
            
            # Get updated user
            updated_user = await db["users"].find_one({"_id": ObjectId(user_id)})
            
            # Remove sensitive information
            if "passwordHash" in updated_user:
                del updated_user["passwordHash"]
            
            return updated_user
        else:
            raise HTTPException(
                status_code=400,
                detail="No valid update data provided"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error updating user: {str(e)}"
        )

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str = Path(..., description="User ID"),
    current_user: Dict[str, Any] = Depends(get_current_admin),
    db=Depends(get_db)
):
    """
    Delete a user (admin only).
    """
    try:
        # Check if user ID is valid
        if not ObjectId.is_valid(user_id):
            raise HTTPException(
                status_code=400,
                detail="Invalid user ID format"
            )
        
        # Prevent self-deletion
        if str(current_user["_id"]) == user_id:
            raise HTTPException(
                status_code=400,
                detail="Cannot delete your own account"
            )
        
        # Find user
        user = await db["users"].find_one({"_id": ObjectId(user_id)})
        
        if not user:
            raise HTTPException(
                status_code=404,
                detail=f"User with ID {user_id} not found"
            )
        
        # Delete user
        result = await db["users"].delete_one({"_id": ObjectId(user_id)})
        
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=400,
                detail="Failed to delete user"
            )
        
        return {"message": f"User {user['username']} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting user: {str(e)}"
        )

@router.get("/articles/stats")
async def get_article_stats(
    current_user: Dict[str, Any] = Depends(get_current_admin),
    db=Depends(get_db),
    cache=Depends(get_cache)
):
    """
    Get detailed article statistics.
    """
    try:
        # Try to get from cache
        cache_key = "admin_article_stats"
        cached_stats = await cache.get(cache_key)
        
        if cached_stats:
            return cached_stats
        
        # Calculate stats
        stats = {}
        
        # Basic counts
        stats["total"] = await db["articles"].count_documents({})
        stats["published"] = await db["articles"].count_documents({"status": "published"})
        stats["draft"] = await db["articles"].count_documents({"status": "draft"})
        stats["hidden"] = await db["articles"].count_documents({"status": "hidden"})
        stats["archived"] = await db["articles"].count_documents({"status": "archived"})
        
        # Most viewed articles
        viewed_cursor = db["articles"].find().sort("views", -1).limit(10)
        most_viewed = await viewed_cursor.to_list(length=10)
        stats["most_viewed"] = [
            {
                "id": str(article["_id"]),
                "title": article["title"],
                "views": article["views"],
                "slug": article.get("slug", "")
            }
            for article in most_viewed
        ]
        
        # Recently edited articles
        recently_edited = []
        revisions_cursor = db["revisions"].find().sort("createdAt", -1).limit(20)
        revisions = await revisions_cursor.to_list(length=20)
        
        # Track articles we've already seen
        seen_articles = set()
        
        for rev in revisions:
            article_id = str(rev["articleId"])
            
            # Skip if we've already seen this article
            if article_id in seen_articles:
                continue
            
            article = await db["articles"].find_one({"_id": rev["articleId"]})
            if article:
                recently_edited.append({
                    "id": article_id,
                    "title": article["title"],
                    "last_edit": rev["createdAt"],
                    "slug": article.get("slug", "")
                })
                seen_articles.add(article_id)
                
                # Stop once we have 10 articles
                if len(recently_edited) >= 10:
                    break
        
        stats["recently_edited"] = recently_edited
        
        # Category statistics
        category_pipeline = [
            {"$unwind": "$categories"},
            {"$group": {"_id": "$categories", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        
        top_categories = await db["articles"].aggregate(category_pipeline).to_list(length=10)
        stats["top_categories"] = top_categories
        
        # Tag statistics
        tag_pipeline = [
            {"$unwind": "$tags"},
            {"$group": {"_id": "$tags", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        
        top_tags = await db["articles"].aggregate(tag_pipeline).to_list(length=10)
        stats["top_tags"] = top_tags
        
        # Cache the results for 15 minutes
        await cache.set(cache_key, stats, 900)
        
        return stats
    except Exception as e:
        logger.error(f"Error getting article stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting article statistics: {str(e)}"
        )

@router.get("/proposals/stats")
async def get_proposal_stats(
    current_user: Dict[str, Any] = Depends(get_current_admin),
    db=Depends(get_db)
):
    """
    Get detailed proposal statistics.
    """
    try:
        stats = {}
        
        # Basic counts
        stats["total"] = await db["proposals"].count_documents({})
        stats["pending"] = await db["proposals"].count_documents({"status": "pending"})
        stats["approved"] = await db["proposals"].count_documents({"status": "approved"})
        stats["rejected"] = await db["proposals"].count_documents({"status": "rejected"})
        
        # Recent proposals
        proposals_cursor = db["proposals"].find().sort("proposedAt", -1).limit(10)
        recent_proposals = await proposals_cursor.to_list(length=10)
        
        enhanced_proposals = []
        for prop in recent_proposals:
            article = await db["articles"].find_one({"_id": prop["articleId"]})
            user = await db["users"].find_one({"_id": prop["proposedBy"]})
            
            if article and user:
                enhanced_proposals.append({
                    "id": str(prop["_id"]),
                    "article": {
                        "id": str(article["_id"]),
                        "title": article["title"],
                        "slug": article.get("slug", "")
                    },
                    "user": {
                        "id": str(user["_id"]),
                        "username": user["username"]
                    },
                    "status": prop["status"],
                    "proposedAt": prop["proposedAt"],
                    "summary": prop.get("summary", "")
                })
        
        stats["recent_proposals"] = enhanced_proposals
        
        # Top proposal contributors
        contributor_pipeline = [
            {"$group": {"_id": "$proposedBy", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        
        top_contributors = await db["proposals"].aggregate(contributor_pipeline).to_list(length=10)
        
        enhanced_contributors = []
        for contributor in top_contributors:
            user = await db["users"].find_one({"_id": contributor["_id"]})
            if user:
                enhanced_contributors.append({
                    "user": {
                        "id": str(user["_id"]),
                        "username": user["username"]
                    },
                    "count": contributor["count"]
                })
        
        stats["top_contributors"] = enhanced_contributors
        
        return stats
    except Exception as e:
        logger.error(f"Error getting proposal stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting proposal statistics: {str(e)}"
        )

@router.post("/system/clear-cache")
async def clear_cache(
    current_user: Dict[str, Any] = Depends(get_current_admin),
    cache=Depends(get_cache)
):
    """
    Clear the application cache (admin only).
    """
    try:
        result = await cache.clear()
        return {"success": result, "message": "Cache cleared successfully"}
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error clearing cache: {str(e)}"
        )
