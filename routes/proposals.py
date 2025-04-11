"""
Proposal-related routes for the Cryptopedia application.
"""
from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from bson import ObjectId
from typing import List, Dict, Any, Optional
from datetime import datetime

from models import Proposal, ProposalCreate
from dependencies import get_db, get_current_user, get_current_editor, get_search, get_cache

router = APIRouter()

@router.post("/articles/{article_id}/proposals", response_model=Proposal)
async def create_proposal(
    article_id: str,
    proposal: ProposalCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db=Depends(get_db)
):
    """
    Create a new edit proposal for an article.
    """
    # Check if article exists
    if not ObjectId.is_valid(article_id):
        raise HTTPException(status_code=400, detail="Invalid article ID")
    
    article = await db["articles"].find_one({"_id": ObjectId(article_id)})
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    # Create proposal
    new_proposal = {
        "articleId": ObjectId(article_id),
        "proposedBy": current_user["_id"],
        "proposedAt": datetime.now(),
        "content": proposal.content,
        "summary": proposal.summary,
        "status": "pending",
        "reviewedBy": None,
        "reviewedAt": None,
        "reviewComment": None
    }
    
    # Insert into database
    result = await db["proposals"].insert_one(new_proposal)
    
    # Return created proposal
    created_proposal = await db["proposals"].find_one({"_id": result.inserted_id})
    return created_proposal

@router.get("/articles/{article_id}/proposals", response_model=List[Dict[str, Any]])
async def get_article_proposals(
    article_id: str,
    status: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db=Depends(get_db)
):
    """
    Get all proposals for an article.
    """
    # Check if article exists
    if not ObjectId.is_valid(article_id):
        raise HTTPException(status_code=400, detail="Invalid article ID")
    
    article = await db["articles"].find_one({"_id": ObjectId(article_id)})
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    # Build query
    query = {"articleId": ObjectId(article_id)}
    if status:
        query["status"] = status
    
    # Get proposals
    cursor = db["proposals"].find(query).sort("proposedAt", -1).skip(skip).limit(limit)
    proposals = await cursor.to_list(length=limit)
    
    # Enhance with user info
    enhanced_proposals = []
    for prop in proposals:
        # Get proposer info
        proposer = await db["users"].find_one({"_id": prop["proposedBy"]})
        proposer_username = proposer["username"] if proposer else "Unknown"
        
        # Get reviewer info if available
        reviewer_username = None
        if prop.get("reviewedBy"):
            reviewer = await db["users"].find_one({"_id": prop["reviewedBy"]})
            reviewer_username = reviewer["username"] if reviewer else "Unknown"
        
        # Add to enhanced list
        enhanced_proposals.append({
            **prop,
            "proposerUsername": proposer_username,
            "reviewerUsername": reviewer_username
        })
    
    return enhanced_proposals

@router.get("/articles/{article_id}/proposals/{proposal_id}", response_model=Dict[str, Any])
async def get_proposal(
    article_id: str,
    proposal_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db=Depends(get_db)
):
    """
    Get a specific proposal.
    """
    # Check if IDs are valid
    if not ObjectId.is_valid(article_id) or not ObjectId.is_valid(proposal_id):
        raise HTTPException(status_code=400, detail="Invalid ID format")
    
    # Get proposal
    proposal = await db["proposals"].find_one({
        "_id": ObjectId(proposal_id),
        "articleId": ObjectId(article_id)
    })
    
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    
    # Get user info
    proposer = await db["users"].find_one({"_id": proposal["proposedBy"]})
    proposer_username = proposer["username"] if proposer else "Unknown"
    
    reviewer_username = None
    if proposal.get("reviewedBy"):
        reviewer = await db["users"].find_one({"_id": proposal["reviewedBy"]})
        reviewer_username = reviewer["username"] if reviewer else "Unknown"
    
    # Return enhanced proposal
    return {
        **proposal,
        "proposerUsername": proposer_username,
        "reviewerUsername": reviewer_username
    }

@router.put("/articles/{article_id}/proposals/{proposal_id}")
async def review_proposal(
    article_id: str,
    proposal_id: str,
    status: str = Query(..., regex="^(approved|rejected)$"),
    comment: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_editor),
    db=Depends(get_db),
    search=Depends(get_search),
    cache=Depends(get_cache)
):
    """
    Review a proposal (approve or reject).
    """
    # Check if IDs are valid
    if not ObjectId.is_valid(article_id) or not ObjectId.is_valid(proposal_id):
        raise HTTPException(status_code=400, detail="Invalid ID format")
    
    # Get proposal
    proposal = await db["proposals"].find_one({
        "_id": ObjectId(proposal_id),
        "articleId": ObjectId(article_id)
    })
    
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    
    # If already reviewed, return error
    if proposal["status"] != "pending":
        raise HTTPException(status_code=400, detail=f"Proposal already {proposal['status']}")
    
    # Update proposal status
    await db["proposals"].update_one(
        {"_id": ObjectId(proposal_id)},
        {"$set": {
            "status": status,
            "reviewedBy": current_user["_id"],
            "reviewedAt": datetime.now(),
            "reviewComment": comment
        }}
    )
    
    # If approved, update the article
    if status == "approved":
        # Get the article
        article = await db["articles"].find_one({"_id": ObjectId(article_id)})
        
        # Update the article content
        await db["articles"].update_one(
            {"_id": ObjectId(article_id)},
            {"$set": {
                "content": proposal["content"],
                "lastUpdatedAt": datetime.now(),
                "lastUpdatedBy": proposal["proposedBy"]
            }}
        )
        
        # Create a revision
        revision = {
            "articleId": ObjectId(article_id),
            "content": proposal["content"],
            "createdBy": proposal["proposedBy"],
            "createdAt": datetime.now(),
            "comment": proposal["summary"]
        }
        
        await db["revisions"].insert_one(revision)
        
        # Update search index
        await search.update(
            index="articles",
            id=article_id,
            document={
                "content": proposal["content"],
                "updated": datetime.now().isoformat()
            }
        )
        
        # Invalidate cache
        await cache.delete(f"article:{article_id}")
        if article.get("slug"):
            await cache.delete(f"article:{article['slug']}")
        
        # Update user's contribution count
        await db["users"].update_one(
            {"_id": proposal["proposedBy"]},
            {"$inc": {"contributions.editsPerformed": 1}}
        )
    
    # Get updated proposal
    updated_proposal = await db["proposals"].find_one({"_id": ObjectId(proposal_id)})
    
    # Get user info
    proposer = await db["users"].find_one({"_id": updated_proposal["proposedBy"]})
    proposer_username = proposer["username"] if proposer else "Unknown"
    
    reviewer = await db["users"].find_one({"_id": updated_proposal["reviewedBy"]})
    reviewer_username = reviewer["username"] if reviewer else "Unknown"
    
    # Return enhanced proposal
    return {
        **updated_proposal,
        "proposerUsername": proposer_username,
        "reviewerUsername": reviewer_username,
        "message": f"Proposal {status}"
    }
