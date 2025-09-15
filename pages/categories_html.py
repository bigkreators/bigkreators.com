# File: pages/categories_html.py
"""
Category-related HTML page routes.
"""
from fastapi import APIRouter, Request, Depends, Path, Query, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from bson import ObjectId
from typing import Optional
import logging

from dependencies import get_db, get_current_user, get_cache

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/categories", response_class=HTMLResponse)
async def categories_list_page(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    parent: Optional[str] = Query(None, description="Filter by parent category"),
    search: Optional[str] = Query(None, description="Search categories"),
    sort: Optional[str] = Query("name"),
    db=Depends(get_db),
    cache=Depends(get_cache)
):
    """
    Render the categories list page.
    """
    templates = request.app.state.templates
    
    try:
        # Try to get from cache if no filters are applied
        cache_key = None
        if not parent and not search:
            cache_key = f"categories_list_{sort}_{skip}_{limit}"
            cached_data = await cache.get(cache_key)
            
            if cached_data:
                return templates.TemplateResponse(
                    "categories.html",
                    {
                        "request": request,
                        **cached_data
                    }
                )
        
        # Build query
        query = {"status": "active"}
        
        if parent is not None:
            if parent == "":
                # Root categories (no parent)
                query["parent_category"] = {"$in": [None, ""]}
            else:
                query["parent_category"] = parent
        
        if search:
            query["$or"] = [
                {"name": {"$regex": search, "$options": "i"}},
                {"description": {"$regex": search, "$options": "i"}}
            ]
        
        # Build sort
        sort_options = {
            "name": [("name", 1)],
            "created": [("createdAt", -1)],
            "articles": [("article_count", -1)],
            "updated": [("lastUpdatedAt", -1)]
        }
        sort_query = sort_options.get(sort, [("name", 1)])
        
        # Get total count
        total = await db["categories"].count_documents(query)
        
        # Get categories
        cursor = db["categories"].find(query).sort(sort_query).skip(skip).limit(limit)
        categories = await cursor.to_list(length=limit)
        
        # Get category statistics for sidebar
        stats_pipeline = [
            {"$match": {"status": "active"}},
            {"$group": {
                "_id": None,
                "total_categories": {"$sum": 1},
                "total_articles": {"$sum": "$article_count"},
                "avg_articles_per_category": {"$avg": "$article_count"}
            }}
        ]
        stats_result = await db["categories"].aggregate(stats_pipeline).to_list(length=1)
        stats = stats_result[0] if stats_result else {}
        
        # Get most popular categories for sidebar
        popular_categories = await db["categories"].find({
            "status": "active",
            "article_count": {"$gt": 0}
        }).sort([("article_count", -1)]).limit(10).to_list(length=10)
        
        # Prepare template data
        template_data = {
            "categories": categories,
            "total": total,
            "skip": skip,
            "limit": limit,
            "parent": parent,
            "search": search,
            "sort": sort,
            "stats": stats,
            "popular_categories": popular_categories
        }
        
        # Cache the result if no filters
        if cache_key:
            await cache.set(cache_key, template_data, 600)  # Cache for 10 minutes
        
        return templates.TemplateResponse(
            "categories.html",
            {
                "request": request,
                **template_data
            }
        )
    except Exception as e:
        logger.error(f"Error getting categories list: {e}")
        return templates.TemplateResponse(
            "categories.html",
            {
                "request": request,
                "categories": [],
                "total": 0,
                "skip": skip,
                "limit": limit,
                "error": "Failed to load categories"
            }
        )

