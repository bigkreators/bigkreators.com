"""
Routes package for the Kryptopedia application.
"""
# Import route modules to make them available for including in the main app
try:
    from . import auth, articles, media, proposals, rewards, special, templates
except ImportError as e:
    print(f"Warning: Could not import all routes: {e}")

__all__ = [
    'auth', 
    'articles', 
    'media', 
    'proposals', 
    'rewards', 
    'special', 
    'templates'
]
