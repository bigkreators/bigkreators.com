"""
Special routes for the Cryptopedia application.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from dependencies import get_db, get_current_user, get_current_admin, get_cache

router = APIRouter()

@router.get("/recentchanges")
async def get_recent_changes(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db=Depends(get_db),
    cache=Depends(get_cache)
):
    """
    Get a list of recent changes to articles.
    """
    # Try to get from cache
    cache_key = f"recentchanges:{skip}:{limit}"
    cached = await cache.get(cache_key)
    if cached:
        return cached
    
    # Get recent revisions
    rev_cursor = db["revisions"].find().sort("createdAt", -1).skip(skip).limit(limit)
    revisions = await rev_cursor.to_list(length=limit)
    
    # Enhance with article info
    result = []
    for rev in revisions:
        article = await db["articles"].find_one({"_id": rev["articleId"]})
        user = await db["users"].find_one({"_id": rev["createdBy"]})
        
        if article and user:
            result.append({
                "type": "revision",
                "id": str(rev["_id"]),
                "timestamp": rev["createdAt"],
                "articleId": str(rev["articleId"]),
                "articleTitle": article.get("title", "Unknown"),
                "userId": str(rev["createdBy"]),
                "username": user.get("username", "Unknown"),
                "comment": rev.get("comment", "")
            })
    
    # Cache results for 5 minutes
    await cache.set(cache_key, result, 300)
    
    return result

@router.get("/statistics")
async def get_statistics(
    db=Depends(get_db),
    cache=Depends(get_cache)
):
    """
    Get site statistics.
    """
    # Try to get from cache
    cached = await cache.get("statistics")
    if cached:
        return cached
    
    # Get statistics
    articles_count = await db["articles"].count_documents({"status": "published"})
    users_count = await db["users"].count_documents({})
    revisions_count = await db["revisions"].count_documents({})
    
    # Most viewed article
    most_viewed = await db["articles"].find_one(
        {"status": "published"},
        sort=[("views", -1)]
    )
    
    # Most active user (by edits)
    most_active = await db["users"].find_one(
        sort=[("contributions.editsPerformed", -1)]
    )
    
    # Recent activity (last 24 hours)
    yesterday = datetime.now() - timedelta(days=1)
    recent_revisions = await db["revisions"].count_documents({"createdAt": {"$gte": yesterday}})
    recent_proposals = await db["proposals"].count_documents({"proposedAt": {"$gte": yesterday}})
    
    statistics = {
        "articles": articles_count,
        "users": users_count,
        "revisions": revisions_count,
        "mostViewedArticle": {
            "id": str(most_viewed["_id"]) if most_viewed else None,
            "title": most_viewed.get("title") if most_viewed else None,
            "views": most_viewed.get("views") if most_viewed else 0
        },
        "mostActiveUser": {
            "id": str(most_active["_id"]) if most_active else None,
            "username": most_active.get("username") if most_active else None,
            "edits": most_active.get("contributions", {}).get("editsPerformed", 0) if most_active else 0
        },
        "recentActivity": {
            "revisions": recent_revisions,
            "proposals": recent_proposals,
            "total": recent_revisions + recent_proposals
        }
    }
    
    # Cache for 1 hour
    await cache.set("statistics", statistics, 3600)
    
    return statistics

@router.get("/users", response_model=List[Dict[str, Any]])
async def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: Dict[str, Any] = Depends(get_current_admin),
    db=Depends(get_db)
):
    """
    Get a list of users (admin only).
    """
    cursor = db["users"].find().sort("joinDate", -1).skip(skip).limit(limit)
    users = await cursor.to_list(length=limit)
    
    # Remove password hashes for security
    for user in users:
        if "passwordHash" in user:
            del user["passwordHash"]
    
    return users

@router.put("/users/{user_id}/role")
async def update_user_role(
    user_id: str,
    role: str = Query(..., regex="^(user|editor|admin)$"),
    current_user: Dict[str, Any] = Depends(get_current_admin),
    db=Depends(get_db)
):
    """
    Update a user's role (admin only).
    """
    from bson import ObjectId
    
    # Check if user exists
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="Invalid user ID")
    
    user = await db["users"].find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent self-demotion
    if str(user["_id"]) == str(current_user["_id"]) and role != "admin":
        raise HTTPException(status_code=400, detail="Cannot demote yourself from admin")
    
    # Update role
    await db["users"].update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"role": role}}
    )
    
    return {"message": f"User role updated to {role}"}

@router.get("/pending-proposals", response_model=List[Dict[str, Any]])
async def get_pending_proposals(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db=Depends(get_db)
):
    """
    Get a list of pending proposals.
    For admins/editors: All pending proposals
    For regular users: Only their own proposals
    """
    # Build query
    query = {"status": "pending"}
    
    # If not admin or editor, only show user's own proposals
    if current_user["role"] not in ["admin", "editor"]:
        query["proposedBy"] = current_user["_id"]
    
    # Get proposals
    cursor = db["proposals"].find(query).sort("proposedAt", -1).skip(skip).limit(limit)
    proposals = await cursor.to_list(length=limit)
    
    # Enhance with article and user info
    enhanced_proposals = []
    for prop in proposals:
        # Get article info
        article = await db["articles"].find_one({"_id": prop["articleId"]})
        article_title = article["title"] if article else "Unknown Article"
        
        # Get proposer info
        proposer = await db["users"].find_one({"_id": prop["proposedBy"]})
        proposer_username = proposer["username"] if proposer else "Unknown"
        
        # Add to enhanced list
        enhanced_proposals.append({
            **prop,
            "articleTitle": article_title,
            "proposerUsername": proposer_username
        })
    
    return enhanced_proposals

@router.get("/search-tags")
async def search_tags(db=Depends(get_db)):
    """
    Get a list of all tags used across articles.
    """
    # Use aggregation to get unique tags and their count
    pipeline = [
        {"$match": {"status": "published"}},
        {"$unwind": "$tags"},
        {"$group": {"_id": "$tags", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    
    result = await db["articles"].aggregate(pipeline).to_list(None)
    
    return [{"tag": item["_id"], "count": item["count"]} for item in result]

@router.get("/search-categories")
async def search_categories(db=Depends(get_db)):
    """
    Get a list of all categories used across articles.
    """
    # Use aggregation to get unique categories and their count
    pipeline = [
        {"$match": {"status": "published"}},
        {"$unwind": "$categories"},
        {"$group": {"_id": "$categories", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    
    result = await db["articles"].aggregate(pipeline).to_list(None)
    
    return [{"category": item["_id"], "count": item["count"]} for item in result]
