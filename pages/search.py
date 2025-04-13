"""
Search page routes.
"""
from fastapi import APIRouter, Request, Depends, Query
from fastapi.responses import HTMLResponse
from typing import Optional
import logging

from dependencies import get_db

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/search", response_class=HTMLResponse)
async def search_page(
    request: Request,
    q: Optional[str] = None,
    db=Depends(get_db)
):
    """
    Render the search results page.
    """
    templates = request.app.state.templates
    results = []
    
    if q:
        # Perform simple text search
        try:
            cursor = db["articles"].find(
                {"$text": {"$search": q}, "status": "published"},
                {"score": {"$meta": "textScore"}}
            ).sort([("score", {"$meta": "textScore"})]).limit(20)
            
            results = await cursor.to_list(length=20)
        except Exception as e:
            logger.error(f"Search error: {str(e)}")
    
    # Render template
    return templates.TemplateResponse(
        "search_results.html",
        {"request": request, "query": q or "", "results": results}
    )
