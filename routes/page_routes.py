# File: routes/page_routes.py
"""
Page routes for the Kryptopedia application.
"""
from fastapi import APIRouter, Depends, HTTPException, Request, Path, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from bson import ObjectId
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import random
import logging

import config
from dependencies import get_db, get_cache, get_current_user, get_search, get_current_admin

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/", response_class=HTMLResponse)
async def homepage(request: Request, db=Depends(get_db), cache=Depends(get_cache)):
    """
    Render the homepage template.
    """
    # Get the templates instance from the app state
    templates = request.app.state.templates
    
    # Try to get featured article from cache
    featured_article = await cache.get("featured_article")
    
    # If not in cache, fetch from database
    if not featured_article:
        # Find featured articles (featuredUntil > now)
        featured_article = await db["articles"].find_one({
            "featuredUntil": {"$gt": datetime.now()},
            "status": "published"
        })
        
        # If no featured article, get most viewed article
        if not featured_article:
            featured_article = await db["articles"].find_one(
                {"status": "published"},
                sort=[("views", -1)]
            )
        
        # Cache featured article for 1 hour
        if featured_article:
            await cache.set("featured_article", featured_article, 3600)
    
    # Get recent articles
    recent_articles = []
    cursor = db["articles"].find({"status": "published"}).sort("createdAt", -1).limit(3)
    recent_articles = await cursor.to_list(length=3)
    
    # Render template
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "featured_article": featured_article,
            "recent_articles": recent_articles
        }
    )

@router.get("/articles/{slug}", response_class=HTMLResponse)
async def article_page(
    request: Request, 
    slug: str = Path(..., description="Article slug or ID"),
    db=Depends(get_db)
):
    """
    Render an article page.
    """
    templates = request.app.state.templates
    
    # Try to find article by slug
    article = await db["articles"].find_one({"slug": slug, "status": "published"})
    
    # If not found by slug, try ObjectId (if valid)
    if not article and ObjectId.is_valid(slug):
        article = await db["articles"].find_one({
            "_id": ObjectId(slug),
            "status": "published"
        })
    
    # If article not found, return 404
    if not article:
        return templates.TemplateResponse(
            "404.html",
            {"request": request, "message": "Article not found"},
            status_code=404
        )
    
    # Increment view count
    await db["articles"].update_one(
        {"_id": article["_id"]},
        {"$inc": {"views": 1}}
    )
    
    # Render article template
    return templates.TemplateResponse(
        "article.html",
        {"request": request, "article": article}
    )

@router.get("/articles", response_class=HTMLResponse)
async def articles_list_page(
    request: Request,
    category: Optional[str] = None,
    tag: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db=Depends(get_db)
):
    """
    Render the articles list page.
    """
    templates = request.app.state.templates
    
    # Build query
    query = {"status": "published"}
    if category:
        query["categories"] = category
    if tag:
        query["tags"] = tag
    
    # Get total count
    total_count = await db["articles"].count_documents(query)
    
    # Get articles
    cursor = db["articles"].find(query).sort("createdAt", -1).skip(skip).limit(limit)
    articles = await cursor.to_list(length=limit)
    
    # Render template
    return templates.TemplateResponse(
        "articles_list.html",
        {
            "request": request,
            "articles": articles,
            "total": total_count,
            "skip": skip,
            "limit": limit,
            "category": category,
            "tag": tag
        }
    )

@router.get("/create-article", response_class=HTMLResponse)
async def create_article_page(request: Request):
    """
    Render the article creation page.
    """
    templates = request.app.state.templates
    return templates.TemplateResponse(
        "create_article.html",
        {"request": request}
    )

@router.get("/edit-article/{article_id}", response_class=HTMLResponse)
async def edit_article_page(
    request: Request,
    article_id: str = Path(..., description="Article ID"),
    db=Depends(get_db)
):
    """
    Render the article editing page.
    """
    templates = request.app.state.templates
    
    # Check if article exists
    if not ObjectId.is_valid(article_id):
        return templates.TemplateResponse(
            "404.html",
            {"request": request, "message": "Invalid article ID"},
            status_code=404
        )
    
    article = await db["articles"].find_one({"_id": ObjectId(article_id)})
    if not article:
        return templates.TemplateResponse(
            "404.html",
            {"request": request, "message": "Article not found"},
            status_code=404
        )
    
    # Render template
    return templates.TemplateResponse(
        "edit_article.html",
        {"request": request, "article": article}
    )

@router.get("/search", response_class=HTMLResponse)
async def search_page(
    request: Request,
    q: Optional[str] = None,
    db=Depends(get_db)
):
    """
    Render the search results page.
    """
    templates = request.app.state.templates
    results = []
    
    if q:
        # Perform simple text search
        try:
            cursor = db["articles"].find(
                {"$text": {"$search": q}, "status": "published"},
                {"score": {"$meta": "textScore"}}
            ).sort([("score", {"$meta": "textScore"})]).limit(20)
            
            results = await cursor.to_list(length=20)
        except Exception as e:
            print(f"Search error: {str(e)}")
    
    # Render template
    return templates.TemplateResponse(
        "search_results.html",
        {"request": request, "query": q or "", "results": results}
    )

