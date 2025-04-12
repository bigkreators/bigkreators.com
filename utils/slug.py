# File: utils/slug.py
"""
Slug generation utilities for the Kryptopedia application.
"""
import re
import unicodedata
from datetime import datetime
from typing import Optional

def generate_slug(title: str, timestamp: Optional[int] = None) -> str:
    """
    Generate a URL-friendly slug from a title.
    
    Args:
        title: The title to slugify
        timestamp: Optional timestamp to append (defaults to current time)
        
    Returns:
        str: The generated slug
    """
    # Normalize unicode characters
    slug = unicodedata.normalize('NFKD', title)
    
    # Convert to ASCII, ignoring non-ASCII characters
    slug = slug.encode('ascii', 'ignore').decode('ascii')
    
    # Convert to lowercase
    slug = slug.lower()
    
    # Replace non-alphanumeric characters with hyphens
    slug = re.sub(r'[^a-z0-9]+', '-', slug)
    
    # Remove leading/trailing hyphens
    slug = slug.strip('-')
    
    # Add timestamp to ensure uniqueness
    if timestamp is None:
        timestamp = int(datetime.now().timestamp())
    
    # Append timestamp
    slug = f"{slug}-{timestamp}"
    
    return slug

def is_valid_slug(slug: str) -> bool:
    """
    Check if a string is a valid slug format.
    
    Args:
        slug: The string to check
        
    Returns:
        bool: True if the string is a valid slug
    """
    # Slugs should only contain lowercase letters, numbers, and hyphens
    # They should not start or end with a hyphen
    return bool(re.match(r'^[a-z0-9]+(-[a-z0-9]+)*(-\d+)?$', slug))
