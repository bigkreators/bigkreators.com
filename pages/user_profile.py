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

@router.get("/users/{user_id}", response_class=HTMLResponse)
async def user_profile_page(
    request: Request,
    user_id: str,
    db=Depends(get_db)
):
    """
    Render the user profile page.
    """
    templates = request.app.state.templates
    
    try:
        # Check if user exists
        if not ObjectId.is_valid(user_id):
            return templates.TemplateResponse(
                "404.html",
                {"request": request, "message": "Invalid user ID"},
                status_code=404
            )
        
        user = await db["users"].find_one({"_id": ObjectId(user_id)})
        if not user:
            return templates.TemplateResponse(
                "404.html",
                {"request": request, "message": "User not found"},
                status_code=404
            )
        
        # Remove sensitive info
        if "passwordHash" in user:
            del user["passwordHash"]
        
        # Get user's articles
        articles_cursor = db["articles"].find({"createdBy": ObjectId(user_id)}).sort("createdAt", -1).limit(5)
        articles = await articles_cursor.to_list(length=5)
        
        # Get user's edits/revisions
        revisions_cursor = db["revisions"].find({"createdBy": ObjectId(user_id)}).sort("createdAt", -1).limit(5)
        revisions = await revisions_cursor.to_list(length=5)
        
        # Get user's proposals
        proposals_cursor = db["proposals"].find({"proposedBy": ObjectId(user_id)}).sort("proposedAt", -1).limit(5)
        proposals = await proposals_cursor.to_list(length=5)
        
        # Enhance with article titles
        enhanced_revisions = []
        for rev in revisions:
            article = await db["articles"].find_one({"_id": rev["articleId"]})
            article_title = article["title"] if article else "Unknown Article"
            
            enhanced_revisions.append({
                **rev,
                "articleTitle": article_title
            })
        
        enhanced_proposals = []
        for prop in proposals:
            article = await db["articles"].find_one({"_id": prop["articleId"]})
            article_title = article["title"] if article else "Unknown Article"
            
            enhanced_proposals.append({
                **prop,
                "articleTitle": article_title
            })
        
        # Check if current user is the profile owner or an admin
        current_user = None
        is_self = False
        is_admin = False
        
        try:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.replace("Bearer ", "")
                from dependencies.auth import get_current_user
                current_user = await get_current_user(token=token, db=db)
                
                is_self = str(current_user["_id"]) == user_id
                is_admin = current_user["role"] == "admin"
        except:
            pass
        
        # Render template
        return templates.TemplateResponse(
            "user_profile.html",
            {
                "request": request,
                "user": user,
                "articles": articles,
                "revisions": enhanced_revisions,
                "proposals": enhanced_proposals,
                "is_self": is_self,
                "is_admin": is_admin,
                "current_user": current_user,
                "active_page": "profile"  # Set active page for navigation highlighting
            }
        )
    except Exception as e:
        logger.error(f"Error displaying user profile: {e}")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": str(e)},
            status_code=500
        )

@router.get("/users/{user_id}/edit", response_class=HTMLResponse)
async def edit_user_profile_page(
    request: Request,
    user_id: str,
    db=Depends(get_db)
):
    """
    Render the user profile editing page.
    """
    templates = request.app.state.templates
    
    try:
        # Check if user exists
        if not ObjectId.is_valid(user_id):
            return templates.TemplateResponse(
                "404.html",
                {"request": request, "message": "Invalid user ID"},
                status_code=404
            )
        
        user = await db["users"].find_one({"_id": ObjectId(user_id)})
        if not user:
            return templates.TemplateResponse(
                "404.html",
                {"request": request, "message": "User not found"},
                status_code=404
            )
        
        # Remove sensitive info
        if "passwordHash" in user:
            del user["passwordHash"]
        
        # Check if current user is the profile owner or an admin
        current_user = None
        is_self = False
        is_admin = False
        
        try:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.replace("Bearer ", "")
                from dependencies.auth import get_current_user
                current_user = await get_current_user(token=token, db=db)
                
                is_self = str(current_user["_id"]) == user_id
                is_admin = current_user["role"] == "admin"
        except:
            pass
        
        # Only allow editing if user is the profile owner or an admin
        if not is_self and not is_admin:
            return templates.TemplateResponse(
                "403.html",
                {"request": request, "message": "You do not have permission to edit this profile"},
                status_code=403
            )
        
        # Render template
        return templates.TemplateResponse(
            "profile_edit.html",  # This template works for both paths
            {
                "request": request,
                "user": user,
                "is_self": is_self,
                "is_admin": is_admin,
                "current_user": current_user,
                "active_page": "profile"  # Set active page for navigation highlighting
            }
        )
    except Exception as e:
        logger.error(f"Error displaying edit profile page: {e}")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": str(e)},
            status_code=500
        )

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
    
    # Try to get current user from authentication token
    current_user = None
    try:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")
            from dependencies.auth import get_current_user
            current_user = await get_current_user(token=token, db=db)
    except Exception as e:
        logger.debug(f"Failed to get current user: {e}")
        # This is expected if not logged in
    
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
            # Not logged in, show login required page instead of redirecting
            return templates.TemplateResponse(
                "login_required.html",
                {
                    "request": request, 
                    "redirect_to": "/profile",
                    "active_page": "profile"
                }
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
        "user_profile.html",  # Use the standard user profile template
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
            "badges": [],  # Future feature
            "active_page": "profile"  # Set active page for navigation highlighting
        }
    )

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
    current_user = None
    try:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")
            from dependencies.auth import get_current_user
            current_user = await get_current_user(token=token, db=db)
    except Exception as e:
        logger.debug(f"Failed to get current user for profile edit: {e}")
        # This is expected if not logged in
    
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
    current_user = None
    try:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")
            from dependencies.auth import get_current_user
            current_user = await get_current_user(token=token, db=db)
    except Exception as e:
        logger.debug(f"Failed to get current user for profile settings: {e}")
        # This is expected if not logged in
    
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
