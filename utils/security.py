"""
Security utilities for the Cryptopedia application.
"""
import bcrypt
import jwt
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional
import config

def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: The plain text password
        
    Returns:
        str: The hashed password
    """
    # Generate a salt and hash the password
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    return hashed.decode('utf-8')  # Return as string

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash.
    
    Args:
        plain_password: The plain text password
        hashed_password: The hashed password
        
    Returns:
        bool: True if the password matches the hash
    """
    return bcrypt.checkpw(
        plain_password.encode('utf-8'), 
        hashed_password.encode('utf-8')
    )

def create_access_token(data: Dict, expires_delta: Optional[timedelta] = None) -> Tuple[str, datetime]:
    """
    Create a JWT access token.
    
    Args:
        data: The data to encode in the token
        expires_delta: Optional custom expiration time
        
    Returns:
        Tuple[str, datetime]: The encoded token and expiration datetime
    """
    to_encode = data.copy()
    
    # Set expiration time
    if expires_delta:
        expires = datetime.utcnow() + expires_delta
    else:
        expires = datetime.utcnow() + timedelta(hours=config.JWT_EXPIRATION_HOURS)
    
    # Add expiration to payload
    to_encode.update({"exp": expires})
    
    # Encode the JWT
    encoded_jwt = jwt.encode(
        to_encode, 
        config.JWT_SECRET, 
        algorithm=config.JWT_ALGORITHM
    )
    
    return encoded_jwt, expires
