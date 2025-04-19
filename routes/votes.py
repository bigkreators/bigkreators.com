# File: routes/votes.py
"""
Vote-related routes for the Kryptopedia application.
"""
from fastapi import APIRouter, Depends, HTTPException, Path, status
from bson import ObjectId
from typing import Dict, Any, Optional
import logging

from dependencies import get_db, get_current_user, get_cache

# Initialize router
router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/articles/{article_id}/vote")
async def vote_article(
    article_id: str,
    vote_data: Dict[str, str],  # Expected {"vote_type": "upvote"|"downvote"}
    current_user: Dict[str, Any] = Depends(get_current_user),
    db=Depends(get_db),
    cache=Depends(get_cache)
):
    """
    Vote on an article (upvote or downvote).
    """
    try:
        # Extract vote type from request data
        vote_type = vote_data.get("vote_type")
        
        # Validate article ID
        if not ObjectId.is_valid(article_id):
            raise HTTPException(status_code=400, detail="Invalid article ID")
        
        # Validate vote type
        if vote_type not in ["upvote", "downvote"]:
            raise HTTPException(status_code=400, detail="Invalid vote type. Must be 'upvote' or 'downvote'")
        
        # Check if article exists
        article = await db["articles"].find_one({"_id": ObjectId(article_id)})
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")
        
        # Get article creator ID for updating upvote counts
        article_creator_id = article.get("createdBy")
        
        # Ensure upvotes and downvotes fields exist in the article document
        if "upvotes" not in article:
            article["upvotes"] = 0
        if "downvotes" not in article:
            article["downvotes"] = 0
        
        # Get current user's vote (if any)
        current_vote = await db["votes"].find_one({
            "articleId": ObjectId(article_id),
            "userId": current_user["_id"]
        })
        
        if not current_vote:
            # User hasn't voted before, create new vote
            await db["votes"].insert_one({
                "articleId": ObjectId(article_id),
                "userId": current_user["_id"],
                "voteType": vote_type
            })
            
            # Increment the vote count
            if vote_type == "upvote":
                await db["articles"].update_one(
                    {"_id": ObjectId(article_id)},
                    {"$inc": {"upvotes": 1}}
                )
                
                # Increment creator's upvote count
                if article_creator_id:
                    await db["users"].update_one(
                        {"_id": article_creator_id},
                        {"$inc": {"contributions.upvotesReceived": 1}}
                    )
            else:
                await db["articles"].update_one(
                    {"_id": ObjectId(article_id)},
                    {"$inc": {"downvotes": 1}}
                )
                
            message = f"Article {vote_type}d successfully"
            
        else:
            # User has already voted
            if current_vote["voteType"] == vote_type:
                # User is trying to vote the same way again, remove the vote
                await db["votes"].delete_one({
                    "_id": current_vote["_id"]
                })
                
                # Decrement the vote count
                if vote_type == "upvote":
                    await db["articles"].update_one(
                        {"_id": ObjectId(article_id)},
                        {"$inc": {"upvotes": -1}}
                    )
                    
                    # Decrement creator's upvote count
                    if article_creator_id:
                        await db["users"].update_one(
                            {"_id": article_creator_id},
                            {"$inc": {"contributions.upvotesReceived": -1}}
                        )
                else:
                    await db["articles"].update_one(
                        {"_id": ObjectId(article_id)},
                        {"$inc": {"downvotes": -1}}
                    )
                    
                message = f"Article {vote_type} removed successfully"
                
            else:
                # User is changing their vote
                await db["votes"].update_one(
                    {"_id": current_vote["_id"]},
                    {"$set": {"voteType": vote_type}}
                )
                
                # Update vote counts
                if vote_type == "upvote":
                    await db["articles"].update_one(
                        {"_id": ObjectId(article_id)},
                        {"$inc": {"upvotes": 1, "downvotes": -1}}
                    )
                    
                    # Increment creator's upvote count
                    if article_creator_id:
                        await db["users"].update_one(
                            {"_id": article_creator_id},
                            {"$inc": {"contributions.upvotesReceived": 1}}
                        )
                else:
                    await db["articles"].update_one(
                        {"_id": ObjectId(article_id)},
                        {"$inc": {"upvotes": -1, "downvotes": 1}}
                    )
                    
                    # Decrement creator's upvote count
                    if article_creator_id:
                        await db["users"].update_one(
                            {"_id": article_creator_id},
                            {"$inc": {"contributions.upvotesReceived": -1}}
                        )
                    
                message = f"Vote changed to {vote_type} successfully"
        
        # Invalidate cache
        if cache:
            await cache.delete(f"article:{article_id}")
            if article.get("slug"):
                await cache.delete(f"article:{article['slug']}")
                
            # Also invalidate creator's profile cache if applicable
            if article_creator_id:
                await cache.delete(f"user:{article_creator_id}")
        
        # Get updated article
        updated_article = await db["articles"].find_one({"_id": ObjectId(article_id)})
        
        # Return vote status
        return {
            "message": message,
            "upvotes": updated_article.get("upvotes", 0),
            "downvotes": updated_article.get("downvotes", 0)
        }
    
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error voting on article: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to vote on article: {str(e)}"
        )

@router.get("/articles/{article_id}/votes")
async def get_article_votes(
    article_id: str,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user),
    db=Depends(get_db)
):
    """
    Get vote counts for an article and the current user's vote status.
    """
    try:
        # Validate article ID
        if not ObjectId.is_valid(article_id):
            raise HTTPException(status_code=400, detail="Invalid article ID")
        
        # Check if article exists
        article = await db["articles"].find_one({"_id": ObjectId(article_id)})
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")
        
        # Ensure upvotes and downvotes fields exist
        upvotes = article.get("upvotes", 0)
        downvotes = article.get("downvotes", 0)
        
        # If fields don't exist in the document, update the document with default values
        if "upvotes" not in article or "downvotes" not in article:
            await db["articles"].update_one(
                {"_id": ObjectId(article_id)},
                {"$set": {
                    "upvotes": upvotes,
                    "downvotes": downvotes
                }}
            )
        
        # Get user's vote if logged in
        user_vote = None
        if current_user:
            vote_record = await db["votes"].find_one({
                "articleId": ObjectId(article_id),
                "userId": current_user["_id"]
            })
            
            if vote_record:
                user_vote = vote_record["voteType"]
        
        return {
            "upvotes": upvotes,
            "downvotes": downvotes,
            "userVote": user_vote
        }
    
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error getting article votes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get article votes: {str(e)}"
        )
