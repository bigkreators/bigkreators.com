"""
Preview-related routes for the Kryptopedia application.
"""
from fastapi import APIRouter, Depends, HTTPException, Body
from typing import Dict, Any
import logging

from utils.wiki_parser import parse_wiki_markup
from dependencies import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/preview")
async def preview_wiki_markup(
    data: Dict[str, Any] = Body(...),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Generate HTML preview of wiki markup.
    """
    try:
        content = data.get("content")
        if not content:
            raise HTTPException(status_code=400, detail="Content is required")
        
        # Parse wiki markup
        html, short_description = parse_wiki_markup(content)
        
        return {
            "html": html,
            "short_description": short_description
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating preview: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate preview: {str(e)}")
