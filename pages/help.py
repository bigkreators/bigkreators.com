# File: pages/help.py
"""
Help page routes for the Kryptopedia application.
"""
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
import logging

from dependencies import get_db

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/help", response_class=HTMLResponse)
async def help_page(request: Request, db=Depends(get_db)):
    """
    Render the main help page.
    """
    templates = request.app.state.templates
    
    return templates.TemplateResponse(
        "help.html",
        {"request": request}
    )

@router.get("/help/formatting", response_class=HTMLResponse)
async def formatting_guide(request: Request):
    """
    Render the formatting guide help page.
    """
    templates = request.app.state.templates
    
    return templates.TemplateResponse(
        "help_formatting.html",
        {"request": request}
    )

@router.get("/help/references", response_class=HTMLResponse)
async def references_guide(request: Request):
    """
    Render the references guide help page.
    """
    templates = request.app.state.templates
    
    return templates.TemplateResponse(
        "help_references.html",
        {"request": request}
    )

@router.get("/help/media", response_class=HTMLResponse)
async def media_guide(request: Request):
    """
    Render the media guide help page.
    """
    templates = request.app.state.templates
    
    return templates.TemplateResponse(
        "help_media.html",
        {"request": request}
    )

@router.get("/help/categories", response_class=HTMLResponse)
async def categories_guide(request: Request):
    """
    Render the categories guide help page.
    """
    templates = request.app.state.templates
    
    return templates.TemplateResponse(
        "help_categories.html",
        {"request": request}
    )

