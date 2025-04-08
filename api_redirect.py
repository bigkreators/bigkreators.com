"""
API redirection helpers to handle API endpoints that should redirect to frontend pages
"""
from fastapi import HTTPException, Depends
from fastapi.responses import RedirectResponse
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

async def redirect_to_random_article(db: AsyncIOMotorClient):
    """Get a random article and redirect to it"""
    # Use MongoDB aggregation to get a random article
    pipeline = [
        {"$match": {"status": "published"}},
        {"$sample": {"size": 1}}
    ]
    
    # Execute pipeline
    results = await db["articles"].aggregate(pipeline).to_list(length=1)
    
    if not results:
        raise HTTPException(status_code=404, detail="No articles found")
    
    # Get the random article
    article = results[0]
    
    # Redirect to the article page
    return RedirectResponse(url=f"/articles/{article['slug']}")
