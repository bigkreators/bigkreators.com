"""
Media-related routes for the Cryptopedia application.
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Path
from fastapi.responses import Response
from typing import Dict, Any, List, Optional
import os

from models import Media
from dependencies import get_db, get_storage, get_current_user

router = APIRouter()

@router.post("/upload", response_model=Media)
async def upload_media(
    file: UploadFile = File(...),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db=Depends(get_db),
    storage=Depends(get_storage)
):
    """
    Upload a media file.
    """
    # Validate file size (limit to 10MB)
    MAX_SIZE = 10 * 1024 * 1024  # 10MB
    content = await file.read()
    if len(content) > MAX_SIZE:
        raise HTTPException(status_code=400, detail="File size exceeds the 10MB limit")
    
    # Reset file stream position
    await file.seek(0)
    
    # Generate unique filename
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    
    # Save file using storage service
    try:
        file_url = await storage.save_file(content, unique_filename, file.content_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")
    
    # Create metadata based on file type
    metadata = {}
    
    # For audio files
    if file.content_type.startswith("audio/"):
        metadata = {"duration": 0}  # Placeholder - would need audio analysis library
    
    # For image files
    elif file.content_type.startswith("image/"):
        metadata = {"dimensions": {"width": 0, "height": 0}}  # Placeholder - would need image analysis library
    
    # Create media entry
    new_media = {
        "filename": unique_filename,
        "originalName": file.filename,
        "mimeType": file.content_type,
        "size": len(content),
        "path": file_url,
        "uploadedBy": current_user["_id"],
        "uploadedAt": None,  # Will be set by database default
        "metadata": metadata,
        "usedInArticles": []
    }
    
    # Insert into database
    result = await db["media"].insert_one(new_media)
    
    # Return created media
    created_media = await db["media"].find_one({"_id": result.inserted_id})
    return created_media

@router.get("/{id}", response_model=Media)
async def get_media(
    id: str = Path(..., description="Media ID"),
    db=Depends(get_db)
):
    """
    Get media file metadata.
    """
    # Check if media exists
    if not id:
        raise HTTPException(status_code=400, detail="Invalid media ID")
    
    # Try to find by ObjectId if valid
    if len(id) == 24 and all(c in "0123456789abcdef" for c in id.lower()):
        from bson import ObjectId
        media = await db["media"].find_one({"_id": ObjectId(id)})
    else:
        # Try to find by filename
        media = await db["media"].find_one({"filename": id})
    
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")
    
    return media

@router.get("/{filename}/content")
async def get_media_content(
    filename: str = Path(..., description="Media filename"),
    db=Depends(get_db),
    storage=Depends(get_storage)
):
    """
    Get media file content directly.
    """
    # Find media by filename
    media = await db["media"].find_one({"filename": filename})
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")
    
    # Get file content from storage
    content = await storage.get_file(filename)
    if not content:
        raise HTTPException(status_code=404, detail="File content not found")
    
    # Determine content type
    content_type = media.get("mimeType", "application/octet-stream")
    
    # Return file content with proper content type
    return Response(content=content, media_type=content_type)

@router.delete("/{id}")
async def delete_media(
    id: str = Path(..., description="Media ID"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db=Depends(get_db),
    storage=Depends(get_storage)
):
    """
    Delete a media file.
    """
    # Only admin or media owner can delete
    from bson import ObjectId
    
    # Check if ID is valid
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid media ID")
    
    # Get media
    media = await db["media"].find_one({"_id": ObjectId(id)})
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")
    
    # Check permissions
    is_admin = current_user["role"] == "admin"
    is_owner = str(media["uploadedBy"]) == str(current_user["_id"])
    
    if not (is_admin or is_owner):
        raise HTTPException(status_code=403, detail="Not authorized to delete this media")
    
    # Check if file is in use
    if media.get("usedInArticles") and len(media["usedInArticles"]) > 0:
        if not is_admin:
            raise HTTPException(
                status_code=400, 
                detail="Cannot delete media that is in use by articles. Contact an admin."
            )
    
    # Delete from storage
    filename = media["filename"]
    deleted = await storage.delete_file(filename)
    
    if not deleted:
        raise HTTPException(status_code=500, detail="Failed to delete file from storage")
    
    # Delete from database
    await db["media"].delete_one({"_id": ObjectId(id)})
    
    return {"message": "Media deleted successfully"}
