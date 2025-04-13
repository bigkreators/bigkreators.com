# File: routes/auth.py (Updated)
"""
Authentication-related routes for the Kryptopedia application.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Body, Form
from fastapi.security import OAuth2PasswordRequestForm
from typing import Dict, Any
from datetime import datetime, timedelta
from bson import ObjectId
import logging

# Import models explicitly without using relative imports
from models.user import UserCreate, User, Token, TokenData, UserUpdate
from dependencies.database import get_db
from dependencies.auth import get_current_user
from utils.security import hash_password, verify_password, create_access_token
import config

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/register", response_model=Dict[str, Any])
async def register_user(user: UserCreate = Body(...), db=Depends(get_db)):
    """
    Register a new user.
    """
    try:
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
            },
            # Add default profile fields
            "displayName": None,
            "bio": None, 
            "location": None,
            "website": None,
            "emailPreferences": {
                "articleUpdates": True,
                "proposalUpdates": True,
                "rewards": True,
                "newsletter": False
            },
            "badges": []
        }
        
        # Insert into database
        result = await db["users"].insert_one(new_user)
        
        return {"message": "User registered successfully", "userId": str(result.inserted_id)}
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error registering user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

@router.post("/login", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db=Depends(get_db)):
    """
    Authenticate user and provide access token.
    OAuth2PasswordRequestForm expects:
    - username: string (can be email)
    - password: string
    """
    try:
        # Log received data for debugging (exclude password)
        logger.debug(f"Login attempt for username: {form_data.username}")
        
        # Find user by username
        user = await db["users"].find_one({"username": form_data.username})
        
        # If user not found, try email
        if not user:
            user = await db["users"].find_one({"email": form_data.username})
        
        # Verify user exists and password is correct
        if not user or not verify_password(form_data.password, user["passwordHash"]):
            logger.warning(f"Failed login attempt for: {form_data.username}")
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
        
        logger.info(f"Successful login for user: {user['username']}")
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_at": expires_at
        }
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error during login: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )

@router.get("/me", response_model=Dict[str, Any])
async def get_current_user_info(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Get information about the currently authenticated user.
    """
    try:
        # Make a copy of the user data to avoid modifying the original
        user_info = dict(current_user)
        
        # Remove sensitive data
        if "passwordHash" in user_info:
            del user_info["passwordHash"]
        
        # Convert ObjectId to string for JSON serialization
        user_info["_id"] = str(user_info["_id"])
        
        return user_info
    except Exception as e:
        logger.error(f"Error retrieving user info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve user information: {str(e)}"
        )

@router.put("/me", response_model=Dict[str, Any])
async def update_current_user(
    user_update: UserUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db=Depends(get_db)
):
    """
    Update information for the currently authenticated user.
    """
    try:
        # Verify password if provided
        if user_update.current_password:
            if not verify_password(user_update.current_password, current_user["passwordHash"]):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Current password is incorrect"
                )
        else:
            # Password required for any update
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is required to update account information"
            )
        
        # Prepare update data
        update_data = {}
        
        # Basic fields
        if user_update.email and user_update.email != current_user["email"]:
            # Check if email is already in use
            existing_user = await db["users"].find_one({"email": user_update.email})
            if existing_user and str(existing_user["_id"]) != str(current_user["_id"]):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email is already in use"
                )
            update_data["email"] = user_update.email
        
        # Extended profile fields
        if user_update.display_name is not None:
            update_data["displayName"] = user_update.display_name
            
        if user_update.bio is not None:
            update_data["bio"] = user_update.bio
            
        if user_update.location is not None:
            update_data["location"] = user_update.location
            
        if user_update.website is not None:
            update_data["website"] = user_update.website
        
        # Password update
        if user_update.password:
            update_data["passwordHash"] = hash_password(user_update.password)
        
        # Email preferences
        if user_update.email_preferences:
            update_data["emailPreferences"] = user_update.email_preferences.dict(by_alias=True)
        
        # Only proceed if there are updates
        if not update_data:
            return {"message": "No changes made"}
        
        # Update in database
        result = await db["users"].update_one(
            {"_id": current_user["_id"]},
            {"$set": update_data}
        )
        
        if result.modified_count == 0:
            return {"message": "No changes were applied"}
        
        # Get updated user data
        updated_user = await db["users"].find_one({"_id": current_user["_id"]})
        
        # Remove sensitive data
        if "passwordHash" in updated_user:
            del updated_user["passwordHash"]
        
        # Convert ObjectId to string
        updated_user["_id"] = str(updated_user["_id"])
        
        return {
            "message": "User information updated successfully",
            "user": updated_user
        }
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error updating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user information: {str(e)}"
        )

@router.post("/logout")
async def logout():
    """
    Logout endpoint.
    
    Note: Since we're using JWT tokens stored in localStorage,
    actual logout happens on the client side by removing the token.
    This endpoint is mainly for logging purposes.
    """
    return {"message": "Successfully logged out"}
