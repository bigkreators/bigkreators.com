"""
Proposal-related models for the Cryptopedia application.
"""
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional
from .base import DBModel, PyObjectId

class ProposalCreate(BaseModel):
    """
    Model for creating a new edit proposal.
    """
    content: str
    summary: str

class Proposal(ProposalCreate, DBModel):
    """
    Complete proposal model with database fields.
    """
    article_id: PyObjectId = Field(..., alias="articleId")
    proposed_by: PyObjectId = Field(..., alias="proposedBy")
    proposed_at: datetime = Field(default_factory=datetime.now, alias="proposedAt")
    status: str = "pending"  # Options: pending, approved, rejected
    reviewed_by: Optional[PyObjectId] = Field(default=None, alias="reviewedBy")
    reviewed_at: Optional[datetime] = Field(default=None, alias="reviewedAt")
    review_comment: Optional[str] = Field(default=None, alias="reviewComment")

    class Config:
        allow_population_by_field_name = True
        schema_extra = {
            "example": {
                "_id": "60d21b4967d0d8992e610c85",
                "articleId": "60d21b4967d0d8992e610c86",
                "content": "<h1>Introduction to Cryptography</h1><p>This is a proposed update to cryptography...</p>",
                "summary": "Updated the introduction section with clearer explanation",
                "proposedBy": "60d21b4967d0d8992e610c87",
                "proposedAt": "2021-06-22T10:00:00",
                "status": "pending",
                "reviewedBy": None,
                "reviewedAt": None,
                "reviewComment": None
            }
        }

class ProposalWithMetadata(Proposal):
    """
    Proposal model with additional metadata for display.
    """
    article_title: str = Field(..., alias="articleTitle")
    proposer_username: str = Field(..., alias="proposerUsername")
    reviewer_username: Optional[str] = Field(default=None, alias="reviewerUsername")

    class Config:
        allow_population_by_field_name = True
