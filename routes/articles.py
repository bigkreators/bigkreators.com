# File: routes/articles.py
"""
Article API routes with namespace support.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from bson import ObjectId
from typing import List, Optional, Dict, Any
from datetime import datetime

from models.article import Article, ArticleCreate, ArticleUpdate, parse_title_namespace
from models.base import PyObjectId
from dependencies import get_db, get_current_user
from utils.slug import generate_namespace_slug
from utils.wiki_parser import parse_wiki_markup, extract_categories_from_content
from utils.namespace import (
    is_valid_namespace, 
    get_namespace_info, 
    namespace_allows_categories,
    get_searchable_namespaces
)

router = APIRouter(prefix="/api/articles", tags=["articles"])

@router.post("/", response_model=Article)
async def create_article(
    article_data: ArticleCreate,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Create a new article with namespace support and duplicate prevention.
    """
    # Parse namespace from title if not already set
    if not hasattr(article_data, 'namespace') or article_data.namespace is None:
        namespace, title = parse_title_namespace(article_data.title)
        article_data.namespace = namespace
        article_data.title = title
    
    # Validate namespace
    if article_data.namespace and not is_valid_namespace(article_data.namespace):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid namespace: {article_data.namespace}"
        )
    
    # Check for duplicate titles within the same namespace
    existing_title = await db["articles"].find_one({
        "title": {"$regex": f"^{article_data.title}$", "$options": "i"},
        "namespace": article_data.namespace,
        "status": {"$ne": "deleted"}
    })
    if existing_title:
        namespace_display = f"{article_data.namespace}:" if article_data.namespace else ""
        raise HTTPException(
            status_code=400,
            detail=f"Article '{namespace_display}{article_data.title}' already exists"
        )
    
    # Check if namespace allows categories
    if article_data.categories and not namespace_allows_categories(article_data.namespace):
        article_data.categories = []
    
    # Extract categories from content if namespace allows
    if namespace_allows_categories(article_data.namespace):
        content_categories = extract_categories_from_content(article_data.content)
        # Merge with explicitly set categories
        all_categories = list(set(article_data.categories + content_categories))
        article_data.categories = all_categories
    
    # Generate namespace-aware slug with title synchronization
    timestamp = int(datetime.now().timestamp())
    slug = generate_namespace_slug(article_data.namespace, article_data.title, timestamp)
    
    # Ensure slug uniqueness (backup check)
    existing_slug = await db["articles"].find_one({"slug": slug})
    slug_counter = 1
    base_slug = slug
    while existing_slug:
        slug = f"{base_slug}-{slug_counter}"
        existing_slug = await db["articles"].find_one({"slug": slug})
        slug_counter += 1
    
    # Parse wiki markup
    parsed_content, short_description = parse_wiki_markup(article_data.content)
    
    # Create article document
    article_dict = article_data.model_dump(by_alias=True)
    article_dict.update({
        "slug": slug,
        "content": parsed_content,  # Store parsed HTML
        "summary": short_description or article_data.summary,
        "createdBy": current_user["_id"],
        "createdAt": datetime.now(),
        "lastUpdatedAt": datetime.now(),
        "lastUpdatedBy": current_user["_id"],
        "status": "published",
        "views": 0,
        "upvotes": 0,
        "downvotes": 0
    })
    
    # Insert into database
    result = await db["articles"].insert_one(article_dict)
    
    # Update category counts for any categories used
    for category_name in article_data.categories:
        await update_category_counts_for_article_change(db, category_name)
    
    # Retrieve and return created article
    created_article = await db["articles"].find_one({"_id": result.inserted_id})
    return created_article

async def update_category_counts_for_article_change(db, category_name: str):
    """
    Update category counts when articles are added/removed from categories.
    This creates the category if it doesn't exist.
    """
    # Check if category exists
    category = await db["categories"].find_one({
        "name": category_name,
        "status": "active"
    })
    
    if not category:
        # Auto-create category with default description
        from utils.slug import generate_slug
        timestamp = int(datetime.now().timestamp())
        slug = generate_slug(category_name, timestamp)
        
        default_description = f"<p>Articles related to {category_name}.</p>"
        
        category_doc = {
            "name": category_name,
            "slug": slug,
            "description": default_description,
            "parent_category": None,
            "sort_key": None,
            "createdBy": None,  # System-created
            "createdAt": datetime.now(),
            "lastUpdatedAt": datetime.now(),
            "lastUpdatedBy": None,
            "article_count": 0,
            "subcategory_count": 0,
            "status": "active"
        }
        
        await db["categories"].insert_one(category_doc)
    
    # Update article count
    article_count = await db["articles"].count_documents({
        "categories": category_name,
        "status": "published"
    })
    
    await db["categories"].update_one(
        {"name": category_name, "status": "active"},
        {
            "$set": {
                "article_count": article_count,
                "lastUpdatedAt": datetime.now()
            }
        }
    )