@router.get("/quick-edit", response_class=HTMLResponse)
async def quick_edit_page(
    request: Request,
    db=Depends(get_db)
):
    """
    Render the quick edit page for easily creating revisions.
    """
    templates = request.app.state.templates
    
    # Get all published articles
    cursor = db["articles"].find({"status": "published"}).sort("title", 1)
    articles = await cursor.to_list(length=100)
    
    return templates.TemplateResponse(
        "quick_edit.html",
        {
            "request": request,
            "articles": articles
        }
    )

@router.get("/random", response_class=RedirectResponse)
async def random_article(db=Depends(get_db)):
    """
    Redirect to a random article.
    """
    # Use aggregation to get a random article
    pipeline = [
        {"$match": {"status": "published"}},
        {"$sample": {"size": 1}}
    ]
    
    results = await db["articles"].aggregate(pipeline).to_list(length=1)
    
    if not results:
        # No articles found, redirect to homepage
        return RedirectResponse(url="/")
    
    # Redirect to the random article
    return RedirectResponse(url=f"/articles/{results[0]['slug']}")

# Special pages routes
@router.get("/special/recentchanges", response_class=HTMLResponse)
async def recent_changes_page(
    request: Request,
    filter: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db=Depends(get_db),
    cache=Depends(get_cache)
):
    """
    Render the recent changes page.
    """
    templates = request.app.state.templates
    
    # Process revisions and proposals
    try:
        # Get recent revisions
        revisions_cursor = db["revisions"].find().sort("createdAt", -1).skip(skip).limit(limit)
        revisions = await revisions_cursor.to_list(length=limit)
        
        # Get recent proposals
        proposals_cursor = db["proposals"].find().sort("proposedAt", -1).skip(skip).limit(limit)
        proposals = await proposals_cursor.to_list(length=limit)
        
        # Combine and sort by date
        changes = []
        
        # Process revisions
        for rev in revisions:
            # Get article
            article = await db["articles"].find_one({"_id": rev["articleId"]})
            if not article:
                continue
                
            # Get user
            user = await db["users"].find_one({"_id": rev["createdBy"]})
            username = user["username"] if user else "Unknown"
            
            changes.append({
                "type": "revision",
                "timestamp": rev["createdAt"],
                "articleId": str(rev["articleId"]),
                "articleTitle": article["title"],
                "userId": str(rev["createdBy"]),
                "username": username,
                "comment": rev.get("comment", "")
            })
        
        # Process proposals
        for prop in proposals:
            # Get article
            article = await db["articles"].find_one({"_id": prop["articleId"]})
            if not article:
                continue
                
            # Get user
            user = await db["users"].find_one({"_id": prop["proposedBy"]})
            username = user["username"] if user else "Unknown"
            
            changes.append({
                "type": "proposal",
                "timestamp": prop["proposedAt"],
                "articleId": str(prop["articleId"]),
                "articleTitle": article["title"],
                "userId": str(prop["proposedBy"]),
                "username": username,
                "comment": prop.get("summary", "")
            })
        
        # Check if we have any changes
        if not changes:
            # Generate some sample changes if no real data exists
            print("No changes found, generating sample data")
            sample_changes = await generate_sample_changes(db)
            changes.extend(sample_changes)
        
        # Sort combined list by timestamp (newest first)
        changes.sort(key=lambda x: x["timestamp"], reverse=True)
        
        # Apply filter if needed
        if filter:
            changes = [c for c in changes if c["type"] == filter]
        
        # Get total count
        total = len(changes)
        
        # Paginate manually
        changes = changes[skip:skip+limit]
        
        # Render template
        return templates.TemplateResponse(
            "recent_changes.html",
            {
                "request": request,
                "changes": changes,
                "total": total,
                "skip": skip,
                "limit": limit,
                "filter": filter
            }
        )
    except Exception as e:
        print(f"Error getting recent changes: {e}")
        # Return empty results on error
        return templates.TemplateResponse(
            "recent_changes.html",
            {
                "request": request,
                "changes": [],
                "total": 0,
                "skip": skip,
                "limit": limit,
                "filter": filter
            }
        )

