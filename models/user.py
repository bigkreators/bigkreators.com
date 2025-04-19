# File: models/user.py
"""
User-related models for the Kryptopedia application.
"""
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr, validator, ConfigDict
from typing import Dict, List, Optional, Any
from .base import DBModel, PyObjectId

class UserContributions(BaseModel):
    """
    Model for user contribution statistics.
    """
    articlesCreated: int = 0
    editsPerformed: int = 0
    proposalsSubmitted: int = 0
    rewardsReceived: int = 0
    upvotesReceived: int = 0  # Added field to track upvotes received

class UserBase(BaseModel):
    """
    Base model for user data.
    """
    username: str
    email: EmailStr
    displayName: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    
    @validator('username')
    def username_must_be_valid(cls, v):
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters')
        if not v.isalnum():
            raise ValueError('Username must contain only alphanumeric characters')
        return v

class UserCreate(UserBase):
    """
    Model for creating a new user.
    """
    password: str
    
    @validator('password')
    def password_must_be_strong(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v

class UserLogin(BaseModel):
    """
    Model for user login.
    """
    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    """
    Model for updating user data.
    """
    displayName: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    currentPassword: Optional[str] = None
    emailPreferences: Optional[Dict[str, bool]] = None

class User(UserBase, DBModel):
    """
    Complete user model with database fields.
    """
    passwordHash: str
    role: str = "user"  # "user", "editor", or "admin"
    joinDate: datetime = Field(default_factory=datetime.now)
    lastLogin: Optional[datetime] = None
    emailPreferences: Dict[str, bool] = Field(default_factory=lambda: {
        "articleUpdates": True,
        "proposalUpdates": True,
        "rewards": True,
        "newsletter": True
    })
    contributions: UserContributions = Field(default_factory=UserContributions)
    
    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "_id": "60d21b4967d0d8992e610c85",
                "username": "johndoe",
                "email": "john.doe@example.com",
                "displayName": "John Doe",
                "passwordHash": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
                "role": "user",
                "bio": "I'm a crypto enthusiast",
                "location": "New York",
                "website": "https://johndoe.com",
                "joinDate": "2021-06-22T10:00:00",
                "lastLogin": "2021-06-23T15:30:00",
                "emailPreferences": {
                    "articleUpdates": True,
                    "proposalUpdates": True,
                    "rewards": True,
                    "newsletter": True
                },
                "contributions": {
                    "articlesCreated": 5,
                    "editsPerformed": 10,
                    "proposalsSubmitted": 3,
                    "rewardsReceived": 7,
                    "upvotesReceived": 42
                }
            }
        }
    )

class Token(BaseModel):
    """
    Model for authentication token.
    """
    access_token: str
    token_type: str

class TokenData(BaseModel):
    """
    Model for token payload data.
    """
    username: Optional[str] = None
    sub: str  # User ID
    role: str = "user"  # User role for authorization
