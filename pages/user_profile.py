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
                "current_user": current_user
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
            "user_profile_edit.html",
            {
                "request": request,
                "user": user,
                "is_self": is_self,
                "is_admin": is_admin,
                "current_user": current_user
            }
        )
    except Exception as e:
        logger.error(f"Error displaying edit profile page: {e}")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": str(e)},