async def generate_sample_changes(db) -> List[Dict[str, Any]]:
    """
    Generate sample changes for display when no real data exists.
    """
    sample_changes = []
    
    # Get some articles and users to reference
    articles_cursor = db["articles"].find({"status": "published"}).limit(5)
    articles = await articles_cursor.to_list(length=5)
    
    if not articles:
        # If no articles exist, we can't generate sample changes
        return []
    
    users_cursor = db["users"].find().limit(3)
    users = await users_cursor.to_list(length=3)
    
    if not users:
        # If no users exist, use a default
        admin_user = {
            "_id": ObjectId(),
            "username": "admin"
        }
        users = [admin_user]
    
    # Sample comments for revisions
    revision_comments = [
        "Fixed typos in introduction",
        "Updated information in the second paragraph",
        "Added new section on advanced techniques",
        "Corrected historical information",
        "Improved formatting and readability",
        "Added references and citations",
        "Restructured content for better flow"
    ]
    
    # Sample comments for proposals
    proposal_comments = [
        "Suggested new content for the introduction",
        "Proposed additional examples",
        "Suggested clearer explanation of concepts",
        "Proposed update to outdated information",
        "Suggested adding missing details"
    ]
    
    # Generate sample revisions
    now = datetime.now()
    for i in range(10):
        article = random.choice(articles)
        user = random.choice(users)
        
        # Create a sample revision
        sample_changes.append({
            "type": "revision",
            "timestamp": now - timedelta(days=i, hours=random.randint(0, 23), minutes=random.randint(0, 59)),
            "articleId": str(article["_id"]),
            "articleTitle": article["title"],
            "userId": str(user["_id"]),
            "username": user["username"],
            "comment": random.choice(revision_comments)
        })
    
    # Generate sample proposals
    for i in range(5):
        article = random.choice(articles)
        user = random.choice(users)
        
        # Create a sample proposal
        sample_changes.append({
            "type": "proposal",
            "timestamp": now - timedelta(days=i, hours=random.randint(0, 23), minutes=random.randint(0, 59)),
            "articleId": str(article["_id"]),
            "articleTitle": article["title"],
            "userId": str(user["_id"]),
            "username": user["username"],
            "comment": random.choice(proposal_comments)
        })
    
    return sample_changes

@router.get("/special/statistics", response_class=HTMLResponse)
async def statistics_page(
    request: Request,
    db=Depends(get_db),
    cache=Depends(get_cache)
):
    """
    Render the statistics page.
    """
    templates = request.app.state.templates
    
    # Try to get from cache
    cache_key = "statistics_page"
    cached_data = await cache.get(cache_key)
    
    if cached_data:
        return templates.TemplateResponse(
            "statistics.html",
            {
                "request": request,
                "statistics": cached_data
            }
        )
    
    try:
        # Get statistics
        statistics = {}
        
        # Article stats
        statistics["total_articles"] = await db["articles"].count_documents({"status": "published"})
        statistics["total_edits"] = await db["revisions"].count_documents({})
        statistics["total_proposals"] = await db["proposals"].count_documents({})
        
        # User stats
        statistics["total_users"] = await db["users"].count_documents({})
        statistics["new_users_today"] = await db["users"].count_documents({
            "joinDate": {"$gte": datetime.now() - timedelta(days=1)}
        })
        
        # Most active users
        top_editors_cursor = db["users"].find().sort("contributions.editsPerformed", -1).limit(5)
        statistics["top_editors"] = await top_editors_cursor.to_list(length=5)
        
        # Most viewed articles
        top_articles_cursor = db["articles"].find({"status": "published"}).sort("views", -1).limit(5)
        statistics["top_articles"] = await top_articles_cursor.to_list(length=5)
        
        # Recent activity (last 24 hours)
        recent_revisions = await db["revisions"].count_documents({
            "createdAt": {"$gte": datetime.now() - timedelta(days=1)}
        })
        recent_proposals = await db["proposals"].count_documents({
            "proposedAt": {"$gte": datetime.now() - timedelta(days=1)}
        })
        
        statistics["recent_activity"] = {
            "revisions": recent_revisions,
            "proposals": recent_proposals,
            "total": recent_revisions + recent_proposals
        }
        
        # Cache the results
        await cache.set(cache_key, statistics, 1800)  # Cache for 30 minutes
        
        # Render template
        return templates.TemplateResponse(
            "statistics.html",
            {
                "request": request,
                "statistics": statistics
            }
        )
    except Exception as e:
        print(f"Error getting statistics: {e}")
        # Return empty results on error
        return templates.TemplateResponse(
            "statistics.html",
            {
                "request": request,
                "statistics": {}
            }
        )

# Add more necessary special pages here...
@router.get("/special/categories", response_class=HTMLResponse)
async def categories_page(request: Request, db=Depends(get_db)):
    """Redirect to categories page."""
    return RedirectResponse(url="/categories")

@router.get("/special/tags", response_class=HTMLResponse)
async def tags_page(request: Request, db=Depends(get_db)):
    """Redirect to tags page."""
    return RedirectResponse(url="/tags")

