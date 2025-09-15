# File: routes/categories.py
"""
Category API routes with auto-population functionality.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from bson import ObjectId
from typing import List, Optional, Dict, Any
from datetime import datetime

from models.category import Category, CategoryCreate, CategoryUpdate, CategoryWithArticles
from models.base import PyObjectId
from dependencies import get_db, get_current_user
from utils.slug import generate_slug
from utils.wiki_parser import parse_wiki_markup

router = APIRouter(prefix="/api/categories", tags=["categories"])

@router.post("/", response_model=Category)
async def create_category(
    category_data: CategoryCreate,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Create a new category with description content.
    """
    # Check for duplicate category name
    existing = await db["categories"].find_one({
        "name": {"$regex": f"^{category_data.name}$", "$options": "i"},
        "status": {"$ne": "deleted"}
    })
    if existing:
        raise HTTPException(
            status_code=400, 
            detail=f"Category '{category_data.name}' already exists"
        )
    
    # Generate slug from category name
    timestamp = int(datetime.now().timestamp())
    slug = generate_slug(category_data.name, timestamp)
    
    # Parse description content as wiki markup
    parsed_description, _ = parse_wiki_markup(category_data.description)
    
    # Create category document
    category_dict = category_data.model_dump(by_alias=True)
    category_dict.update({
        "slug": slug,
        "description": parsed_description,  # Store parsed HTML
        "createdBy": current_user["_id"],
        "createdAt": datetime.now(),
        "lastUpdatedAt": datetime.now(),
        "lastUpdatedBy": current_user["_id"],
        "article_count": 0,
        "subcategory_count": 0,
        "status": "active"
    })
    
    # Insert into database
    result = await db["categories"].insert_one(category_dict)
    
    # Update article counts for parent category if specified
    if category_data.parent_category:
        await update_category_counts(db, category_data.parent_category)
    
    # Retrieve and return created category
    created_category = await db["categories"].find_one({"_id": result.inserted_id})
    return created_category

@router.get("/", response_model=List[Category])
async def list_categories(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    parent: Optional[str] = Query(None, description="Filter by parent category"),
    search: Optional[str] = Query(None, description="Search category names and descriptions"),
    sort: Optional[str] = Query("name", description="Sort by: name, created, articles, updated"),
    db=Depends(get_db)
):
    """
    List categories with filtering and sorting.
    """
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
    
    # Execute query
    cursor = db["categories"].find(query).sort(sort_query).skip(skip).limit(limit)
    categories = await cursor.to_list(length=limit)
    
    return categories

@router.get("/{category_name}", response_model=CategoryWithArticles)
async def get_category_with_articles(
    category_name: str = Path(..., description="Category name or slug"),
    article_skip: int = Query(0, ge=0, description="Skip articles for pagination"),
    article_limit: int = Query(20, ge=1, le=100, description="Limit articles returned"),
    sort_articles: str = Query("title", description="Sort articles by: title, created, views, updated"),
    db=Depends(get_db)
):
    """
    Get a category with its description and auto-populated article list.
    """
    # Try to find category by name or slug
    category = await db["categories"].find_one({
        "$or": [
            {"name": {"$regex": f"^{category_name}$", "$options": "i"}},
            {"slug": category_name}
        ],
        "status": "active"
    })
    
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
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
    
    # Get subcategories
    subcategories_cursor = db["categories"].find({
        "parent_category": category["name"],
        "status": "active"
    }).sort([("name", 1)])
    
    subcategories = await subcategories_cursor.to_list(length=None)
    
    # Prepare response
    category_with_articles = CategoryWithArticles(**category)
    category_with_articles.articles = articles
    category_with_articles.subcategories = subcategories
    
    return category_with_articles