@router.get("/", response_model=List[Article])
async def list_articles(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    category: Optional[str] = Query(None),
    tag: Optional[str] = Query(None),
    namespace: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    sort: Optional[str] = Query("newest"),
    db=Depends(get_db)
):
    """
    List articles with filtering by namespace, category, tag, etc.
    """
    # Build query
    query = {"status": "published"}
    
    # Filter by namespace
    if namespace is not None:
        if namespace == "main":
            query["namespace"] = ""
        else:
            query["namespace"] = namespace
    else:
        # Only include searchable namespaces by default
        searchable_ns = get_searchable_namespaces()
        query["namespace"] = {"$in": searchable_ns}
    
    # Filter by category
    if category:
        query["categories"] = category
    
    # Filter by tag
    if tag:
        query["tags"] = tag
    
    # Search in title and content
    if search:
        query["$or"] = [
            {"title": {"$regex": search, "$options": "i"}},
            {"summary": {"$regex": search, "$options": "i"}},
            {"content": {"$regex": search, "$options": "i"}}
        ]
    
    # Build sort
    sort_options = {
        "newest": [("createdAt", -1)],
        "oldest": [("createdAt", 1)],
        "mostviewed": [("views", -1)],
        "title": [("title", 1)],
        "updated": [("lastUpdatedAt", -1)]
    }
    sort_query = sort_options.get(sort, [("createdAt", -1)])
    
    # Execute query
    cursor = db["articles"].find(query).sort(sort_query).skip(skip).limit(limit)
    articles = await cursor.to_list(length=limit)
    
    return articles

@router.get("/{article_id}", response_model=Article)
async def get_article(
    article_id: str = Path(..., description="Article ID or slug"),
    db=Depends(get_db)
):
    """
    Get a single article by ID or slug, with support for namespace:title format.
    """
    # Try to find by slug first (handles namespace:title format)
    article = await db["articles"].find_one({"slug": article_id, "status": "published"})
    
    # If not found by slug, try by ObjectId
    if not article and ObjectId.is_valid(article_id):
        article = await db["articles"].find_one({
            "_id": ObjectId(article_id),
            "status": "published"
        })
    
    # If still not found, try to parse as namespace:title and find by those fields
    if not article and ":" in article_id:
        namespace, title = article_id.split(":", 1)
        # Convert underscores back to spaces in title
        title = title.replace("_", " ")
        
        article = await db["articles"].find_one({
            "namespace": namespace,
            "title": title,
            "status": "published"
        })
    
    # Final fallback: try to find article by title pattern matching (for legacy URLs)
    if not article:
        # Convert slug back to potential title patterns
        title_patterns = [
            article_id.replace('-', ' ').title(),
            article_id.replace('-', ' '),
            article_id.replace('_', ' ').title(),
            article_id.replace('_', ' ')
        ]
        
        for pattern in title_patterns:
            article = await db["articles"].find_one({
                "title": {"$regex": f"^{pattern}$", "$options": "i"},
                "status": "published"
            })
            if article:
                break
    
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    # Increment view count
    await db["articles"].update_one(
        {"_id": article["_id"]},
        {"$inc": {"views": 1}}
    )
    
    return article

