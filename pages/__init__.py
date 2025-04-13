"""
HTML page routes package for the Kryptopedia application.
"""
from fastapi import APIRouter

# Create a parent router that will include all page routers
router = APIRouter()

# Import and include all page route modules
from .home import router as home_router
from .articles import router as articles_router
from .profiles import router as profiles_router
from .admin import router as admin_router
from .special import router as special_router
from .search import router as search_router

# Include all page routers
router.include_router(home_router)
router.include_router(articles_router)
router.include_router(profiles_router)
router.include_router(admin_router)
router.include_router(special_router)
router.include_router(search_router)

# Export the parent router
__all__ = ['router']