@router.get("/categories", response_class=HTMLResponse)
async def categories_list_page(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db=Depends(get_db)
):
    """
    Render the categories list page.
    """
    templates = request.app.state.templates
    
    try:
        # Use aggregation to get unique categories and their count
        pipeline = [
            {"$match": {"status": "published"}},
            {"$unwind": "$categories"},
            {"$group": {"_id": "$categories", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$skip": skip},
            {"$limit": limit},
            {"$project": {"name": "$_id", "count": 1, "_id": 0}}
        ]
        
        categories = await db["articles"].aggregate(pipeline).to_list(length=limit)
        
        # Get total count
        total_pipeline = [
            {"$match": {"status": "published"}},
            {"$unwind": "$categories"},
            {"$group": {"_id": "$categories"}},
            {"$count": "total"}
        ]
        
        total_result = await db["articles"].aggregate(total_pipeline).to_list(length=1)
        total = total_result[0]["total"] if total_result else 0
        
        # Render template
        return templates.TemplateResponse(
            "categories.html",
            {
                "request": request,
                "categories": categories,
                "total": total,
                "skip": skip,
                "limit": limit
            }
        )
    except Exception as e:
        print(f"Error getting categories: {e}")
        return templates.TemplateResponse(
            "categories.html",
            {
                "request": request,
                "categories": [],
                "total": 0,
                "skip": skip,
                "limit": limit
            }
        )

@router.get("/tags", response_class=HTMLResponse)
async def tags_list_page(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db=Depends(get_db)
):
    """
    Render the tags list page.
    """
    templates = request.app.state.templates
    
    try:
        # Use aggregation to get unique tags and their count
        pipeline = [
            {"$match": {"status": "published"}},
            {"$unwind": "$tags"},
            {"$group": {"_id": "$tags", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$skip": skip},
            {"$limit": limit},
            {"$project": {"name": "$_id", "count": 1, "_id": 0}}
        ]
        
        tags = await db["articles"].aggregate(pipeline).to_list(length=limit)
        
        # Get total count
        total_pipeline = [
            {"$match": {"status": "published"}},
            {"$unwind": "$tags"},
            {"$group": {"_id": "$tags"}},
            {"$count": "total"}
        ]
        
        total_result = await db["articles"].aggregate(total_pipeline).to_list(length=1)
        total = total_result[0]["total"] if total_result else 0
        
        # Render template
        return templates.TemplateResponse(
            "tags.html",
            {
                "request": request,
                "tags": tags,
                "total": total,
                "skip": skip,
                "limit": limit
            }
        )
    except Exception as e:
        print(f"Error getting tags: {e}")
        return templates.TemplateResponse(
            "tags.html",
            {
                "request": request,
                "tags": [],
                "total": 0,
                "skip": skip,
                "limit": limit
            }
        )

@router.get("/articles/{article_id}/history", response_class=HTMLResponse)
async def article_history_page(
    request: Request,
    article_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db=Depends(get_db)
):
    """
    Render the article history page.
    """
    templates = request.app.state.templates
    
    try:
        # Check if article exists
        if not ObjectId.is_valid(article_id):
            return templates.TemplateResponse(
                "404.html",
                {"request": request, "message": "Invalid article ID"},
                status_code=404
            )
        
        article = await db["articles"].find_one({"_id": ObjectId(article_id)})
        if not article:
            return templates.TemplateResponse(
                "404.html",
                {"request": request, "message": "Article not found"},
                status_code=404
            )
        
        # Get revisions
        cursor = db["revisions"].find({"articleId": ObjectId(article_id)}).sort("createdAt", -1).skip(skip).limit(limit)
        revisions = await cursor.to_list(length=limit)
        
        # Enhance with user info
        enhanced_revisions = []
        for rev in revisions:
            user = await db["users"].find_one({"_id": rev["createdBy"]})
            username = user["username"] if user else "Unknown"
            
            enhanced_revisions.append({
                **rev,
                "creatorUsername": username
            })
        
        # Get total count
        total = await db["revisions"].count_documents({"articleId": ObjectId(article_id)})
        
        # Get current user to check if they're an editor
        current_user = None
        try:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.replace("Bearer ", "")
                from dependencies.auth import get_current_user
                current_user = await get_current_user(token=token, db=db)
        except:
            pass
        
        is_editor = current_user and current_user.get("role") in ["admin", "editor"]
        
        # Render template
        return templates.TemplateResponse(
            "article_history.html",
            {
                "request": request,
                "article": article,
                "revisions": enhanced_revisions,
                "total": total,
                "skip": skip,
                "limit": limit,
                "is_editor": is_editor
            }
        )
    except Exception as e:
        print(f"Error getting article history: {e}")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": f"Error loading article history: {str(e)}"},
            status_code=500
        )

@router.get("/articles/{article_id}/revisions/{revision_id}", response_class=HTMLResponse)
async def article_revision_page(
    request: Request,
    article_id: str,
    revision_id: str,
    db=Depends(get_db)
):
    """
    Render the article revision page.
    """
    templates = request.app.state.templates
    
    try:
        # Check if article and revision exist
        if not ObjectId.is_valid(article_id) or not ObjectId.is_valid(revision_id):
            return templates.TemplateResponse(
                "404.html",
                {"request": request, "message": "Invalid ID format"},
                status_code=404
            )
        
        article = await db["articles"].find_one({"_id": ObjectId(article_id)})
        if not article:
            return templates.TemplateResponse(
                "404.html",
                {"request": request, "message": "Article not found"},
                status_code=404
            )
        
        revision = await db["revisions"].find_one({
            "_id": ObjectId(revision_id),
            "articleId": ObjectId(article_id)
        })
        
        if not revision:
            return templates.TemplateResponse(
                "404.html",
                {"request": request, "message": "Revision not found"},
                status_code=404
            )
        
        # Get user info
        user = await db["users"].find_one({"_id": revision["createdBy"]})
        username = user["username"] if user else "Unknown"
        
        # Check if user is editor
        current_user = None
        try:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.replace("Bearer ", "")
                from dependencies.auth import get_current_user
                current_user = await get_current_user(token=token, db=db)
        except:
            pass
        
        is_editor = current_user and current_user.get("role") in ["admin", "editor"]
        
        # Render template
        return templates.TemplateResponse(
            "article_revision.html",
            {
                "request": request,
                "article": article,
                "revision": {**revision, "creatorUsername": username},
                "is_editor": is_editor
            }
        )
    except Exception as e:
        print(f"Error getting article revision: {e}")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": f"Error loading revision: {str(e)}"},
            status_code=500
        )

@router.get("/articles/{article_id}/compare/{old_id}/{new_id}", response_class=HTMLResponse)
async def article_compare_page(
    request: Request,
    article_id: str,
    old_id: str,
    new_id: str,
    db=Depends(get_db)
):
    """
    Render the article comparison page.
    """
    templates = request.app.state.templates
    
    try:
        # Check if article and revisions exist
        if not ObjectId.is_valid(article_id) or not ObjectId.is_valid(old_id) or not ObjectId.is_valid(new_id):
            return templates.TemplateResponse(
                "404.html",
                {"request": request, "message": "Invalid ID format"},
                status_code=404
            )
        
        article = await db["articles"].find_one({"_id": ObjectId(article_id)})
        if not article:
            return templates.TemplateResponse(
                "404.html",
                {"request": request, "message": "Article not found"},
                status_code=404
            )
        
        old_revision = await db["revisions"].find_one({
            "_id": ObjectId(old_id),
            "articleId": ObjectId(article_id)
        })
        
        new_revision = await db["revisions"].find_one({
            "_id": ObjectId(new_id),
            "articleId": ObjectId(article_id)
        })
        
        if not old_revision or not new_revision:
            return templates.TemplateResponse(
                "404.html",
                {"request": request, "message": "One or both revisions not found"},
                status_code=404
            )
        
        # Get user info
        old_user = await db["users"].find_one({"_id": old_revision["createdBy"]})
        new_user = await db["users"].find_one({"_id": new_revision["createdBy"]})
        
        old_revision["creatorUsername"] = old_user["username"] if old_user else "Unknown"
        new_revision["creatorUsername"] = new_user["username"] if new_user else "Unknown"
        
        # Render template
        return templates.TemplateResponse(
            "article_compare.html",
            {
                "request": request,
                "article": article,
                "old_revision": old_revision,
                "new_revision": new_revision
            }
        )
    except Exception as e:
        print(f"Error comparing revisions: {e}")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": f"Error comparing revisions: {str(e)}"},
            status_code=500
        )

@router.get("/articles/{article_id}/revisions/{revision_id}/restore", response_class=HTMLResponse)
async def article_restore_page(
    request: Request,
    article_id: str,
    revision_id: str,
    db=Depends(get_db)
):
    """
    Render the article restore confirmation page.
    """
    templates = request.app.state.templates
    
    try:
        # Check if article and revision exist
        if not ObjectId.is_valid(article_id) or not ObjectId.is_valid(revision_id):
            return templates.TemplateResponse(
                "404.html",
                {"request": request, "message": "Invalid ID format"},
                status_code=404
            )
        
        article = await db["articles"].find_one({"_id": ObjectId(article_id)})
        if not article:
            return templates.TemplateResponse(
                "404.html",
                {"request": request, "message": "Article not found"},
                status_code=404
            )
        
        revision = await db["revisions"].find_one({
            "_id": ObjectId(revision_id),
            "articleId": ObjectId(article_id)
        })
        
        if not revision:
            return templates.TemplateResponse(
                "404.html",
                {"request": request, "message": "Revision not found"},
                status_code=404
            )
        
        # Get user info
        user = await db["users"].find_one({"_id": revision["createdBy"]})
        username = user["username"] if user else "Unknown"
        
        # Render template
        return templates.TemplateResponse(
            "article_restore_confirm.html",
            {
                "request": request,
                "article": article,
                "revision": {**revision, "creatorUsername": username}
            }
        )
    except Exception as e:
        print(f"Error loading restore page: {e}")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": f"Error loading restore page: {str(e)}"},
            status_code=500
        )

