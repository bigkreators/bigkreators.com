# File: models/category.py
"""
Category model for the Kryptopedia application.
Categories are treated as special namespace pages with auto-populated content listings.
"""
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, computed_field
from typing import Dict, List, Optional, Any, Union
from .base import DBModel, PyObjectId

class CategoryBase(BaseModel):
    """
    Base model for category data.
    Categories have their own content (description) and automatically list articles.
    """
    name: str = Field(..., description="Category name (without Category: prefix)")
    description: str = Field(..., description="Category description content")
    parent_category: Optional[str] = Field(None, description="Parent category for hierarchical organization")
    sort_key: Optional[str] = Field(None, description="Custom sort key for category ordering")
    
    @computed_field
    @property
    def full_title(self) -> str:
        """Get the full title including Category: prefix."""
        return f"Category:{self.name}"
    
    @computed_field
    @property 
    def url_path(self) -> str:
        """Get the URL path for this category."""
        return f"/categories/{self.name.replace(' ', '_')}"

    model_config = ConfigDict(
        populate_by_name=True
    )

class CategoryCreate(CategoryBase):
    """
    Model for creating a new category.
    """
    pass

class CategoryUpdate(BaseModel):
    """
    Model for updating category data.
    """
    name: Optional[str] = None
    description: Optional[str] = None
    parent_category: Optional[str] = None
    sort_key: Optional[str] = None

    model_config = ConfigDict(
        populate_by_name=True
    )

class Category(CategoryBase, DBModel):
    """
    Complete category model with database fields.
    """
    slug: str = Field(..., description="URL-friendly slug")
    created_by: PyObjectId = Field(..., alias="createdBy")
    created_at: datetime = Field(default_factory=datetime.now, alias="createdAt")
    last_updated_at: Optional[datetime] = Field(default=None, alias="lastUpdatedAt")
    last_updated_by: Optional[PyObjectId] = Field(default=None, alias="lastUpdatedBy")
    article_count: int = Field(default=0, description="Number of articles in this category")
    subcategory_count: int = Field(default=0, description="Number of subcategories")
    status: str = Field(default="active", description="Category status: active, hidden, deleted")

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "_id": "60d21b4967d0d8992e610c85",
                "name": "Blockchain Technology",
                "description": "Articles about blockchain technology, cryptocurrencies, and distributed ledger systems.",
                "slug": "blockchain-technology",
                "full_title": "Category:Blockchain Technology",
                "url_path": "/categories/Blockchain_Technology",
                "article_count": 15,
                "subcategory_count": 3,
                "status": "active",
                "createdBy": "60d21b4967d0d8992e610c85",
                "createdAt": "2024-01-15T10:30:00Z"
            }
        }
    )

class CategoryWithArticles(Category):
    """
    Category model that includes populated articles list.
    """
    articles: List[Dict[str, Any]] = Field(default_factory=list, description="Articles in this category")
    subcategories: List[Dict[str, Any]] = Field(default_factory=list, description="Subcategories")
    
    model_config = ConfigDict(
        populate_by_name=True
    )
