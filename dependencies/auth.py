# File: dependencies/auth.py (Updated with Anonymous User Support)
"""
Authentication dependencies for FastAPI with anonymous user support.
"""
from fastapi import Depends, HTTPException, status, Request, Cookie
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from typing import Dict, Any, Optional, Union
from bson import ObjectId
import logging
import ipaddress

import config
from dependencies.database import get_db

logger = logging.getLogger(__name__)

# Initialize OAuth2 password bearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{config.API_PREFIX}/auth/login", auto_error=False)

def get_client_ip(request: Request) -> str:
    """
    Get the client's IP address from the request.
    Handles proxies and load balancers.
    """
    # Check for X-Forwarded-For header (from proxies)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Take the first IP in the chain
        ip = forwarded_for.split(",")[0].strip()
    else:
        # Fall back to direct connection IP
        ip = request.client.host if request.client else "unknown"
    
    return ip

def anonymize_ip(ip: str) -> str:
    """
    Anonymize an IP address for privacy.
    For IPv4: Keep first 3 octets (e.g., 192.168.1.x)
    For IPv6: Keep first 64 bits
    """
    try:
        ip_obj = ipaddress.ip_address(ip)
        if ip_obj.version == 4:
            # IPv4: Replace last octet with 'x'
            parts = ip.split('.')
            if len(parts) == 4:
                return f"{parts[0]}.{parts[1]}.{parts[2]}.x"
        elif ip_obj.version == 6:
            # IPv6: Keep first 64 bits, replace rest with 'x'
            parts = ip.split(':')
            if len(parts) >= 4:
                return ':'.join(parts[:4]) + ":x:x:x:x"
    except ValueError:
        # Invalid IP format
        pass
    
    return "x.x.x.x"  # Fallback for invalid IPs

async def validate_token_manually(token: str, db) -> Optional[Dict[str, Any]]:
    """
    Manually validate a token and return the user if valid.
    This is a helper function for direct token validation.
    
    Args:
        token: JWT token string
        db: Database connection
        
    Returns:
        Dict: The user document if token is valid, None otherwise
    """
    if not token:
        return None
        
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
            return None
            
    except JWTError as e:
        logger.warning(f"JWT error: {e}")
        return None
    
    try:
        # Get user from database
        user = await db["users"].find_one({"_id": ObjectId(user_id)})
        if user is None:
            logger.warning(f"User with ID {user_id} not found")
            return None
        
        return user
    except Exception as e:
        logger.error(f"Error retrieving user: {e}")
        return None

async def get_user_or_anonymous(request: Request, db) -> Dict[str, Any]:
    """
    Get user identifier - either authenticated user or anonymous IP.
    This is the main function for handling both authenticated and anonymous users.
    
    Args:
        request: The FastAPI request object
        db: Database connection
        
    Returns:
        Dict containing:
        - type: "authenticated" | "anonymous"
        - user: user_object | None
        - identifier: user_id | ip_address
        - display_name: username | "IP: x.x.x.x"
        - ip: actual IP address
        - anonymized_ip: privacy-safe IP
    """
    # Get client IP
    client_ip = get_client_ip(request)
    anonymized_ip = anonymize_ip(client_ip)
    
    # Try to get authenticated user first
    # Check Authorization header
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.replace("Bearer ", "")
        user = await validate_token_manually(token, db)
        if user:
            return {
                "type": "authenticated",
                "user": user,
                "identifier": str(user["_id"]),
                "display_name": user["username"],
                "ip": client_ip,
                "anonymized_ip": anonymized_ip,
                "can_create": True,
                "can_upload": True,
                "can_move": True,
                "can_reward": True
            }
    
    # Try cookie token
    token = request.cookies.get("token")
    if token:
        user = await validate_token_manually(token, db)
        if user:
            return {
                "type": "authenticated",
                "user": user,
                "identifier": str(user["_id"]),
                "display_name": user["username"],
                "ip": client_ip,
                "anonymized_ip": anonymized_ip,
                "can_create": True,
                "can_upload": True,
                "can_move": True,
                "can_reward": True
            }
    
    # Fall back to anonymous user
    return {
        "type": "anonymous",
        "user": None,
        "identifier": anonymized_ip,
        "display_name": f"IP: {anonymized_ip}",
        "ip": client_ip,
        "anonymized_ip": anonymized_ip,
        "can_create": False,
        "can_upload": False,
        "can_move": False,
        "can_reward": False
    }

async def check_ip_rate_limit(ip: str, db, action: str = "edit", window_minutes: int = 60, max_actions: int = 10) -> bool:
    """
    Check if an IP address has exceeded rate limits for a specific action.
    
    Args:
        ip: IP address to check
        db: Database connection
        action: Type of action (edit, create, upload)
        window_minutes: Time window in minutes
        max_actions: Maximum actions allowed in the window
        
    Returns:
        bool: True if rate limit exceeded, False otherwise
    """
    from datetime import datetime, timedelta
    
    # Calculate time window
    window_start = datetime.now() - timedelta(minutes=window_minutes)
    
    # Count recent actions from this IP
    recent_actions = await db["ip_actions"].count_documents({
        "ip": anonymize_ip(ip),
        "action": action,
        "timestamp": {"$gte": window_start}
    })
    
    return recent_actions >= max_actions

async def log_ip_action(ip: str, action: str, db, details: Dict[str, Any] = None):
    """
    Log an action performed by an IP address for rate limiting and abuse prevention.
    
    Args:
        ip: IP address
        action: Type of action performed
        db: Database connection
        details: Optional additional details about the action
    """
    from datetime import datetime
    
    action_log = {
        "ip": anonymize_ip(ip),
        "action": action,
        "timestamp": datetime.now(),
        "details": details or {}
    }
    
    await db["ip_actions"].insert_one(action_log)

# Keep existing functions for backward compatibility
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
    Note: This still requires authentication - use get_user_or_anonymous for optional auth.
    
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
    
    # Use the manual validation function
    user = await validate_token_manually(actual_token, db)
    if user is None:
        raise credentials_exception
        
    return user

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

async def get_user_or_anonymous(
    request: Request,
    db = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get the current user if authenticated, otherwise return anonymous user info.
    This allows routes to work for both authenticated and anonymous users.
    """
    try:
        # Try to get token from cookie first
        token = request.cookies.get("token")
        
        # Try Authorization header if no cookie
        if not token:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.replace("Bearer ", "")
        
        # If we have a token, try to validate it
        if token:
            payload = jwt.decode(
                token,
                config.JWT_SECRET,
                algorithms=[config.JWT_ALGORITHM]
            )
            
            user_id = payload.get("sub")
            if user_id:
                user = await db["users"].find_one({"_id": ObjectId(user_id)})
                if user:
                    return user
    except:
        # Any error means we treat as anonymous
        pass
    
    # Return anonymous user
    return {
        "_id": None,
        "username": "Anonymous",
        "email": None,
        "role": "anonymous",
        "is_anonymous": True
    }
