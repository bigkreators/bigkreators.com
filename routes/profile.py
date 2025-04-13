# File: routes/profile.py
"""
User profile routes for the Kryptopedia application.
"""
from fastapi import APIRouter, Depends, HTTPException, Request, Path, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from bson import ObjectId
from typing import Optional, Dict, Any
import logging

import config
from dependencies import get_db, get_current_user, get_cache
from utils.security import verify_password, hash_password

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/profile", response_class=HTMLResponse)
@router.get("/profile/{username}", response_class=HTMLResponse)
async def profile_page(
    request: Request,
    username: Optional[str] = None,
    tab: Optional[str] = Query(None),
    articles_skip: int = Query(0, alias="skip", ge=0),
    articles_limit: int = Query(10, alias="limit", ge=1, le=50),
    contributions_skip: int = Query(0, ge=0),
    contributions_limit: int = Query(10, ge=1, le=50),
    proposals_skip: int = Query(0, ge=0),
    proposals_limit: int = Query(10, ge=1, le=50),
    rewards_skip: int = Query(0, ge=0),
    rewards_limit: int = Query(10, ge=1, le=50),
    db=Depends(get_db),
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    """
    Render the user profile page.
    """
    templates = request.app.state.templates
    
    # Determine which user's profile to show
    if username:
        # Show the profile of the requested user
        user = await db["users"].find_one({"username": username})
        if not user:
            return templates.TemplateResponse(
                "404.html",
                {"request": request, "message": "User not found"},
                status_code=404
            )
        is_own_profile = current_user and str(current_user["_id"]) == str(user["_id"])
    else:
        # Show the current user's profile
        if not current_user:
            # Redirect to login if not logged in
            return RedirectResponse(url="/")
        user = current_user
        is_own_profile = True
    
    # Get user's articles
    articles_cursor = db["articles"].find({"createdBy": user["_id"]}).sort("createdAt", -1).skip(articles_skip).limit(articles_limit)
    articles = await articles_cursor.to_list(length=articles_limit)
    articles_total = await db["articles"].count_documents({"createdBy": user["_id"]})
    
    # Get user's contributions (revisions)
    contributions_cursor = db["revisions"].find({"createdBy": user["_id"]}).sort("createdAt", -1).skip(contributions_skip).limit(contributions_limit)
    contributions = await contributions_cursor.to_list(length=contributions_limit)
    contributions_total = await db["revisions"].count_documents({"createdBy": user["_id"]})
    
    # Enhance contributions with article info
    enhanced_contributions = []
    for contribution in contributions:
        article = await db["articles"].find_one({"_id": contribution["articleId"]})
        if article:
            enhanced_contributions.append({
                **contribution,
                "articleTitle": article.get("title", "Unknown Article"),
                "articleSlug": article.get("slug")
            })
    
    # Get user's proposals
    proposals_cursor = db["proposals"].find({"proposedBy": user["_id"]}).sort("proposedAt", -1).skip(proposals_skip).limit(proposals_limit)
    proposals = await proposals_cursor.to_list(length=proposals_limit)
    proposals_total = await db["proposals"].count_documents({"proposedBy": user["_id"]})
    
    # Enhance proposals with article info
    enhanced_proposals = []
    for proposal in proposals:
        article = await db["articles"].find_one({"_id": proposal["articleId"]})
        if article:
            enhanced_proposals.append({
                **proposal,
                "articleTitle": article.get("title", "Unknown Article"),
                "articleSlug": article.get("slug")
            })
    
    # Get user's rewards
    rewards_cursor = db["rewards"].find({"rewardedUser": user["_id"]}).sort("rewardedAt", -1).skip(rewards_skip).limit(rewards_limit)
    rewards = await rewards_cursor.to_list(length=rewards_limit)
    rewards_total = await db["rewards"].count_documents({"rewardedUser": user["_id"]})
    
    # Enhance rewards with article and user info
    enhanced_rewards = []
    for reward in rewards:
        article = await db["articles"].find_one({"_id": reward["articleId"]})
        rewarder = await db["users"].find_one({"_id": reward["rewardedBy"]})
        
        if article and rewarder:
            enhanced_rewards.append({
                **reward,
                "articleTitle": article.get("title", "Unknown Article"),
                "articleSlug": article.get("slug"),
                "rewarderUsername": rewarder.get("username", "Unknown User")
            })
    
    # Render the profile template
    return templates.TemplateResponse(
        "user_profile.html",
        {
            "request": request,
            "user": user,
            "is_own_profile": is_own_profile,
            "articles": articles,
            "articles_total": articles_total,
            "articles_skip": articles_skip,
            "contributions": enhanced_contributions,
            "contributions_total": contributions_total,
            "contributions_skip": contributions_skip,
            "proposals": enhanced_proposals,
            "proposals_total": proposals_total,
            "proposals_skip": proposals_skip,
            "rewards": enhanced_rewards,
            "rewards_total": rewards_total,
            "rewards_skip": rewards_skip,
            "badges": []  # Future feature
        }
    )

@router.get("/profile/edit", response_class=HTMLResponse)
async def edit_profile_page(
    request: Request,
    db=Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Render the profile editing page.
    """
    templates = request.app.state.templates
    
    # Render the edit profile template
    return templates.TemplateResponse(
        "profile_edit.html",
        {
            "request": request,
            "user": current_user
        }
    )

@router.get("/profile/settings", response_class=HTMLResponse)
async def profile_settings_page(
    request: Request,
    db=Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Redirect to profile with settings tab active.
    """
    return RedirectResponse(url="/profile?tab=settings")

@router.put("/api/auth/profile")
async def update_profile(
    user_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user),
    db=Depends(get_db)
):
    """
    Update the current user's profile information.
    """
    try:
        # Verify current password
        if not user_data.get("currentPassword"):
            raise HTTPException(status_code=400, detail="Current password is required")
        
        if not verify_password(user_data["currentPassword"], current_user["passwordHash"]):
            raise HTTPException(status_code=400, detail="Current password is incorrect")
        
        # Prepare update data
        update_data = {}
        
        # Basic profile fields
        if "displayName" in user_data:
            update_data["displayName"] = user_data["displayName"]
        
        if "bio" in user_data:
            update_data["bio"] = user_data["bio"]
        
        if "location" in user_data:
            update_data["location"] = user_data["location"]
        
        if "website" in user_data:
            update_data["website"] = user_data["website"]
        
        # Email field
        if "email" in user_data and user_data["email"] != current_user["email"]:
            # Check if email is already in use
            existing_user = await db["users"].find_one({"email": user_data["email"]})
            if existing_user and str(existing_user["_id"]) != str(current_user["_id"]):
                raise HTTPException(status_code=400, detail="Email is already in use")
            
            update_data["email"] = user_data["email"]
        
        # Email preferences
        if "emailPreferences" in user_data:
            update_data["emailPreferences"] = user_data["emailPreferences"]
        
        # Password update
        if user_data.get("password"):
            update_data["passwordHash"] = hash_password(user_data["password"])
        
        # Only update if there are changes
        if not update_data:
            return {"message": "No changes to save"}
        
        # Update user in database
        result = await db["users"].update_one(
            {"_id": current_user["_id"]},
            {"$set": update_data}
        )
        
        if result.modified_count == 0:
            return {"message": "No changes made"}
        
        return {"message": "Profile updated successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating profile: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update profile: {str(e)}")

@router.get("/api/users/{username}")
async def get_user_info(
    username: str,
    db=Depends(get_db)
):
    """
    Get basic public information about a user.
    """
    try:
        # Find user by username
        user = await db["users"].find_one({"username": username})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Return only public information
        return {
            "username": user["username"],
            "displayName": user.get("displayName"),
            "bio": user.get("bio"),
            "location": user.get("location"),
            "website": user.get("website"),
            "role": user["role"],
            "joinDate": user["joinDate"],
            "contributions": user["contributions"],
            "reputation": user["reputation"]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching user info: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch user info: {str(e)}")
