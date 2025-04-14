# File: pages/user_profile.py

"""
User profile page routes for the Kryptopedia application.
"""
from fastapi import APIRouter, Request, Depends, Path, Query, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from typing import Optional, Dict, Any
import logging
from bson import ObjectId

# Add this function at the top of the file, after imports
async def get_user_from_request(request, db):
    """
    Try to get the current user from the request using multiple methods.
    Returns None if no authenticated user is found.
    """
    # Try to get token from Authorization header
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.replace("Bearer ", "")
        try:
            from dependencies.auth import get_current_user
            return await get_current_user(token=token, db=db)
        except Exception as e:
            print(f"Error getting user from Authorization header: {e}")
    
    # Try to get token from cookie
    token = request.cookies.get("token")
    if token:
        try:
            from dependencies.auth import get_current_user
            return await get_current_user(token=token, db=db)
        except Exception as e:
            print(f"Error getting user from cookie: {e}")
    
    # No valid authentication found
    return None

from dependencies import get_db, get_current_user, get_cache

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
    db=Depends(get_db)
):
    """
    Render the user profile page.
    """
    templates = request.app.state.templates
    
    # Try to get current user from request
    current_user = await get_user_from_request(request, db)
    
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
            # Return login required template if not logged in
            return templates.TemplateResponse(
                "login_required.html",
                {"request": request, "redirect_to": "/profile"}
            )
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
    
    # Enhanced contributions with article info
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
    
    # Enhanced proposals with article info
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
    
    # Enhanced rewards with article and user info
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
            "current_user": current_user,
            "articles": articles,
            "articles_total": articles_total,
            "articles_skip": articles_skip,
            "articles_limit": articles_limit,
            "contributions": enhanced_contributions,
            "contributions_total": contributions_total,
            "contributions_skip": contributions_skip,
            "contributions_limit": contributions_limit,
            "proposals": enhanced_proposals,
            "proposals_total": proposals_total,
            "proposals_skip": proposals_skip,
            "proposals_limit": proposals_limit,
            "rewards": enhanced_rewards,
            "rewards_total": rewards_total,
            "rewards_skip": rewards_skip,
            "rewards_limit": rewards_limit,
            "badges": [],  # Future feature
            "active_page": "profile",  # For sidebar navigation
            "tab": tab  # Pass the tab parameter to the template
        }
    )

@router.get("/profile/edit", response_class=HTMLResponse)
async def edit_profile_page(
    request: Request,
    db=Depends(get_db)
):
    """
    Redirect to profile with the edit query parameter
    """
    return RedirectResponse(url="/profile/edit-profile")

@router.get("/profile/edit-profile", response_class=HTMLResponse)
async def edit_profile_details_page(
    request: Request,
    db=Depends(get_db)
):
    """
    Render the profile editing page.
    """
    templates = request.app.state.templates
    
    # Try to get current user from request
    current_user = await get_user_from_request(request, db)
    
    # If no user is found, return login required page
    if not current_user:
        return templates.TemplateResponse(
            "login_required.html",
            {"request": request, "redirect_to": "/profile/edit-profile"}
        )
    
    # Render the edit profile template
    return templates.TemplateResponse(
        "profile_edit.html",
        {
            "request": request,
            "user": current_user,
            "is_own_profile": True,
            "active_page": "profile"  # Set active page for navigation highlighting
        }
    )

@router.get("/profile/settings", response_class=HTMLResponse)
async def profile_settings_page(
    request: Request,
    db=Depends(get_db)
):
    """
    Redirect to profile with settings tab active.
    """
    return RedirectResponse(url="/profile?tab=settings")
