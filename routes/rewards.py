"""
Reward-related routes for the Cryptopedia application.
"""
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from bson import ObjectId
from typing import Dict, Any, List, Optional
from datetime import datetime

from models import Reward, RewardCreate
from dependencies import get_db, get_current_user

router = APIRouter()

@router.post("/articles/{article_id}/rewards", response_model=Dict[str, Any])
async def create_reward(
    article_id: str,
    reward: RewardCreate,
    revision_id: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db=Depends(get_db)
):
    """
    Create a reward for an article or specific revision.
    """
    # Check if article exists
    if not ObjectId.is_valid(article_id):
        raise HTTPException(status_code=400, detail="Invalid article ID")
    
    article = await db["articles"].find_one({"_id": ObjectId(article_id)})
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    # Determine the user to reward
    revision_obj_id = None
    if revision_id:
        if not ObjectId.is_valid(revision_id):
            raise HTTPException(status_code=400, detail="Invalid revision ID")
        
        revision = await db["revisions"].find_one({
            "_id": ObjectId(revision_id),
            "articleId": ObjectId(article_id)
        })
        
        if not revision:
            raise HTTPException(status_code=404, detail="Revision not found")
        
        revision_obj_id = ObjectId(revision_id)
        rewarded_user_id = revision["createdBy"]
    else:
        # Reward goes to article creator
        rewarded_user_id = article["createdBy"]
    
    # Don't allow self-rewarding
    if str(rewarded_user_id) == str(current_user["_id"]):
        raise HTTPException(status_code=400, detail="Cannot reward your own content")
    
    # Validate reward type
    valid_reward_types = ["helpful", "insightful", "comprehensive"]
    if reward.reward_type not in valid_reward_types:
        raise HTTPException(status_code=400, detail=f"Invalid reward type. Must be one of: {', '.join(valid_reward_types)}")
    
    # Create reward
    new_reward = {
        "articleId": ObjectId(article_id),
        "revisionId": revision_obj_id,
        "rewardType": reward.reward_type,
        "points": reward.points,
        "rewardedUser": rewarded_user_id,
        "rewardedBy": current_user["_id"],
        "rewardedAt": datetime.now()
    }
    
    result = await db["rewards"].insert_one(new_reward)
    
    # Update user's reputation and rewards count
    await db["users"].update_one(
        {"_id": rewarded_user_id},
        {"$inc": {
            "reputation": reward.points,
            "contributions.rewardsReceived": 1
        }}
    )
    
    # Get created reward
    created_reward = await db["rewards"].find_one({"_id": result.inserted_id})
    
    # Get user info
    rewarded_user = await db["users"].find_one({"_id": rewarded_user_id})
    
    # Return enhanced reward
    return {
        **created_reward,
        "rewardedUsername": rewarded_user["username"] if rewarded_user else "Unknown",
        "rewarderUsername": current_user["username"],
        "message": f"Successfully rewarded {rewarded_user['username'] if rewarded_user else 'user'} with {reward.points} points"
    }

@router.get("/articles/{article_id}/rewards", response_model=List[Dict[str, Any]])
async def get_article_rewards(
    article_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db=Depends(get_db)
):
    """
    Get all rewards for an article.
    """
    # Check if article exists
    if not ObjectId.is_valid(article_id):
        raise HTTPException(status_code=400, detail="Invalid article ID")
    
    article = await db["articles"].find_one({"_id": ObjectId(article_id)})
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    # Get rewards
    cursor = db["rewards"].find({"articleId": ObjectId(article_id)}).sort("rewardedAt", -1).skip(skip).limit(limit)
    rewards = await cursor.to_list(length=limit)
    
    # Enhance with user info
    enhanced_rewards = []
    for reward in rewards:
        # Get rewarded user info
        rewarded_user = await db["users"].find_one({"_id": reward["rewardedUser"]})
        rewarded_username = rewarded_user["username"] if rewarded_user else "Unknown"
        
        # Get rewarder info
        rewarder = await db["users"].find_one({"_id": reward["rewardedBy"]})
        rewarder_username = rewarder["username"] if rewarder else "Unknown"
        
        # Add to enhanced list
        enhanced_rewards.append({
            **reward,
            "rewardedUsername": rewarded_username,
            "rewarderUsername": rewarder_username
        })
    
    return enhanced_rewards

@router.get("/users/{user_id}/rewards", response_model=List[Dict[str, Any]])
async def get_user_rewards(
    user_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db=Depends(get_db)
):
    """
    Get all rewards received by a user.
    """
    # Check if user exists
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="Invalid user ID")
    
    user = await db["users"].find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get rewards
    cursor = db["rewards"].find({"rewardedUser": ObjectId(user_id)}).sort("rewardedAt", -1).skip(skip).limit(limit)
    rewards = await cursor.to_list(length=limit)
    
    # Enhance with article and user info
    enhanced_rewards = []
    for reward in rewards:
        # Get article info
        article = await db["articles"].find_one({"_id": reward["articleId"]})
        article_title = article["title"] if article else "Unknown Article"
        
        # Get rewarder info
        rewarder = await db["users"].find_one({"_id": reward["rewardedBy"]})
        rewarder_username = rewarder["username"] if rewarder else "Unknown"
        
        # Add to enhanced list
        enhanced_rewards.append({
            **reward,
            "articleTitle": article_title,
            "rewarderUsername": rewarder_username
        })
    
    return enhanced_rewards