@router.put("/{article_id}", response_model=Article)
async def update_article(
    article_id: str,
    article_update: ArticleUpdate,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Update an existing article.
    """
    # Validate article ID
    if not ObjectId.is_valid(article_id):
        raise HTTPException(status_code=400, detail="Invalid article ID")
    
    # Find existing article
    existing_article = await db["articles"].find_one({"_id": ObjectId(article_id)})
    if not existing_article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    # Build update data
    update_data = {}
    
    # Handle title and namespace changes with duplicate prevention
    if article_update.title is not None:
        namespace, title = parse_title_namespace(article_update.title)
        
        # Check for duplicate titles within the same namespace (excluding current article)
        existing_title = await db["articles"].find_one({
            "title": {"$regex": f"^{title}$", "$options": "i"},
            "namespace": namespace,
            "status": {"$ne": "deleted"},
            "_id": {"$ne": ObjectId(article_id)}
        })
        if existing_title:
            namespace_display = f"{namespace}:" if namespace else ""
            raise HTTPException(
                status_code=400,
                detail=f"Article '{namespace_display}{title}' already exists"
            )
        
        update_data["title"] = title
        update_data["namespace"] = namespace
        
        # Generate new slug if title or namespace changed
        if title != existing_article["title"] or namespace != existing_article.get("namespace", ""):
            timestamp = int(datetime.now().timestamp())
            new_slug = generate_namespace_slug(namespace, title, timestamp)
            
            # Ensure slug uniqueness
            existing_slug = await db["articles"].find_one({
                "slug": new_slug,
                "_id": {"$ne": ObjectId(article_id)}
            })
            slug_counter = 1
            base_slug = new_slug
            while existing_slug:
                new_slug = f"{base_slug}-{slug_counter}"
                existing_slug = await db["articles"].find_one({
                    "slug": new_slug,
                    "_id": {"$ne": ObjectId(article_id)}
                })
                slug_counter += 1
            
            update_data["slug"] = new_slug
    
    # Handle namespace changes
    if article_update.namespace is not None:
        if not is_valid_namespace(article_update.namespace):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid namespace: {article_update.namespace}"
            )
        update_data["namespace"] = article_update.namespace
    
    # Handle content changes
    if article_update.content is not None:
        parsed_content, short_description = parse_wiki_markup(article_update.content)
        update_data["content"] = parsed_content
        
        # Update summary with short description if found
        if short_description:
            update_data["summary"] = short_description
    
    # Handle other fields
    for field in ["summary", "categories", "tags", "metadata", "status"]:
        value = getattr(article_update, field, None)
        if value is not None:
            update_data[field] = value
    
    # Extract categories from content if applicable
    current_namespace = update_data.get("namespace", existing_article.get("namespace", ""))
    old_categories = existing_article.get("categories", [])
    new_categories = old_categories
    
    if namespace_allows_categories(current_namespace) and article_update.content:
        content_categories = extract_categories_from_content(article_update.content)
        existing_categories = update_data.get("categories", existing_article.get("categories", []))
        all_categories = list(set(existing_categories + content_categories))
        update_data["categories"] = all_categories
        new_categories = all_categories
    elif "categories" in update_data:
        new_categories = update_data["categories"]
    
    # Add update metadata
    update_data["lastUpdatedAt"] = datetime.now()
    update_data["lastUpdatedBy"] = current_user["_id"]
    
    # Update article
    await db["articles"].update_one(
        {"_id": ObjectId(article_id)},
        {"$set": update_data}
    )
    
    # Update category counts for changed categories
    affected_categories = set(old_categories + new_categories)
    for category_name in affected_categories:
        await update_category_counts_for_article_change(db, category_name)
    
    # Return updated article
    updated_article = await db["articles"].find_one({"_id": ObjectId(article_id)})
    return updated_article

@router.delete("/{article_id}")
async def delete_article(
    article_id: str,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Delete an article (soft delete by setting status to 'deleted').
    """
    if not ObjectId.is_valid(article_id):
        raise HTTPException(status_code=400, detail="Invalid article ID")
    
    result = await db["articles"].update_one(
        {"_id": ObjectId(article_id)},
        {
            "$set": {
                "status": "deleted",
                "lastUpdatedAt": datetime.now(),
                "lastUpdatedBy": current_user["_id"]
            }
        }
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Article not found")
    
    return {"message": "Article deleted successfully"}

@router.get("/namespace/{namespace}")
async def list_articles_by_namespace(
    namespace: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db=Depends(get_db)
):
    """
    List articles in a specific namespace.
    """
    # Handle "main" namespace
    if namespace == "main":
        namespace = ""
    
    # Validate namespace
    if namespace and not is_valid_namespace(namespace):
        raise HTTPException(status_code=400, detail="Invalid namespace")
    
    # Query articles
    query = {"namespace": namespace, "status": "published"}
    cursor = db["articles"].find(query).sort([("title", 1)]).skip(skip).limit(limit)
    articles = await cursor.to_list(length=limit)
    
    # Get namespace info
    namespace_info = get_namespace_info(namespace)
    
    return {
        "namespace": namespace,
        "namespace_info": namespace_info,
        "articles": articles,
        "total": await db["articles"].count_documents(query)
    }

@router.get("/namespaces/list")
async def list_namespaces(db=Depends(get_db)):
    """
    List all namespaces with article counts.
    """
    from utils.namespace import NAMESPACE_CONFIG
    
    namespaces = []
    for ns_key, ns_config in NAMESPACE_CONFIG.items():
        count = await db["articles"].count_documents({
            "namespace": ns_key,
            "status": "published"
        })
        
        namespaces.append({
            "key": ns_key,
            "name": ns_config["name"],
            "description": ns_config["description"],
            "url_prefix": ns_config["url_prefix"],
            "article_count": count,
            "searchable": ns_config["searchable"],
            "allow_categories": ns_config["allow_categories"]
        })
    
    return namespaces
