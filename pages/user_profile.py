# File: pages/user_profile.py
"""
User profile page routes for the Kryptopedia application.
"""
from fastapi import APIRouter, Request, Depends, Path, Query, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from typing import Optional, Dict, Any
import logging
from bson import ObjectId

from dependencies import get_db, get_current_user, get_cache

router = APIRouter()
logger = logging.getLogger(__name__)

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
            from dependencies.auth import validate_token_manually
            return await validate_token_manually(token, db)
        except Exception as e:
            logger.debug(f"Error getting user from Authorization header: {e}")
    
    # Try to get token from cookie
    token = request.cookies.get("token")
    if token:
        try:
            from dependencies.auth import validate_token_manually
            return await validate_token_manually(token, db)
        except Exception as e:
            logger.debug(f"Error getting user from cookie: {e}")
    
    # No valid authentication found
    return None

# IMPORTANT: Define specific routes before parameterized ones
# This route must come before the /profile/{username} route
@router.get("/profile/edit", response_class=HTMLResponse)
async def edit_profile_page(
    request: Request,
    db=Depends(get_db)
):
    """
    Render the profile editing page.
    """
    templates = request.app.state.templates
    
    # Try to get current user from authentication token
    current_user = await get_user_from_request(request, db)
    
    # Check if user is authenticated
    if not current_user:
        return templates.TemplateResponse(
            "login_required.html",
            {
                "request": request, 
                "redirect_to": "/profile/edit",
                "active_page": "profile"
            }
        )
    
    # Render the edit profile template
    return templates.TemplateResponse(
        "profile_edit.html",
        {
            "request": request,
            "user": current_user,
            "is_self": True,
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
    # Try to get current user from authentication token
    current_user = await get_user_from_request(request, db)
    
    # Check if user is authenticated
    if not current_user:
        templates = request.app.state.templates
        return templates.TemplateResponse(
            "login_required.html",
            {
                "request": request, 
                "redirect_to": "/profile?tab=settings",
                "active_page": "profile"
            }
        )
    
    return RedirectResponse(url="/profile?tab=settings")

# Now define the parameterized routes with a regex constraint to avoid conflicts
# Use regex to make sure username doesn't match the other static routes
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
    
    # Try to get current authenticated user
    current_user = await get_user_from_request(request, db)
    
    # Determine which user profile to show
    if username:
        # Showing another user's profile
        profile_user = await db["users"].find_one({"username": username})
        if not profile_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        is_self = current_user and str(current_user["_id"]) == str(profile_user["_id"])
    else:
        # Showing current user's own profile
        if not current_user:
            return templates.TemplateResponse(
                "login_required.html",
                {
                    "request": request, 
                    "redirect_to": "/profile",
                    "active_page": "profile"
                }
            )
        profile_user = current_user
        is_self = True
    
    # Get user's articles with pagination
    articles_cursor = db["articles"].find({"authorId": profile_user["_id"]})
    total_articles = await db["articles"].count_documents({"authorId": profile_user["_id"]})
    articles = await articles_cursor.skip(articles_skip).limit(articles_limit).to_list(length=articles_limit)
    
    # Get user's contributions (edit history) with pagination  
    contributions_cursor = db["revisions"].find({"editorId": profile_user["_id"]})
    total_contributions = await db["revisions"].count_documents({"editorId": profile_user["_id"]})
    contributions = await contributions_cursor.skip(contributions_skip).limit(contributions_limit).to_list(length=contributions_limit)
    
    # Get user's proposals with pagination (if they have any)
    proposals_cursor = db["proposals"].find({"proposerId": profile_user["_id"]})
    total_proposals = await db["proposals"].count_documents({"proposerId": profile_user["_id"]})
    proposals = await proposals_cursor.skip(proposals_skip).limit(proposals_limit).to_list(length=proposals_limit)
    
    # Get user's rewards with pagination (if they have any)
    rewards_cursor = db["rewards"].find({"userId": profile_user["_id"]})
    total_rewards = await db["rewards"].count_documents({"userId": profile_user["_id"]})
    rewards = await rewards_cursor.skip(rewards_skip).limit(rewards_limit).to_list(length=rewards_limit)
    
    # Convert ObjectIds to strings for template rendering
    for article in articles:
        article["_id"] = str(article["_id"])
        article["authorId"] = str(article["authorId"])
    
    for contribution in contributions:
        contribution["_id"] = str(contribution["_id"])
        contribution["articleId"] = str(contribution["articleId"])
        contribution["editorId"] = str(contribution["editorId"])
    
    for proposal in proposals:
        proposal["_id"] = str(proposal["_id"])
        proposal["articleId"] = str(proposal["articleId"])
        proposal["proposerId"] = str(proposal["proposerId"])
    
    for reward in rewards:
        reward["_id"] = str(reward["_id"])
        reward["userId"] = str(reward["userId"])
    
    # Convert profile user ID to string
    profile_user["_id"] = str(profile_user["_id"])
    
    return templates.TemplateResponse(
        "user_profile.html",
        {
            "request": request,
            "user": profile_user,
            "current_user": current_user,
            "is_self": is_self,
            "active_tab": tab or "overview",
            "articles": articles,
            "contributions": contributions,
            "proposals": proposals,
            "rewards": rewards,
            "total_articles": total_articles,
            "total_contributions": total_contributions, 
            "total_proposals": total_proposals,
            "total_rewards": total_rewards,
            "articles_skip": articles_skip,
            "articles_limit": articles_limit,
            "contributions_skip": contributions_skip,
            "contributions_limit": contributions_limit,
            "proposals_skip": proposals_skip,
            "proposals_limit": proposals_limit,
            "rewards_skip": rewards_skip,
            "rewards_limit": rewards_limit,
            "active_page": "profile"
        }
    )
