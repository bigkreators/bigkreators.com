# File: models/__init__.py
"""
Models package for the Kryptopedia application.
"""
# First import base models to avoid circular imports
from .base import PyObjectId, DBModel

# Then import specific models
from .user import (
    UserBase, UserCreate, UserLogin, UserUpdate, User, 
    UserContributions, Token, TokenData
)
from .article import (
    ArticleBase, ArticleCreate, ArticleUpdate, Article, 
    ArticleWithCreator, ArticleMetadata
)
from .revision import (
    RevisionCreate, Revision, RevisionWithMetadata
)
from .proposal import (
    ProposalCreate, Proposal, ProposalWithMetadata
)
from .media import (
    MediaCreate, Media, MediaWithUploader, MediaMetadata
)
from .reward import (
    RewardCreate, Reward, RewardWithMetadata
)

# Export all models
__all__ = [
    'PyObjectId', 'DBModel',
    'UserBase', 'UserCreate', 'UserLogin', 'UserUpdate', 'User', 
    'UserContributions', 'Token', 'TokenData',
    'ArticleBase', 'ArticleCreate', 'ArticleUpdate', 'Article', 
    'ArticleWithCreator', 'ArticleMetadata',
    'RevisionCreate', 'Revision', 'RevisionWithMetadata',
    'ProposalCreate', 'Proposal', 'ProposalWithMetadata',
    'MediaCreate', 'Media', 'MediaWithUploader', 'MediaMetadata',
    'RewardCreate', 'Reward', 'RewardWithMetadata'
]
