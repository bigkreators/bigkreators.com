# File: utils/namespace.py
"""
Namespace utilities for Kryptopedia.
"""
from typing import Dict, List, Optional, Tuple

# Define the namespace configuration
NAMESPACE_CONFIG = {
    "": {
        "name": "Main",
        "description": "Main content namespace for articles",
        "url_prefix": "/articles",
        "searchable": True,
        "allow_categories": True,
        "content_model": "wikitext"
    },
    "Category": {
        "name": "Category", 
        "description": "Category organization pages",
        "url_prefix": "/categories",
        "searchable": True,
        "allow_categories": False,
        "content_model": "category"
    },
    "Template": {
        "name": "Template",
        "description": "Reusable template content",
        "url_prefix": "/templates", 
        "searchable": False,
        "allow_categories": True,
        "content_model": "wikitext"
    },
    "Help": {
        "name": "Help",
        "description": "Help and documentation pages",
        "url_prefix": "/help",
        "searchable": True,
        "allow_categories": True,
        "content_model": "wikitext"
    },
    "User": {
        "name": "User",
        "description": "User pages and subpages",
        "url_prefix": "/users",
        "searchable": False,
        "allow_categories": False,
        "content_model": "wikitext"
    },
    "File": {
        "name": "File", 
        "description": "File description pages",
        "url_prefix": "/media",
        "searchable": True,
        "allow_categories": True,
        "content_model": "file"
    },
    "Kryptopedia": {
        "name": "Kryptopedia",
        "description": "Project-related pages",
        "url_prefix": "/project",
        "searchable": True,
        "allow_categories": True,
        "content_model": "wikitext"
    },
    "Talk": {
        "name": "Talk",
        "description": "Discussion pages",
        "url_prefix": "/talk",
        "searchable": False,
        "allow_categories": False,
        "content_model": "wikitext"
    }
}

def get_valid_namespaces() -> Dict[str, str]:
    """Get a mapping of namespace keys to display names."""
    return {ns: config["name"] for ns, config in NAMESPACE_CONFIG.items()}

def is_valid_namespace(namespace: str) -> bool:
    """Check if a namespace is valid."""
    return namespace in NAMESPACE_CONFIG

def get_namespace_info(namespace: str) -> Optional[Dict]:
    """Get configuration information for a namespace."""
    return NAMESPACE_CONFIG.get(namespace)

def parse_title_with_namespace(full_title: str) -> Tuple[str, str]:
    """
    Parse a title to extract namespace and title.
    
    Args:
        full_title: The full title (e.g., "Category:Blockchain" or "Introduction to Crypto")
        
    Returns:
        Tuple[str, str]: (namespace, title) - namespace is empty string for main namespace
    """
    if ":" in full_title:
        potential_namespace, title = full_title.split(":", 1)
        if is_valid_namespace(potential_namespace):
            return potential_namespace, title.strip()
    
    # No valid namespace found, treat as main namespace
    return "", full_title.strip()

def get_namespace_url(namespace: str, title: str) -> str:
    """
    Generate the appropriate URL for a page in a namespace.
    All articles stay under /articles/ path regardless of namespace.
    
    Args:
        namespace: The namespace
        title: The page title
        
    Returns:
        str: The URL path
        
    Examples:
        get_namespace_url("Kryptopedia", "Rules (being merged)")
        → "/articles/Kryptopedia:Rules_(being_merged)"
        
        get_namespace_url("", "Bitcoin Basics") 
        → "/articles/Bitcoin_Basics"
    """
    from .slug import generate_namespace_slug
    
    # Generate the proper slug that includes namespace
    slug = generate_namespace_slug(namespace, title)
    
    # All articles use the same /articles/ path
    return f"/articles/{slug}"

def format_full_title(namespace: str, title: str) -> str:
    """
    Format a full title including namespace prefix.
    
    Args:
        namespace: The namespace (empty string for main)
        title: The page title
        
    Returns:
        str: The full formatted title
    """
    if namespace:
        return f"{namespace}:{title}"
    return title

def get_searchable_namespaces() -> List[str]:
    """Get list of namespaces that should be included in search."""
    return [ns for ns, config in NAMESPACE_CONFIG.items() if config["searchable"]]

def namespace_allows_categories(namespace: str) -> bool:
    """Check if a namespace allows category assignment."""
    config = get_namespace_info(namespace)
    return config["allow_categories"] if config else False

def get_namespace_content_model(namespace: str) -> str:
    """Get the content model for a namespace."""
    config = get_namespace_info(namespace)
    return config["content_model"] if config else "wikitext"

def suggest_namespace_for_title(title: str) -> str:
    """
    Suggest appropriate namespace based on title patterns.
    
    Args:
        title: The page title
        
    Returns:
        str: Suggested namespace (empty string for main)
    """
    title_lower = title.lower()
    
    # Category pattern
    if title_lower.startswith("category"):
        return "Category"
    
    # Template pattern  
    if title_lower.startswith("template"):
        return "Template"
        
    # Help pattern
    if any(word in title_lower for word in ["help", "guide", "tutorial", "how to"]):
        return "Help"
        
    # User pattern
    if title_lower.startswith("user"):
        return "User"
        
    # File pattern
    if any(ext in title_lower for ext in [".jpg", ".png", ".gif", ".svg", ".pdf", ".doc"]):
        return "File"
        
    # Project pattern
    if any(word in title_lower for word in ["kryptopedia", "policy", "guideline", "project"]):
        return "Kryptopedia"
        
    # Default to main namespace
    return ""

def get_namespace_statistics() -> Dict[str, Dict[str, int]]:
    """
    Get statistics about namespace usage.
    This would typically query the database, but returns empty for now.
    
    Returns:
        Dict[str, Dict[str, int]]: Statistics per namespace
    """
    stats = {}
    for namespace in NAMESPACE_CONFIG.keys():
        stats[namespace] = {
            "total_pages": 0,
            "total_views": 0,
            "recent_changes": 0
        }
    return stats
