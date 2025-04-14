"""
Additional media-related routes for the Kryptopedia application.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, List

from dependencies import get_db, get_current_user

router = APIRouter()

@router.get("/my-uploads")
async def get_user_uploads(
    current_user: Dict[str, Any] = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db=Depends(get_db)
):
    """
    Get the current user's uploaded media files.
    """
    try:
        # Query the database for user's uploads
        cursor = db["media"].find(
            {"uploadedBy": current_user["_id"]}
        ).sort("uploadedAt", -1).skip(skip).limit(limit)
        
        # Convert cursor to list
        uploads = await cursor.to_list(length=limit)
        
        # Return the uploads
        return uploads
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve uploads: {str(e)}")
