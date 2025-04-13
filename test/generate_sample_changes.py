"""
Updated route for recent changes that includes sample data generation
if no actual data exists in the database.
"""
from fastapi import APIRouter, Depends, HTTPException, Request, Path, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from bson import ObjectId
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import random

import config
from dependencies import get_db, get_cache, get_current_user, get_search

@router.get("/special/recentchanges", response_class=HTMLResponse)
async def recent_changes_page(
    request: Request,
    filter: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db=Depends(get_db),
    cache=Depends(get_cache)
):
    """
    Render the recent changes page.
    """
    templates = request.app.state.templates
    
    # Process revisions and proposals as before
    try:
        # Get recent revisions
        revisions_cursor = db["revisions"].find().sort("createdAt", -1).skip(skip).limit(limit)
        revisions = await revisions_cursor.to_list(length=limit)
        
        # Get recent proposals
        proposals_cursor = db["proposals"].find().sort("proposedAt", -1).skip(skip).limit(limit)
        proposals = await proposals_cursor.to_list(length=limit)
        
        # Combine and sort by date
        changes = []
        
        # Process revisions
        for rev in revisions:
            # Get article
            article = await db["articles"].find_one({"_id": rev["articleId"]})
            if not article:
                continue
                
            # Get user
            user = await db["users"].find_one({"_id": rev["createdBy"]})
            username = user["username"] if user else "Unknown"
            
            changes.append({
                "type": "revision",
                "timestamp": rev["createdAt"],
                "articleId": str(rev["articleId"]),
                "articleTitle": article["title"],
                "userId": str(rev["createdBy"]),
                "username": username,
                "comment": rev.get("comment", "")
            })
        
        # Process proposals
        for prop in proposals:
            # Get article
            article = await db["articles"].find_one({"_id": prop["articleId"]})
            if not article:
                continue
                
            # Get user
            user = await db["users"].find_one({"_id": prop["proposedBy"]})
            username = user["username"] if user else "Unknown"
            
            changes.append({
                "type": "proposal",
                "timestamp": prop["proposedAt"],
                "articleId": str(prop["articleId"]),
                "articleTitle": article["title"],
                "userId": str(prop["proposedBy"]),
                "username": username,
                "comment": prop.get("summary", "")
            })
        
        # Check if we have any changes
        if not changes:
            # Generate some sample changes if no real data exists
            print("No changes found, generating sample data")
            sample_changes = await generate_sample_changes(db)
            changes.extend(sample_changes)
        
        # Sort combined list by timestamp (newest first)
        changes.sort(key=lambda x: x["timestamp"], reverse=True)
        
        # Apply filter if needed
        if filter:
            changes = [c for c in changes if c["type"] == filter]
        
        # Get total count
        total = len(changes)
        
        # Paginate manually
        changes = changes[skip:skip+limit]
        
        # Render template
        return templates.TemplateResponse(
            "recent_changes.html",
            {
                "request": request,
                "changes": changes,
                "total": total,
                "skip": skip,
                "limit": limit,
                "filter": filter
            }
        )
    except Exception as e:
        print(f"Error getting recent changes: {e}")
        # Return empty results on error
        return templates.TemplateResponse(
            "recent_changes.html",
            {
                "request": request,
                "changes": [],
                "total": 0,
                "skip": skip,
                "limit": limit,
                "filter": filter
            }
        )

async def generate_sample_changes(db) -> List[Dict[str, Any]]:
    """
    Generate sample changes for display when no real data exists.
    """
    sample_changes = []
    
    # Get some articles and users to reference
    articles_cursor = db["articles"].find({"status": "published"}).limit(5)
    articles = await articles_cursor.to_list(length=5)
    
    if not articles:
        # If no articles exist, we can't generate sample changes
        return []
    
    users_cursor = db["users"].find().limit(3)
    users = await users_cursor.to_list(length=3)
    
    if not users:
        # If no users exist, use a default
        admin_user = {
            "_id": ObjectId(),
            "username": "admin"
        }
        users = [admin_user]
    
    # Sample comments for revisions
    revision_comments = [
        "Fixed typos in introduction",
        "Updated information in the second paragraph",
        "Added new section on advanced techniques",
        "Corrected historical information",
        "Improved formatting and readability",
        "Added references and citations",
        "Restructured content for better flow"
    ]
    
    # Sample comments for proposals
    proposal_comments = [
        "Suggested new content for the introduction",
        "Proposed additional examples",
        "Suggested clearer explanation of concepts",
        "Proposed update to outdated information",
        "Suggested adding missing details"
    ]
    
    # Generate sample revisions
    now = datetime.now()
    for i in range(10):
        article = random.choice(articles)
        user = random.choice(users)
        
        # Create a sample revision
        sample_changes.append({
            "type": "revision",
            "timestamp": now - timedelta(days=i, hours=random.randint(0, 23), minutes=random.randint(0, 59)),
            "articleId": str(article["_id"]),
            "articleTitle": article["title"],
            "userId": str(user["_id"]),
            "username": user["username"],
            "comment": random.choice(revision_comments)
        })
    
    # Generate sample proposals
    for i in range(5):
        article = random.choice(articles)
        user = random.choice(users)
        
        # Create a sample proposal
        sample_changes.append({
            "type": "proposal",
            "timestamp": now - timedelta(days=i, hours=random.randint(0, 23), minutes=random.randint(0, 59)),
            "articleId": str(article["_id"]),
            "articleTitle": article["title"],
            "userId": str(user["_id"]),
            "username": user["username"],
            "comment": random.choice(proposal_comments)
        })
    
    return sample_changes
