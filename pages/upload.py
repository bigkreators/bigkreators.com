"""
Upload file page routes for the Kryptopedia application.
"""
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
import logging

from dependencies import get_db, get_current_user, get_storage

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/upload-file", response_class=HTMLResponse)
async def upload_file_page(
    request: Request, 
    db=Depends(get_db)
):
    """
    Render the file upload page.
    """
    templates = request.app.state.templates
    
    # Try to get user from request for authentication check
    current_user = None
    try:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")
            from dependencies.auth import get_current_user
            current_user = await get_current_user(token=token, db=db)
    except:
        # This is expected if the user is not logged in
        pass
    
    # User doesn't need to be authenticated to view the page
    # The client-side JavaScript will handle showing the login prompt if needed
    
    return templates.TemplateResponse(
        "upload_file.html",
        {
            "request": request,
            "active_page": "upload",
            "current_user": current_user
        }
    )
