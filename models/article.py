# File: models/article.py
"""
Article-related models for the Kryptopedia application.
"""
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, List, Optional, Any, Union
from .base import DBModel, PyObjectId

class ArticleMetadata(BaseModel):
    """
    Model for article metadata flags.
    """
    has_audio: bool = Field(default=False, alias="hasAudio")
    has_special_symbols: bool = Field(default=False, alias="hasSpecialSymbols")
    contains_made_up_content: bool = Field(default=False, alias="containsMadeUpContent")

    model_config = ConfigDict(
        populate_by_name=True
    )

class ArticleBase(BaseModel):
    """
    Base model for article data.
    """
    title: str
    content: str
    summary: str
    categories: List[str] = []
    tags: List[str] = []
    metadata: Union[ArticleMetadata, Dict[str, Any]] = Field(default_factory=ArticleMetadata)

    model_config = ConfigDict(
        populate_by_name=True
    )

class ArticleCreate(ArticleBase):
    """
    Model for creating a new article.
    """
    pass

# File: models/article.py (partial update)

class ArticleUpdate(BaseModel):
    """
    Model for updating article data.
    """
    title: Optional[str] = None
    content: Optional[str] = None
    summary: Optional[str] = None
    categories: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Union[ArticleMetadata, Dict[str, Any]]] = None
    editComment: Optional[str] = None  # Comment describing the edit
    status: Optional[str] = None  # Status field: "published", "draft", "hidden", "archived"

    model_config = ConfigDict(
        populate_by_name=True
    )

class Article(ArticleBase, DBModel):
    """
    Complete article model with database fields.
    """
    slug: str
    created_by: PyObjectId = Field(..., alias="createdBy")
    created_at: datetime = Field(default_factory=datetime.now, alias="createdAt")
    last_updated_at: Optional[datetime] = Field(default=None, alias="lastUpdatedAt")
    last_updated_by: Optional[PyObjectId] = Field(default=None, alias="lastUpdatedBy")
    featured_until: Optional[datetime] = Field(default=None, alias="featuredUntil")
    status: str = "published"
    views: int = 0

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "_id": "60d21b4967d0d8992e610c85",
                "title": "Introduction to Cryptography",
                "slug": "introduction-to-cryptography-1624356169",
                "content": "<h1>Introduction to Cryptography</h1><p>This is an introduction to cryptography...</p>",
                "summary": "A beginner's guide to cryptography concepts and techniques.",
                "categories": ["Cryptography", "Security"],
                "tags": ["beginner", "encryption", "security"],
                "metadata": {
                    "hasAudio": False,
                    "hasSpecialSymbols": True,
                    "containsMadeUpContent": False
                },
                "createdBy": "60d21b4967d0d8992e610c85",
                "createdAt": "2021-06-22T10:00:00",
                "lastUpdatedAt": "2021-06-23T15:30:00",
                "lastUpdatedBy": "60d21b4967d0d8992e610c86",
                "featuredUntil": "2021-07-22T10:00:00",
                "status": "published",
                "views": 150
            }
        }
    )

class ArticleWithCreator(Article):
    """
    Article model with creator information included.
    """
    creator_username: str = Field(..., alias="creatorUsername")
    creator_reputation: int = Field(..., alias="creatorReputation")

    model_config = ConfigDict(
        populate_by_name=True
    )