@router.put("/{category_id}", response_model=Category)
async def update_category(
    category_id: str,
    category_update: CategoryUpdate,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Update an existing category.
    """
    # Validate category ID
    if not ObjectId.is_valid(category_id):
        raise HTTPException(status_code=400, detail="Invalid category ID")
    
    # Find existing category
    existing_category = await db["categories"].find_one({"_id": ObjectId(category_id)})
    if not existing_category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Build update data
    update_data = {}
    
    # Check for name conflicts if name is being changed
    if category_update.name and category_update.name != existing_category["name"]:
        existing_name = await db["categories"].find_one({
            "name": {"$regex": f"^{category_update.name}$", "$options": "i"},
            "status": {"$ne": "deleted"},
            "_id": {"$ne": ObjectId(category_id)}
        })
        if existing_name:
            raise HTTPException(
                status_code=400, 
                detail=f"Category '{category_update.name}' already exists"
            )
        
        update_data["name"] = category_update.name
        
        # Generate new slug
        timestamp = int(datetime.now().timestamp())
        update_data["slug"] = generate_slug(category_update.name, timestamp)
    
    # Handle description changes
    if category_update.description is not None:
        parsed_description, _ = parse_wiki_markup(category_update.description)
        update_data["description"] = parsed_description
    
    # Handle other fields
    for field in ["parent_category", "sort_key"]:
        value = getattr(category_update, field, None)
        if value is not None:
            update_data[field] = value
    
    # Add update metadata
    update_data["lastUpdatedAt"] = datetime.now()
    update_data["lastUpdatedBy"] = current_user["_id"]
    
    # Update category
    await db["categories"].update_one(
        {"_id": ObjectId(category_id)},
        {"$set": update_data}
    )
    
    # Update counts if parent changed
    old_parent = existing_category.get("parent_category")
    new_parent = update_data.get("parent_category", old_parent)
    
    if old_parent != new_parent:
        if old_parent:
            await update_category_counts(db, old_parent)
        if new_parent:
            await update_category_counts(db, new_parent)
    
    # Return updated category
    updated_category = await db["categories"].find_one({"_id": ObjectId(category_id)})
    return updated_category

@router.delete("/{category_id}")
async def delete_category(
    category_id: str,
    force: bool = Query(False, description="Force delete even if category has articles"),
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Delete a category (soft delete by setting status to 'deleted').
    """
    if not ObjectId.is_valid(category_id):
        raise HTTPException(status_code=400, detail="Invalid category ID")
    
    # Find category
    category = await db["categories"].find_one({"_id": ObjectId(category_id)})
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Check if category has articles
    article_count = await db["articles"].count_documents({
        "categories": category["name"],
        "status": "published"
    })
    
    if article_count > 0 and not force:
        raise HTTPException(
            status_code=400,
            detail=f"Category has {article_count} articles. Use force=true to delete anyway."
        )
    
    # Check if category has subcategories
    subcategory_count = await db["categories"].count_documents({
        "parent_category": category["name"],
        "status": "active"
    })
    
    if subcategory_count > 0 and not force:
        raise HTTPException(
            status_code=400,
            detail=f"Category has {subcategory_count} subcategories. Use force=true to delete anyway."
        )
    
    # Soft delete
    await db["categories"].update_one(
        {"_id": ObjectId(category_id)},
        {
            "$set": {
                "status": "deleted",
                "lastUpdatedAt": datetime.now(),
                "lastUpdatedBy": current_user["_id"]
            }
        }
    )
    
    # Update parent category counts
    if category.get("parent_category"):
        await update_category_counts(db, category["parent_category"])
    
    return {"message": "Category deleted successfully"}

@router.post("/{category_name}/refresh-counts")
async def refresh_category_counts(
    category_name: str,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Manually refresh the article and subcategory counts for a category.
    """
    await update_category_counts(db, category_name)
    return {"message": f"Counts refreshed for category '{category_name}'"}

async def update_category_counts(db, category_name: str):
    """
    Update article and subcategory counts for a category.
    """
    # Count articles
    article_count = await db["articles"].count_documents({
        "categories": category_name,
        "status": "published"
    })
    
    # Count subcategories
    subcategory_count = await db["categories"].count_documents({
        "parent_category": category_name,
        "status": "active"
    })
    
    # Update the category
    await db["categories"].update_one(
        {"name": category_name, "status": "active"},
        {
            "$set": {
                "article_count": article_count,
                "subcategory_count": subcategory_count,
                "lastUpdatedAt": datetime.now()
            }
        }
    )

@router.get("/stats/overview")
async def get_category_statistics(db=Depends(get_db)):
    """
    Get overview statistics about categories.
    """
    # Total categories
    total_categories = await db["categories"].count_documents({"status": "active"})
    
    # Categories with articles
    categories_with_articles = await db["categories"].count_documents({
        "status": "active",
        "article_count": {"$gt": 0}
    })
    
    # Empty categories
    empty_categories = total_categories - categories_with_articles
    
    # Most popular categories
    popular_categories = await db["categories"].find({
        "status": "active"
    }).sort([("article_count", -1)]).limit(10).to_list(length=10)
    
    # Recently created categories
    recent_categories = await db["categories"].find({
        "status": "active"
    }).sort([("createdAt", -1)]).limit(5).to_list(length=5)
    
    return {
        "total_categories": total_categories,
        "categories_with_articles": categories_with_articles,
        "empty_categories": empty_categories,
        "popular_categories": popular_categories,
        "recent_categories": recent_categories
    }