# Additional routes to add to routes/page_routes.py

@router.get("/articles/{article_id}/propose", response_class=HTMLResponse)
async def propose_edit_page(
    request: Request,
    article_id: str = Path(..., description="Article ID"),
    db=Depends(get_db)
):
    """
    Render the page for creating an edit proposal.
    """
    templates = request.app.state.templates
    
    # Check if article exists
    if not ObjectId.is_valid(article_id):
        return templates.TemplateResponse(
            "404.html",
            {"request": request, "message": "Invalid article ID"},
            status_code=404
        )
    
    article = await db["articles"].find_one({"_id": ObjectId(article_id)})
    if not article:
        return templates.TemplateResponse(
            "404.html",
            {"request": request, "message": "Article not found"},
            status_code=404
        )
    
    # Render template
    return templates.TemplateResponse(
        "propose_edit.html",
        {"request": request, "article": article}
    )

@router.get("/proposals", response_class=HTMLResponse)
async def proposals_list_page(
    request: Request,
    status: Optional[str] = None,
    article_id: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db=Depends(get_db)
):
    """
    Render the page listing edit proposals.
    """
    templates = request.app.state.templates
    
    # Build query
    query = {}
    if status and status != "all":
        query["status"] = status
    
    if article_id and ObjectId.is_valid(article_id):
        query["articleId"] = ObjectId(article_id)
    
    # Get proposals
    cursor = db["proposals"].find(query).sort("proposedAt", -1).skip(skip).limit(limit)
    proposals = await cursor.to_list(length=limit)
    
    # Get total count
    total_count = await db["proposals"].count_documents(query)
    
    # Enhance proposals with article info
    enhanced_proposals = []
    for prop in proposals:
        # Get article info
        article = await db["articles"].find_one({"_id": prop["articleId"]})
        article_title = article["title"] if article else "Unknown Article"
        
        # Get user info
        proposer = await db["users"].find_one({"_id": prop["proposedBy"]})
        proposer_username = proposer["username"] if proposer else "Unknown"
        
        # Get reviewer info if available
        reviewer_username = None
        if prop.get("reviewedBy"):
            reviewer = await db["users"].find_one({"_id": prop["reviewedBy"]})
            reviewer_username = reviewer["username"] if reviewer else "Unknown"
        
        # Add enhanced info
        enhanced_proposals.append({
            **prop,
            "articleTitle": article_title,
            "proposerUsername": proposer_username,
            "reviewerUsername": reviewer_username
        })
    
    # Get article if filtering by article
    article = None
    if article_id and ObjectId.is_valid(article_id):
        article = await db["articles"].find_one({"_id": ObjectId(article_id)})
    
    # Check if user is editor
    is_editor = False
    try:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")
            from dependencies.auth import get_current_user
            current_user = await get_current_user(token=token, db=db)
            is_editor = current_user.get("role") in ["admin", "editor"]
    except:
        pass
    
    # Render template
    return templates.TemplateResponse(
        "proposals_list.html",
        {
            "request": request,
            "proposals": enhanced_proposals,
            "total": total_count,
            "skip": skip,
            "limit": limit,
            "status": status,
            "article": article,
            "is_editor": is_editor
        }
    )

