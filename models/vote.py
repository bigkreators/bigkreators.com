# File: models/vote.py
"""
Vote model for the Kryptopedia application.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from bson import ObjectId
from .base import PyObjectId

class VoteBase(BaseModel):
    """Base model for votes."""
    voteType: str  # "upvote" or "downvote"

class VoteCreate(VoteBase):
    """Model for creating a vote."""
    pass

class Vote(VoteBase):
    """Complete vote model with database fields."""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    articleId: PyObjectId
    userId: PyObjectId
    createdAt: datetime = Field(default_factory=datetime.now)
    
    class Config:
        allow_population_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str
        }
