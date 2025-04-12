"""
Authentication-related routes for the Kryptopedia application.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordRequestForm
from typing import Dict, Any
from datetime import datetime, timedelta
from bson import ObjectId

from models import UserCreate, User, Token
from dependencies import get_db, get_current_user  # Added import for get_current_user
from utils.security import hash_password, verify_password, create_access_token
import config

router = APIRouter()

@router.post("/register", response_model=Dict[str, Any])
async def register_user(user: UserCreate = Body(...), db=Depends(get_db)):
    """
    Register a new user.
    """
    # Check if username already exists
    existing_user = await db["users"].find_one({"username": user.username})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email already exists
    existing_email = await db["users"].find_one({"email": user.email})
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash password
    hashed_password = hash_password(user.password)
    
    # Create user document
    new_user = {
        "username": user.username,
        "email": user.email,
        "passwordHash": hashed_password,
        "role": "user",
        "joinDate": datetime.now(),
        "lastLogin": None,
        "reputation": 0,
        "contributions": {
            "articlesCreated": 0,
            "editsPerformed": 0,
            "rewardsReceived": 0
        }
    }
    
    # Insert into database
    result = await db["users"].insert_one(new_user)
    
    return {"message": "User registered successfully", "userId": str(result.inserted_id)}

@router.post("/login", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db=Depends(get_db)):
    """
    Authenticate user and provide access token.
    OAuth2PasswordRequestForm expects:
    - username: string
    - password: string
    """
    # Find user by username
    user = await db["users"].find_one({"username": form_data.username})
    
    # If user not found, try email
    if not user:
        user = await db["users"].find_one({"email": form_data.username})
    
    # Verify user exists and password is correct
    if not user or not verify_password(form_data.password, user["passwordHash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(hours=config.JWT_EXPIRATION_HOURS)
    access_token, expires_at = create_access_token(
        data={"sub": str(user["_id"])},
        expires_delta=access_token_expires
    )
    
    # Update last login
    await db["users"].update_one(
        {"_id": user["_id"]},
        {"$set": {"lastLogin": datetime.now()}}
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_at": expires_at
    }

@router.get("/me", response_model=Dict[str, Any])
async def get_current_user_info(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Get information about the currently authenticated user.
    """
    # Remove sensitive data
    if "passwordHash" in current_user:
        del current_user["passwordHash"]
    
    # Convert ObjectId to string for JSON serialization
    current_user["_id"] = str(current_user["_id"])
    
    return current_user
