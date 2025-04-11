"""
Reward-related models for the Kryptopedia application.
"""
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Annotated
from .base import DBModel, PyObjectId

class RewardCreate(BaseModel):
    """
    Model for creating a new reward.
    """
    reward_type: str = Field(..., alias="rewardType")  # Options: helpful, insightful, comprehensive
    points: int

    model_config = ConfigDict(
        populate_by_name=True
    )

class Reward(RewardCreate, DBModel):
    """
    Complete reward model with database fields.
    """
    article_id: PyObjectId = Field(..., alias="articleId")
    revision_id: Optional[PyObjectId] = Field(default=None, alias="revisionId")
    rewarded_user: PyObjectId = Field(..., alias="rewardedUser")
    rewarded_by: PyObjectId = Field(..., alias="rewardedBy")
    rewarded_at: datetime = Field(default_factory=datetime.now, alias="rewardedAt")

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "_id": "60d21b4967d0d8992e610c85",
                "articleId": "60d21b4967d0d8992e610c86",
                "revisionId": "60d21b4967d0d8992e610c87",
                "rewardType": "insightful",
                "points": 10,
                "rewardedUser": "60d21b4967d0d8992e610c88",
                "rewardedBy": "60d21b4967d0d8992e610c89",
                "rewardedAt": "2021-06-22T10:00:00"
            }
        }
    )

class RewardWithMetadata(Reward):
    """
    Reward model with additional metadata for display.
    """
    article_title: str = Field(..., alias="articleTitle")
    rewarded_username: str = Field(..., alias="rewardedUsername")
    rewarder_username: str = Field(..., alias="rewarderUsername")

    model_config = ConfigDict(
        populate_by_name=True
    )