@router.get("/articles/{article_id}/proposals", response_class=HTMLResponse)
async def article_proposals_page(
    request: Request,
    article_id: str,
    status: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db=Depends(get_db)
):
    """
    Render the page listing proposals for a specific article.
    """
    templates = request.app.state.templates
    
    # Check if article exists
    if not ObjectId.is_valid(article_id):
        return templates.TemplateResponse(
            "404.html",
            {"request": request, "message": "Invalid article ID"},
            status_code=404
        )
    
    article = await db["articles"].find_one({"_id": ObjectId(article_id)})
    if not article:
        return templates.TemplateResponse(
            "404.html",
            {"request": request, "message": "Article not found"},
            status_code=404
        )
    
    # Redirect to the general proposals page with article filter
    return RedirectResponse(
        url=f"/proposals?article_id={article_id}" + (f"&status={status}" if status else "")
    )

@router.get("/articles/{article_id}/proposals/{proposal_id}", response_class=HTMLResponse)
async def view_proposal_page(
    request: Request,
    article_id: str,
    proposal_id: str,
    db=Depends(get_db)
):
    """
    Render the page for viewing a specific proposal.
    """
    templates = request.app.state.templates
    
    # Check if article and proposal exist
    if not ObjectId.is_valid(article_id) or not ObjectId.is_valid(proposal_id):
        return templates.TemplateResponse(
            "404.html",
            {"request": request, "message": "Invalid ID format"},
            status_code=404
        )
    
    article = await db["articles"].find_one({"_id": ObjectId(article_id)})
    if not article:
        return templates.TemplateResponse(
            "404.html",
            {"request": request, "message": "Article not found"},
            status_code=404
        )
    
    proposal = await db["proposals"].find_one({
        "_id": ObjectId(proposal_id),
        "articleId": ObjectId(article_id)
    })
    
    if not proposal:
        return templates.TemplateResponse(
            "404.html",
            {"request": request, "message": "Proposal not found"},
            status_code=404
        )
    
    # Get user info
    proposer = await db["users"].find_one({"_id": proposal["proposedBy"]})
    proposer_username = proposer["username"] if proposer else "Unknown"
    
    reviewer_username = None
    if proposal.get("reviewedBy"):
        reviewer = await db["users"].find_one({"_id": proposal["reviewedBy"]})
        reviewer_username = reviewer["username"] if reviewer else "Unknown"
    
    # Check if user is editor
    is_editor = False
    try:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")
            from dependencies.auth import get_current_user
            current_user = await get_current_user(token=token, db=db)
            is_editor = current_user.get("role") in ["admin", "editor"]
    except:
        pass
    
    # Add user info to proposal
    enhanced_proposal = {
        **proposal,
        "proposerUsername": proposer_username,
        "reviewerUsername": reviewer_username
    }
    
    # Render template
    return templates.TemplateResponse(
        "proposal_view.html",
        {
            "request": request,
            "article": article,
            "proposal": enhanced_proposal,
            "is_editor": is_editor
        }
    )

# File: routes/page_routes.py