@router.get("/categories/{category_name}", response_class=HTMLResponse)
async def category_page(
    request: Request,
    category_name: str = Path(..., description="Category name or slug"),
    article_skip: int = Query(0, ge=0, description="Skip articles for pagination"),
    article_limit: int = Query(20, ge=1, le=100, description="Limit articles returned"),
    sort_articles: str = Query("title", description="Sort articles by: title, created, views, updated"),
    db=Depends(get_db)
):
    """
    Render a category page with description and auto-populated articles.
    """
    templates = request.app.state.templates
    
    try:
        # Convert URL-encoded category name back to normal
        category_name_decoded = category_name.replace('_', ' ')
        
        # Try to find category by name or slug
        category = await db["categories"].find_one({
            "$or": [
                {"name": {"$regex": f"^{category_name_decoded}$", "$options": "i"}},
                {"slug": category_name}
            ],
            "status": "active"
        })
        
        if not category:
            return templates.TemplateResponse(
                "404.html",
                {"request": request, "message": f"Category '{category_name_decoded}' not found"},
                status_code=404
            )
        
        # Get articles in this category
        article_sort_options = {
            "title": [("title", 1)],
            "created": [("createdAt", -1)],
            "views": [("views", -1)],
            "updated": [("lastUpdatedAt", -1)]
        }
        article_sort = article_sort_options.get(sort_articles, [("title", 1)])
        
        articles_cursor = db["articles"].find({
            "categories": category["name"],
            "status": "published"
        }).sort(article_sort).skip(article_skip).limit(article_limit)
        
        articles = await articles_cursor.to_list(length=article_limit)
        
        # Add canonical URLs to articles
        for article in articles:
            if article.get("namespace"):
                from utils.namespace import get_namespace_url
                article["canonical_url"] = get_namespace_url(article["namespace"], article["title"])
            else:
                article["canonical_url"] = f"/articles/{article['slug']}"
        
        # Get subcategories
        subcategories_cursor = db["categories"].find({
            "parent_category": category["name"],
            "status": "active"
        }).sort([("name", 1)])
        
        subcategories = await subcategories_cursor.to_list(length=None)
        
        # Get current user for editing permissions
        current_user = None
        try:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.replace("Bearer ", "")
                from dependencies.auth import get_current_user
                current_user = await get_current_user(token=token, db=db)
        except:
            pass
        
        # Add computed properties to category
        category["full_title"] = f"Category:{category['name']}"
        category["articles"] = articles
        category["subcategories"] = subcategories
        
        return templates.TemplateResponse(
            "category_page.html",
            {
                "request": request,
                "category": category,
                "current_user": current_user,
                "article_skip": article_skip,
                "article_limit": article_limit,
                "sort_articles": sort_articles
            }
        )
    except Exception as e:
        logger.error(f"Error loading category page for '{category_name}': {e}")
        return templates.TemplateResponse(
            "404.html",
            {"request": request, "message": "Error loading category page"},
            status_code=500
        )

@router.get("/create-category", response_class=HTMLResponse)
async def create_category_page(request: Request):
    """
    Render the category creation page.
    """
    templates = request.app.state.templates
    return templates.TemplateResponse(
        "create_category.html",
        {"request": request}
    )

@router.get("/categories/{category_slug}/edit", response_class=HTMLResponse)
async def edit_category_page(
    request: Request,
    category_slug: str = Path(..., description="Category slug"),
    db=Depends(get_db)
):
    """
    Render the category editing page.
    """
    templates = request.app.state.templates
    
    # Find category by slug
    category = await db["categories"].find_one({
        "slug": category_slug,
        "status": "active"
    })
    
    if not category:
        return templates.TemplateResponse(
            "404.html",
            {"request": request, "message": "Category not found"},
            status_code=404
        )
    
    return templates.TemplateResponse(
        "edit_category.html",
        {
            "request": request,
            "category": category
        }
    )

@router.get("/categories/{category_name}/feed")
async def category_rss_feed(
    category_name: str = Path(..., description="Category name"),
    db=Depends(get_db)
):
    """
    Generate RSS feed for a category.
    """
    from fastapi.responses import Response
    import xml.etree.ElementTree as ET
    from datetime import datetime
    
    # Convert URL-encoded category name back to normal
    category_name_decoded = category_name.replace('_', ' ')
    
    # Find category
    category = await db["categories"].find_one({
        "name": {"$regex": f"^{category_name_decoded}$", "$options": "i"},
        "status": "active"
    })
    
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Get recent articles in category
    articles = await db["articles"].find({
        "categories": category["name"],
        "status": "published"
    }).sort([("createdAt", -1)]).limit(20).to_list(length=20)
    
    # Generate RSS XML
    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")
    
    ET.SubElement(channel, "title").text = f"Category:{category['name']} - Kryptopedia"
    ET.SubElement(channel, "link").text = f"https://kryptopedia.com/categories/{category_name}"
    ET.SubElement(channel, "description").text = category.get("description", "").replace("<", "&lt;").replace(">", "&gt;")
    ET.SubElement(channel, "lastBuildDate").text = datetime.now().strftime("%a, %d %b %Y %H:%M:%S GMT")
    
    for article in articles:
        item = ET.SubElement(channel, "item")
        
        title = article["title"]
        if article.get("namespace"):
            title = f"{article['namespace']}:{title}"
        
        ET.SubElement(item, "title").text = title
        ET.SubElement(item, "link").text = f"https://kryptopedia.com/articles/{article['slug']}"
        ET.SubElement(item, "description").text = article.get("summary", "")
        ET.SubElement(item, "pubDate").text = article["createdAt"].strftime("%a, %d %b %Y %H:%M:%S GMT")
        ET.SubElement(item, "guid").text = f"https://kryptopedia.com/articles/{article['slug']}"
    
    xml_string = ET.tostring(rss, encoding="unicode")
    
    return Response(
        content=xml_string,
        media_type="application/rss+xml",
        headers={"Content-Type": "application/rss+xml; charset=utf-8"}
    )
