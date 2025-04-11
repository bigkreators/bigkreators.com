"""
Revision-related models for the Kryptopedia application.
"""
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Annotated
from .base import DBModel, PyObjectId

class RevisionCreate(BaseModel):
    """
    Model for creating a new revision.
    """
    content: str
    comment: str

class Revision(RevisionCreate, DBModel):
    """
    Complete revision model with database fields.
    """
    article_id: PyObjectId = Field(..., alias="articleId")
    created_by: PyObjectId = Field(..., alias="createdBy")
    created_at: datetime = Field(default_factory=datetime.now, alias="createdAt")
    diff: Optional[str] = None

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "_id": "60d21b4967d0d8992e610c85",
                "articleId": "60d21b4967d0d8992e610c86",
                "content": "<h1>Introduction to Cryptography</h1><p>This is an updated introduction to cryptography...</p>",
                "createdBy": "60d21b4967d0d8992e610c87",
                "createdAt": "2021-06-22T10:00:00",
                "comment": "Updated introduction section",
                "diff": "Diff content here showing changes"
            }
        }
    )

class RevisionWithMetadata(Revision):
    """
    Revision model with additional metadata for display.
    """
    article_title: str = Field(..., alias="articleTitle")
    creator_username: str = Field(..., alias="creatorUsername")

    model_config = ConfigDict(
        populate_by_name=True
    )
