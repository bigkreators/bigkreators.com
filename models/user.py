"""
User-related models for the Kryptopedia application.
"""
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Dict, Optional, List, Annotated
from .base import DBModel, PyObjectId

class UserBase(BaseModel):
    """
    Base model for user data.
    """
    username: str
    email: EmailStr

class UserCreate(UserBase):
    """
    Model for creating a new user.
    """
    password: str

class UserLogin(BaseModel):
    """
    Model for user login credentials.
    """
    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    """
    Model for updating user data.
    """
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None

class UserContributions(BaseModel):
    """
    Model for user contribution statistics.
    """
    articles_created: int = Field(default=0, alias="articlesCreated")
    edits_performed: int = Field(default=0, alias="editsPerformed")
    rewards_received: int = Field(default=0, alias="rewardsReceived")

    model_config = ConfigDict(
        populate_by_name=True
    )

class User(UserBase, DBModel):
    """
    Complete user model with database fields.
    """
    role: str = "user"
    join_date: datetime = Field(default_factory=datetime.now, alias="joinDate")
    last_login: Optional[datetime] = Field(default=None, alias="lastLogin")
    reputation: int = 0
    contributions: UserContributions = Field(default_factory=UserContributions)

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "_id": "60d21b4967d0d8992e610c85",
                "username": "johndoe",
                "email": "johndoe@example.com",
                "role": "user",
                "joinDate": "2021-06-22T10:00:00",
                "lastLogin": "2021-06-23T15:30:00",
                "reputation": 100,
                "contributions": {
                    "articlesCreated": 5,
                    "editsPerformed": 10,
                    "rewardsReceived": 3
                }
            }
        }
    )

class Token(BaseModel):
    """
    Model for authentication tokens.
    """
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime

class TokenData(BaseModel):
    """
    Model for JWT token payload data.
    """
    user_id: Optional[str] = None
