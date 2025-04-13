# File: dependencies/auth.py
"""
Authentication dependencies for FastAPI.
"""
from fastapi import Depends, HTTPException, status, Request, Cookie
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from typing import Dict, Any, Optional, Union
from bson import ObjectId
import logging

import config
from dependencies.database import get_db

logger = logging.getLogger(__name__)

# Initialize OAuth2 password bearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{config.API_PREFIX}/auth/login")

async def get_token_from_request(request: Request, token: Optional[str] = Depends(oauth2_scheme)) -> str:
    """
    Try to get the token from various sources (OAuth2, headers, cookies)
    
    Args:
        request: The request object
        token: The token from OAuth2PasswordBearer dependency
        
    Returns:
        str: The token if found
        
    Raises:
        HTTPException: If no token is found
    """
    # First try the OAuth2 token
    if token:
        return token
    
    # Then try the Authorization header
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header.replace("Bearer ", "")
    
    # Finally try the cookie
    token_cookie = request.cookies.get("token")
    if token_cookie:
        return token_cookie
    
    # No token found
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )

async def get_current_user(
    request: Request = None, 
    token: Optional[str] = Depends(oauth2_scheme),
    db=Depends(get_db)
) -> Dict[str, Any]:
    """
    Dependency to get the current authenticated user.
    
    Args:
        request: The request object (optional)
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
    
    # If request is provided, try to get token from various sources
    actual_token = token
    if request is not None:
        try:
            actual_token = await get_token_from_request(request, token)
        except HTTPException:
            # If no token is found, just use the provided token
            actual_token = token
    
    # If still no token, raise exception
    if not actual_token:
        logger.warning("No token provided")
        raise credentials_exception
    
    try:
        # Decode JWT token
        payload = jwt.decode(
            actual_token,
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

async def get_current_admin(
    request: Request = None,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Dependency to ensure the current user is an admin.
    
    Args:
        request: The request object (optional)
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

async def get_current_editor(
    request: Request = None,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Dependency to ensure the current user is an editor or admin.
    
    Args:
        request: The request object (optional)
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
