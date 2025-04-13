"""
Error page routes for the Kryptopedia application.
"""
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
import logging

from dependencies import get_db

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/404", response_class=HTMLResponse)
async def not_found_page(request: Request):
    """
    Render the 404 page.
    """
    templates = request.app.state.templates
    return templates.TemplateResponse(
        "404.html",
        {"request": request, "message": "Page not found"},
        status_code=404
    )

@router.get("/403", response_class=HTMLResponse)
async def forbidden_page(request: Request):
    """
    Render the 403 page.
    """
    templates = request.app.state.templates
    return templates.TemplateResponse(
        "403.html",
        {"request": request, "message": "Access forbidden"},
        status_code=403
    )

@router.get("/500", response_class=HTMLResponse)
async def server_error_page(request: Request):
    """
    Render the 500 page.
    """
    templates = request.app.state.templates
    return templates.TemplateResponse(
        "error.html",
        {"request": request, "message": "Internal server error"},
        status_code=500
    )

@router.get("/maintenance", response_class=HTMLResponse)
async def maintenance_page(request: Request):
    """
    Render the maintenance page.
    """
    templates = request.app.state.templates
    return templates.TemplateResponse(
        "maintenance.html",
        {"request": request}
    )

# Include in the main app to handle error cases
def add_error_handlers(app):
    """
    Add error handlers to the FastAPI app.
    """
    @app.exception_handler(404)
    async def custom_404_handler(request, exc):
        templates = request.app.state.templates
        return templates.TemplateResponse(
            "404.html",
            {"request": request, "message": "Page not found"},
            status_code=404
        )
    
    @app.exception_handler(403)
    async def custom_403_handler(request, exc):
        templates = request.app.state.templates
        return templates.TemplateResponse(
            "403.html",
            {"request": request, "message": "Access forbidden"},
            status_code=403
        )
    
    @app.exception_handler(500)
    async def custom_500_handler(request, exc):
        templates = request.app.state.templates
        logger.error(f"Internal server error: {str(exc)}")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": "Internal server error"},
            status_code=500
        )
