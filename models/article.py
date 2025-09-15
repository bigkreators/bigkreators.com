# File: models/article.py
"""
Article-related models for the Kryptopedia application.
"""
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, computed_field
from typing import Dict, List, Optional, Any, Union, Tuple
from .base import DBModel, PyObjectId

# Define supported namespaces
VALID_NAMESPACES = {
    "": "Main",  # Main namespace (articles)
    "Category": "Category",
    "Template": "Template", 
    "Help": "Help",
    "User": "User",
    "File": "File",
    "Talk": "Talk",
    "Kryptopedia": "Kryptopedia",  # Project namespace
}

def parse_title_namespace(full_title: str) -> Tuple[str, str]:
    """
    Parse a title to extract namespace and title.
    
    Args:
        full_title: The full title (e.g., "Category:Blockchain" or "Introduction to Crypto")
        
    Returns:
        Tuple[str, str]: (namespace, title) - namespace is empty string for main namespace
    """
    if ":" in full_title:
        potential_namespace, title = full_title.split(":", 1)
        if potential_namespace in VALID_NAMESPACES:
            return potential_namespace, title.strip()
    
    # No valid namespace found, treat as main namespace
    return "", full_title.strip()

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
    
    # Namespace fields
    namespace: str = Field(default="", description="Article namespace (empty for main)")
    
    @computed_field
    @property
    def full_title(self) -> str:
        """Get the full title including namespace prefix."""
        if self.namespace:
            return f"{self.namespace}:{self.title}"
        return self.title
    
    @computed_field
    @property
    def display_title(self) -> str:
        """Get the display title without namespace prefix."""
        return self.title
    
    @computed_field
    @property
    def namespace_name(self) -> str:
        """Get the human-readable namespace name."""
        return VALID_NAMESPACES.get(self.namespace, "Unknown")
    
    @computed_field
    @property 
    def canonical_url(self) -> str:
        """Get the canonical URL path for this article."""
        from utils.namespace import get_namespace_url
        return get_namespace_url(self.namespace, self.title)

    model_config = ConfigDict(
        populate_by_name=True
    )

class ArticleCreate(ArticleBase):
    """
    Model for creating a new article.
    """
    
    def __init__(self, **data):
        # Parse namespace from title if provided
        if 'title' in data and 'namespace' not in data:
            namespace, title = parse_title_namespace(data['title'])
            data['namespace'] = namespace
            data['title'] = title
        super().__init__(**data)
    
    @computed_field
    @property 
    def canonical_url(self) -> str:
        """Get the canonical URL path for this article."""
        from utils.namespace import get_namespace_url
        return get_namespace_url(self.namespace, self.title)

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
    namespace: Optional[str] = None  # Allow updating namespace

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
    upvotes: int = 0  # Number of upvotes
    downvotes: int = 0  # Number of downvotes

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "_id": "60d21b4967d0d8992e610c85",
                "title": "Introduction to Cryptography",
                "namespace": "",
                "full_title": "Introduction to Cryptography",
                "slug": "introduction-to-cryptography-1624356169",
                "content": "<h1>Introduction to Cryptography</h1><p>This is an introduction to cryptography...</p>",
                "summary": "A beginner's guide to cryptography concepts and techniques.",
                "categories": ["Cryptography", "Technology"],
                "tags": ["crypto", "security", "beginner"],
                "status": "published",
                "views": 42,
                "upvotes": 5,
                "downvotes": 1,
                "createdBy": "60d21b4967d0d8992e610c85",
                "createdAt": "2024-01-15T10:30:00Z"
            }
        }
    )

class ArticleWithCreator(Article):
    """
    Article model with creator information included.
    Used for display purposes when creator details are needed.
    """
    creator_username: str = Field(..., alias="creatorUsername")
    creator_reputation: Optional[int] = Field(default=0, alias="creatorReputation")

    model_config = ConfigDict(
        populate_by_name=True
    )
