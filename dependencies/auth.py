# File: dependencies/auth.py
"""
Authentication dependencies for FastAPI.
"""
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from typing import Dict, Optional, List
from bson import ObjectId
import logging

import config
from dependencies.database import get_db
from models import TokenData

# Configure logging
logger = logging.getLogger(__name__)

# Initialize OAuth2 password bearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{config.API_PREFIX}/auth/login")

async def get_current_user(authorization: str = Header(None), db=Depends(get_db)):
    """
    Dependency to get the current authenticated user.
    Used in route functions that require authentication.
    
    Args:
        authorization: Auth header containing JWT token
        db: MongoDB database
        
    Returns:
        Dict: The user document
        
    Raises:
        HTTPException: If authentication fails
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Handle case when no token is provided
    if not authorization:
        logger.warning("No authorization header provided")
        raise credentials_exception

    # Extract the token from the authorization header
    try:
        # Check if the authorization header starts with "Bearer "
        if not authorization.startswith("Bearer "):
            logger.warning("Authorization header doesn't start with 'Bearer '")
            raise credentials_exception
        
        token = authorization.replace("Bearer ", "")
        
        # Decode JWT token
        payload = jwt.decode(
            token, 
            config.JWT_SECRET, 
            algorithms=[config.JWT_ALGORITHM]
        )
        user_id = payload.get("sub")
        if user_id is None:
            logger.warning("Token missing 'sub' claim")
            raise credentials_exception
        token_data = TokenData(user_id=user_id)
    except JWTError as e:
        logger.warning(f"JWT error: {e}")
        raise credentials_exception
    except Exception as e:
        logger.error(f"Error decoding token: {e}")
        raise credentials_exception
    
    # Get user from database
    try:
        user = await db["users"].find_one({"_id": ObjectId(token_data.user_id)})
        if user is None:
            logger.warning(f"User not found: {token_data.user_id}")
            raise credentials_exception
        
        # For debugging
        logger.debug(f"Authenticated user: {user['username']}")
        
        return user
    except Exception as e:
        logger.error(f"Database error in get_current_user: {e}")
        raise credentials_exception

async def get_current_admin(current_user: Dict = Depends(get_current_user)):
    """
    Dependency to ensure the current user is an admin.
    Used in route functions that require admin privileges.
    
    Args:
        current_user: The authenticated user
        
    Returns:
        Dict: The user document if they are an admin
        
    Raises:
        HTTPException: If the user is not an admin
    """
    if current_user["role"] != "admin":
        logger.warning(f"Admin access denied for user: {current_user['username']}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions. Admin role required."
        )
    return current_user

async def get_current_editor(current_user: Dict = Depends(get_current_user)):
    """
    Dependency to ensure the current user is an editor or admin.
    Used in route functions that require editor privileges.
    
    Args:
        current_user: The authenticated user
        
    Returns:
        Dict: The user document if they are an editor or admin
        
    Raises:
        HTTPException: If the user is not an editor or admin
    """
    if current_user["role"] not in ["admin", "editor"]:
        logger.warning(f"Editor access denied for user: {current_user['username']}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions. Editor or admin role required."
        )
    return current_user