@router.get("/admin/articles", response_class=HTMLResponse)
async def article_management_page(
    request: Request,
    status: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: Dict[str, Any] = Depends(get_current_admin),
    db=Depends(get_db)
):
    """
    Render the article management page (admin only).
    """
    templates = request.app.state.templates
    
    try:
        # Build query
        query = {}
        
        # Filter by status if provided
        if status:
            query["status"] = status
        
        # Search in title, content, or summary if provided
        if search:
            query["$or"] = [
                {"title": {"$regex": search, "$options": "i"}},
                {"content": {"$regex": search, "$options": "i"}},
                {"summary": {"$regex": search, "$options": "i"}}
            ]
        
        # Get total count
        total_count = await db["articles"].count_documents(query)
        
        # Get articles with pagination
        cursor = db["articles"].find(query).sort("lastUpdatedAt", -1).skip(skip).limit(limit)
        articles = await cursor.to_list(length=limit)
        
        # Render template
        return templates.TemplateResponse(
            "article_management.html",
            {
                "request": request,
                "articles": articles,
                "total": total_count,
                "skip": skip,
                "limit": limit,
                "status": status,
                "search": search,
                "current_user": current_user
            }
        )
    except Exception as e:
        logger.error(f"Error in article management page: {e}")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": str(e)},
            status_code=500
        )

# File: routes/page_routes.py
# Add these route handlers to the page_routes.py file

@router.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_admin),
    db=Depends(get_db)
):
    """
    Render the admin dashboard.
    """
    templates = request.app.state.templates
    
    try:
        # Gather statistics
        stats = {}
        
        # Article stats
        stats["articles"] = await db["articles"].count_documents({"status": "published"})
        
        # User stats
        stats["users"] = await db["users"].count_documents({})
        
        # Pending proposals
        stats["pending_proposals"] = await db["proposals"].count_documents({"status": "pending"})
        
        # Recent activity (last 24 hours)
        recent_revisions = await db["revisions"].count_documents({
            "createdAt": {"$gte": datetime.now() - timedelta(days=1)}
        })
        recent_proposals = await db["proposals"].count_documents({
            "proposedAt": {"$gte": datetime.now() - timedelta(days=1)}
        })
        
        stats["recent_activity"] = {
            "revisions": recent_revisions,
            "proposals": recent_proposals,
            "total": recent_revisions + recent_proposals
        }
        
        # Get recent activity for display
        recent_activity = []
        
        # Get recent revisions
        revisions_cursor = db["revisions"].find().sort("createdAt", -1).limit(5)
        revisions = await revisions_cursor.to_list(length=5)
        
        for rev in revisions:
            article = await db["articles"].find_one({"_id": rev["articleId"]})
            user = await db["users"].find_one({"_id": rev["createdBy"]})
            
            if article and user:
                recent_activity.append({
                    "type": "Edit",
                    "timestamp": rev["createdAt"],
                    "articleId": str(rev["articleId"]),
                    "articleTitle": article["title"],
                    "username": user["username"]
                })
        
        # Get recent proposals
        proposals_cursor = db["proposals"].find().sort("proposedAt", -1).limit(5)
        proposals = await proposals_cursor.to_list(length=5)
        
        for prop in proposals:
            article = await db["articles"].find_one({"_id": prop["articleId"]})
            user = await db["users"].find_one({"_id": prop["proposedBy"]})
            
            if article and user:
                recent_activity.append({
                    "type": "Proposal",
                    "timestamp": prop["proposedAt"],
                    "articleId": str(prop["articleId"]),
                    "articleTitle": article["title"],
                    "username": user["username"]
                })
        
        # Sort by timestamp
        recent_activity.sort(key=lambda x: x["timestamp"], reverse=True)
        recent_activity = recent_activity[:5]  # Only show top 5
        
        # Render template
        return templates.TemplateResponse(
            "admin_dashboard.html",
            {
                "request": request,
                "stats": stats,
                "recent_activity": recent_activity,
                "current_user": current_user
            }
        )
    except Exception as e:
        logger.error(f"Error in admin dashboard: {e}")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": str(e)},
            status_code=500
        )

@router.get("/admin/users", response_class=HTMLResponse)
async def user_management_page(
    request: Request,
    role: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: Dict[str, Any] = Depends(get_current_admin),
    db=Depends(get_db)
):
    """
    Render the user management page.
    """
    templates = request.app.state.templates
    
    try:
        # Build query
        query = {}
        
        # Filter by role if provided
        if role:
            query["role"] = role
        
        # Search in username or email if provided
        if search:
            query["$or"] = [
                {"username": {"$regex": search, "$options": "i"}},
                {"email": {"$regex": search, "$options": "i"}}
            ]
        
        # Get total count
        total_count = await db["users"].count_documents(query)
        
        # Get users with pagination
        cursor = db["users"].find(query).sort("joinDate", -1).skip(skip).limit(limit)
        users = await cursor.to_list(length=limit)
        
        # Render template
        return templates.TemplateResponse(
            "user_management.html",
            {
                "request": request,
                "users": users,
                "total": total_count,
                "skip": skip,
                "limit": limit,
                "role": role,
                "search": search,
                "current_user": current_user
            }
        )
    except Exception as e:
        logger.error(f"Error in user management page: {e}")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": str(e)},
            status_code=500
        )

