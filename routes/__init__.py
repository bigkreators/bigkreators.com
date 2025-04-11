"""
Routes package for the Cryptopedia application.
"""
# Import route modules to make them available for including in the main app
from . import auth, templates

# Add placeholder imports for other routes that will be implemented later
# These will be implemented in separate files
from . import articles, media, proposals, rewards, special

__all__ = [
    'auth', 
    'articles', 
    'media', 
    'proposals', 
    'rewards', 
    'special', 
    'templates'
]
