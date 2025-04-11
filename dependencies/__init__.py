"""
Dependencies package for FastAPI dependency injection.
"""
from .database import get_db
from .auth import get_current_user, get_current_admin, oauth2_scheme
from .storage import get_storage
from .cache import get_cache
from .search import get_search

__all__ = [
    'get_db',
    'get_current_user',
    'get_current_admin',
    'oauth2_scheme',
    'get_storage',
    'get_cache',
    'get_search'
]
