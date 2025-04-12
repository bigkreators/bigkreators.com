# File: dependencies/auth.py
"""
Authentication dependencies for FastAPI.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from typing import Dict, Any, Optional
from bson import ObjectId
import logging

import config
from dependencies.database import get_db

logger = logging.getLogger(__name__)

# Initialize OAuth2 password bearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{config.API_PREFIX}/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme), db=Depends(get_db)) -> Dict[str, Any]:
    """
    Dependency to get the current authenticated user.
    
    Args:
        token: JWT token from OAuth2 password bearer
        db: MongoDB database dependency
        
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
    
    try:
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
    except JWTError as e:
        logger.warning(f"JWT error: {e}")
        raise credentials_exception
    
    try:
        # Get user from database
        user = await db["users"].find_one({"_id": ObjectId(user_id)})
        if user is None:
            logger.warning(f"User with ID {user_id} not found")
            raise credentials_exception
        
        return user
    except Exception as e:
        logger.error(f"Error retrieving user: {e}")
        raise credentials_exception

async def get_current_admin(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Dependency to ensure the current user is an admin.
    
    Args:
        current_user: The authenticated user
        
    Returns:
        Dict: The user document if they are an admin
        
    Raises:
        HTTPException: If the user is not an admin
    """
    if current_user["role"] != "admin":
        logger.warning(f"User {current_user['username']} attempted admin action without admin role")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    
    return current_user

async def get_current_editor(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Dependency to ensure the current user is an editor or admin.
    
    Args:
        current_user: The authenticated user
        
    Returns:
        Dict: The user document if they are an editor or admin
        
    Raises:
        HTTPException: If the user is not an editor or admin
    """
    if current_user["role"] not in ["admin", "editor"]:
        logger.warning(f"User {current_user['username']} attempted editor action without editor/admin role")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Editor privileges required"
        )
    
    return current_user
