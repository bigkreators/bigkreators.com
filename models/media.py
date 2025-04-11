"""
Media-related models for the Kryptopedia application.
"""
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, List, Any, Optional, Annotated
from .base import DBModel, PyObjectId

class MediaMetadata(BaseModel):
    """
    Model for media metadata.
    """
    duration: Optional[int] = None  # For audio/video files, in seconds
    dimensions: Optional[Dict[str, int]] = None  # For images, width/height
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "duration": 120,  # 2 minutes
                "dimensions": {
                    "width": 1920,
                    "height": 1080
                }
            }
        }
    )

class MediaCreate(BaseModel):
    """
    Model for creating a new media entry.
    """
    filename: str
    original_name: str = Field(..., alias="originalName")
    mime_type: str = Field(..., alias="mimeType")
    size: int
    path: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(
        populate_by_name=True
    )

class Media(MediaCreate, DBModel):
    """
    Complete media model with database fields.
    """
    uploaded_by: PyObjectId = Field(..., alias="uploadedBy")
    uploaded_at: datetime = Field(default_factory=datetime.now, alias="uploadedAt")
    used_in_articles: List[PyObjectId] = Field(default_factory=list, alias="usedInArticles")

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "_id": "60d21b4967d0d8992e610c85",
                "filename": "1624356169-example.jpg",
                "originalName": "example.jpg",
                "mimeType": "image/jpeg",
                "size": 1024000,
                "path": "/media/1624356169-example.jpg",
                "metadata": {
                    "dimensions": {
                        "width": 1920,
                        "height": 1080
                    }
                },
                "uploadedBy": "60d21b4967d0d8992e610c86",
                "uploadedAt": "2021-06-22T10:00:00",
                "usedInArticles": [
                    "60d21b4967d0d8992e610c87",
                    "60d21b4967d0d8992e610c88"
                ]
            }
        }
    )

class MediaWithUploader(Media):
    """
    Media model with uploader information included.
    """
    uploader_username: str = Field(..., alias="uploaderUsername")

    model_config = ConfigDict(
        populate_by_name=True
    )
