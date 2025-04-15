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
    
    Accepts:
        - content: The wiki markup content
        - summary: Optional article summary for short description
        - proposalSummary: Optional context for proposal previews
    """
    try:
        content = data.get("content")
        if not content:
            raise HTTPException(status_code=400, detail="Content is required")
        
        # Get optional summary/description if provided
        summary = data.get("summary")
        
        # If summary is provided, add short description markup to content
        # This way the server handles the markup transformation
        if summary and not content.startswith("{{Short description|"):
            content = f"{{{{Short description|{summary}}}}}\n\n{content}"
        
        # Parse wiki markup
        html, short_description = parse_wiki_markup(content)
        
        # Prepare response with both HTML and extracted short description
        response = {
            "html": html,
            "short_description": short_description
        }
        
        # If this is a proposal preview, add context
        proposal_summary = data.get("proposalSummary")
        if proposal_summary:
            response["proposal_context"] = {
                "summary": proposal_summary
            }
        
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating preview: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate preview: {str(e)}")
