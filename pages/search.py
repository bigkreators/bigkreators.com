"""
Search-related page routes for the Kryptopedia application.
"""
from fastapi import APIRouter, Request, Depends, Query
from fastapi.responses import HTMLResponse
from typing import Optional
import logging

from dependencies import get_db

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/search", response_class=HTMLResponse)
async def search_page(
    request: Request,
    q: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db=Depends(get_db)
):
    """
    Render the search results page.
    """
    templates = request.app.state.templates
    results = []
    total = 0
    
    if q:
        # Perform simple text search
        try:
            # MongoDB text search
            cursor = db["articles"].find(
                {"$text": {"$search": q}, "status": "published"},
                {"score": {"$meta": "textScore"}}
            ).sort([("score", {"$meta": "textScore"})]).skip(skip).limit(limit)
            
            # Get search results
            results = await cursor.to_list(length=limit)
            
            # Count total results
            total = await db["articles"].count_documents(
                {"$text": {"$search": q}, "status": "published"}
            )
            
        except Exception as e:
            logger.error(f"Search error: {str(e)}")
    
    # Render template
    return templates.TemplateResponse(
        "search_results.html",
        {
            "request": request, 
            "query": q or "", 
            "results": results,
            "total": total,
            "skip": skip,
            "limit": limit
        }
    )

@router.get("/search/advanced", response_class=HTMLResponse)
async def advanced_search_page(
    request: Request,
    q: Optional[str] = None,
    category: Optional[str] = None,
    tag: Optional[str] = None,
    author: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    sort: Optional[str] = Query(None, description="Sorting order: 'relevance', 'date', 'views'"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db=Depends(get_db)
):
    """
    Render the advanced search page with more filter options.
    """
    templates = request.app.state.templates
    results = []
    total = 0
    
    # Get categories for filter dropdown
    categories_pipeline = [
        {"$match": {"status": "published"}},
        {"$unwind": "$categories"},
        {"$group": {"_id": "$categories", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 20}
    ]
    categories = await db["articles"].aggregate(categories_pipeline).to_list(length=20)
    
    # Get tags for filter dropdown
    tags_pipeline = [
        {"$match": {"status": "published"}},
        {"$unwind": "$tags"},
        {"$group": {"_id": "$tags", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 20}
    ]
    tags = await db["articles"].aggregate(tags_pipeline).to_list(length=20)
    
    # Build the advanced search query
    if q or category or tag or author or date_from or date_to:
        try:
            query = {"status": "published"}
            
            # Full-text search
            if q:
                query["$text"] = {"$search": q}
            
            # Category filter
            if category:
                query["categories"] = category
            
            # Tag filter
            if tag:
                query["tags"] = tag
            
            # Author filter (by username)
            if author:
                # Find user first
                user = await db["users"].find_one({"username": {"$regex": f"^{author}$", "$options": "i"}})
                if user:
                    query["createdBy"] = user["_id"]
            
            # Date range filter
            date_filter = {}
            if date_from:
                # Convert string to datetime
                from datetime import datetime
                try:
                    date_from_dt = datetime.strptime(date_from, "%Y-%m-%d")
                    date_filter["$gte"] = date_from_dt
                except ValueError:
                    pass
                
            if date_to:
                try:
                    date_to_dt = datetime.strptime(date_to, "%Y-%m-%d")
                    date_filter["$lte"] = date_to_dt
                except ValueError:
                    pass
                
            if date_filter:
                query["createdAt"] = date_filter
            
            # Determine sort order
            sort_options = {}
            if q and (not sort or sort == 'relevance'):
                sort_options = [("score", {"$meta": "textScore"})]
                projection = {"score": {"$meta": "textScore"}}
            elif sort == 'date':
                sort_options = [("createdAt", -1)]
                projection = {}
            elif sort == 'views':
                sort_options = [("views", -1)]
                projection = {}
            else:
                # Default to date
                sort_options = [("createdAt", -1)]
                projection = {}
            
            # Execute query
            if q and (not sort or sort == 'relevance'):
                cursor = db["articles"].find(query, projection).sort(sort_options).skip(skip).limit(limit)
            else:
                cursor = db["articles"].find(query).sort(sort_options).skip(skip).limit(limit)
                
            results = await cursor.to_list(length=limit)
            
            # Count total results
            total = await db["articles"].count_documents(query)
            
        except Exception as e:
            logger.error(f"Advanced search error: {str(e)}")
    
    # Render template
    return templates.TemplateResponse(
        "advanced_search.html",
        {
            "request": request,
            "query": q or "",
            "category": category or "",
            "tag": tag or "",
            "author": author or "",
            "date_from": date_from or "",
            "date_to": date_to or "",
            "sort": sort or "relevance",
            "results": results,
            "total": total,
            "skip": skip,
            "limit": limit,
            "categories": categories,
            "tags": tags
        }
    )
