# File: models/__init__.py
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

# Vote model
class Vote(BaseModel):
    articleId: str
    userId: str
    voteType: str  # "upvote" or "downvote"
