"""
Pages package for the Kryptopedia application.
This package contains all the page routes for the application.
"""
from fastapi import APIRouter

# Import routers from all page modules
from .home import router as home_router
from .articles import router as articles_router
from .articles_html import router as articles_html_router
from .admin import router as admin_router
from .special import router as special_router
from .proposals import router as proposals_router
from .search import router as search_router
from .user_profile import router as user_profile_router
from .errors import router as errors_router, add_error_handlers
from .help import router as help_router  # Add this
from .community import router as community_router  # Add this
from .donate import router as donate_router  # Add this
from .upload import router as upload_router 
from .crypto_admin import router as crypto_admin_router

# Create a combined router for all pages
router = APIRouter()

# Include all page routers
router.include_router(home_router)
router.include_router(articles_router)
router.include_router(admin_router)
router.include_router(special_router)
router.include_router(proposals_router)
router.include_router(search_router)
router.include_router(user_profile_router)
router.include_router(errors_router)
router.include_router(help_router)
router.include_router(community_router)
router.include_router(donate_router)
router.include_router(upload_router)
router.include_router(articles_html_router)
router.include_router(crypto_admin_router)

# Export modules
__all__ = [
    'router',
    'add_error_handlers',
    'home_router',
    'articles_router',
    'admin_router',
    'special_router',
    'proposals_router',
    'search_router',
    'user_profile_router',
    'errors_router'
    'help_router'
    'community_router'
    'donate_router'
    'upload_router'
    'article_html_router'
    'crypto_admin_router'
]