@router.get("/admin/proposals", response_class=HTMLResponse)
async def admin_proposals_page(
    request: Request,
    status: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: Dict[str, Any] = Depends(get_current_admin),
    db=Depends(get_db)
):
    """
    Admin page for managing all proposals.
    """
    # Redirect to the proposals page with proper filtering
    return RedirectResponse(url=f"/proposals?status={status or 'pending'}")

# File: routes/page_routes.py
# Add this route handler to the page_routes.py file

@router.get("/users/{user_id}", response_class=HTMLResponse)
async def user_profile_page(
    request: Request,
    user_id: str,
    db=Depends(get_db)
):
    """
    Render the user profile page.
    """
    templates = request.app.state.templates
    
    try:
        # Check if user exists
        if not ObjectId.is_valid(user_id):
            return templates.TemplateResponse(
                "404.html",
                {"request": request, "message": "Invalid user ID"},
                status_code=404
            )
        
        user = await db["users"].find_one({"_id": ObjectId(user_id)})
        if not user:
            return templates.TemplateResponse(
                "404.html",
                {"request": request, "message": "User not found"},
                status_code=404
            )
        
        # Remove sensitive info
        if "passwordHash" in user:
            del user["passwordHash"]
        
        # Get user's articles
        articles_cursor = db["articles"].find({"createdBy": ObjectId(user_id)}).sort("createdAt", -1).limit(5)
        articles = await articles_cursor.to_list(length=5)
        
        # Get user's edits/revisions
        revisions_cursor = db["revisions"].find({"createdBy": ObjectId(user_id)}).sort("createdAt", -1).limit(5)
        revisions = await revisions_cursor.to_list(length=5)
        
        # Get user's proposals
        proposals_cursor = db["proposals"].find({"proposedBy": ObjectId(user_id)}).sort("proposedAt", -1).limit(5)
        proposals = await proposals_cursor.to_list(length=5)
        
        # Enhance with article titles
        enhanced_revisions = []
        for rev in revisions:
            article = await db["articles"].find_one({"_id": rev["articleId"]})
            article_title = article["title"] if article else "Unknown Article"
            
            enhanced_revisions.append({
                **rev,
                "articleTitle": article_title
            })
        
        enhanced_proposals = []
        for prop in proposals:
            article = await db["articles"].find_one({"_id": prop["articleId"]})
            article_title = article["title"] if article else "Unknown Article"
            
            enhanced_proposals.append({
                **prop,
                "articleTitle": article_title
            })
        
        # Check if current user is the profile owner or an admin
        current_user = None
        is_self = False
        is_admin = False
        
        try:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.replace("Bearer ", "")
                from dependencies.auth import get_current_user
                current_user = await get_current_user(token=token, db=db)
                
                is_self = str(current_user["_id"]) == user_id
                is_admin = current_user["role"] == "admin"
        except:
            pass
        
        # Render template
        return templates.TemplateResponse(
            "user_profile.html",
            {
                "request": request,
                "user": user,
                "articles": articles,
                "revisions": enhanced_revisions,
                "proposals": enhanced_proposals,
                "is_self": is_self,
                "is_admin": is_admin,
                "current_user": current_user
            }
        )
    except Exception as e:
        logger.error(f"Error displaying user profile: {e}")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": str(e)},
            status_code=500
        )

# File: routes/page_routes.py
# Add this route handler to the page_routes.py file

@router.get("/users/{user_id}/edit", response_class=HTMLResponse)
async def edit_user_profile_page(
    request: Request,
    user_id: str,
    db=Depends(get_db)
):
    """
    Render the user profile edit page.
    """
    templates = request.app.state.templates
    
    try:
        # Check if user exists
        if not ObjectId.is_valid(user_id):
            return templates.TemplateResponse(
                "404.html",
                {"request": request, "message": "Invalid user ID"},
                status_code=404
            )
        
        user = await db["users"].find_one({"_id": ObjectId(user_id)})
        if not user:
            return templates.TemplateResponse(
                "404.html",
                {"request": request, "message": "User not found"},
                status_code=404
            )
        
        # Remove sensitive info
        if "passwordHash" in user:
            del user["passwordHash"]
        
        # Check if current user is the profile owner or an admin
        current_user = None
        is_self = False
        is_admin = False
        
        try:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.replace("Bearer ", "")
                from dependencies.auth import get_current_user
                current_user = await get_current_user(token=token, db=db)
                
                is_self = str(current_user["_id"]) == user_id
                is_admin = current_user["role"] == "admin"
        except:
            pass
        
        # Only allow editing if user is the profile owner or an admin
        if not is_self and not is_admin:
            return templates.TemplateResponse(
                "403.html",
                {"request": request, "message": "You do not have permission to edit this profile"},
                status_code=403
            )
        
        # Render template
        return templates.TemplateResponse(
            "user_profile_edit.html",
            {
                "request": request,
                "user": user,
                "is_self": is_self,
                "is_admin": is_admin,
                "current_user": current_user
            }
        )
    except Exception as e:
        logger.error(f"Error displaying edit profile page: {e}")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": str(e)},
            status_code=500
        )
