"""
Dependencies package for FastAPI dependency injection.
"""
from .database import get_db
from .auth import get_current_user, get_current_admin, oauth2_scheme
from .storage import get_storage
from .cache import get_cache
from .search import get_search
from fastapi import Depends, HTTPException, status

__all__ = [
    'get_db',
    'get_current_user',
    'get_current_admin',
    'oauth2_scheme',
    'get_storage',
    'get_cache',
    'get_search'
]

async def get_current_editor(current_user: dict = Depends(get_current_user)):
    """
    Dependency to check if the current user has editor privileges.
    Raises 403 if the user is not an editor or admin.
    """
    if current_user["role"] not in ["editor", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Editor privileges required"
        )
    return current_user
