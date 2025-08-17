# File: dependencies/__init__.py
"""
Dependencies package for FastAPI dependency injection.
"""
from .database import get_db
from .auth import get_current_user, get_current_admin, get_current_editor, oauth2_scheme, get_user_or_anonymous
from .storage import get_storage
from .cache import get_cache
from .search import get_search

__all__ = [
    'get_db',
    'get_current_user',
    'get_current_admin',
    'get_current_editor',
    'oauth2_scheme',
    'get_user_or_anonymous',
    'get_storage',
    'get_cache',
    'get_search'
]
