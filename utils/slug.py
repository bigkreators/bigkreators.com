# File: utils/slug.py
"""
Slug generation utilities for the Kryptopedia application with namespace support.
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

def generate_namespace_slug(namespace: str, title: str, timestamp: Optional[int] = None) -> str:
    """
    Generate a namespace-aware slug for articles.
    
    Args:
        namespace: The namespace (empty string for main namespace)
        title: The title within the namespace
        timestamp: Optional timestamp to append
        
    Returns:
        str: The generated namespace-aware slug
    """
    if namespace:
        # For namespaced articles, include namespace prefix
        combined_title = f"{namespace}_{title}"
        return generate_slug(combined_title, timestamp)
    else:
        # Main namespace articles
        return generate_slug(title, timestamp)

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

def parse_slug_namespace(slug: str) -> tuple[str, str]:
    """
    Parse namespace from a slug if present.
    
    Args:
        slug: The slug to parse
        
    Returns:
        tuple[str, str]: (namespace, remaining_slug) where namespace is empty for main namespace
    """
    # Known namespace prefixes in slugs
    namespace_prefixes = ['category_', 'template_', 'help_', 'user_', 'file_', 'kryptopedia_']
    
    slug_lower = slug.lower()
    for prefix in namespace_prefixes:
        if slug_lower.startswith(prefix):
            namespace = prefix.rstrip('_').capitalize()
            remaining_slug = slug[len(prefix):]
            return namespace, remaining_slug
    
    # No namespace found
    return "", slug
