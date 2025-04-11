"""
Authentication dependencies for FastAPI.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from typing import Dict, Optional
from bson import ObjectId
import config
from dependencies.database import get_db
from models import TokenData

# Initialize OAuth2 password bearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{config.API_PREFIX}/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme), db=Depends(get_db)):
    """
    Dependency to get the current authenticated user.
    Used in route functions that require authentication.
    
    Args:
        token: JWT token from Authentication header
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
    try:
        # Decode JWT token
        payload = jwt.decode(
            token, 
            config.JWT_SECRET, 
            algorithms=[config.JWT_ALGORITHM]
        )
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        token_data = TokenData(user_id=user_id)
    except JWTError:
        raise credentials_exception
    
    # Get user from database
    user = await db["users"].find_one({"_id": ObjectId(token_data.user_id)})
    if user is None:
        raise credentials_exception
    
    return user

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
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions. Editor or admin role required."
        )
    return current_user
