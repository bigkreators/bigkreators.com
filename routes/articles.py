@router.put("/{id}", response_model=Article)
async def update_article(
    id: str,
    article_update: ArticleUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db=Depends(get_db),
    search=Depends(get_search),
    cache=Depends(get_cache)
):
    """
    Update an article.
    """
    try:
        # Validate ID
        if not ObjectId.is_valid(id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid article ID"
            )
        
        # Get the article
        article = await db["articles"].find_one({"_id": ObjectId(id)})
        if not article:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Article not found"
            )
        
        # Check permissions
        is_admin = current_user.get("role") == "admin"
        is_editor = current_user.get("role") == "editor"
        is_owner = str(article.get("createdBy", "")) == str(current_user.get("_id", ""))
        
        if not (is_admin or is_editor or is_owner):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to edit this article"
            )
        
        # Build update data
        update_data = {}
        
        if article_update.title is not None:
            update_data["title"] = article_update.title
            
            # If title changes, update slug
            if article_update.title != article["title"]:
                update_data["slug"] = generate_slug(article_update.title)
        
        if article_update.content is not None:
            update_data["content"] = article_update.content
        
        if article_update.summary is not None:
            update_data["summary"] = article_update.summary
        
        if article_update.categories is not None:
            update_data["categories"] = article_update.categories
        
        if article_update.tags is not None:
            update_data["tags"] = article_update.tags
        
        if article_update.metadata is not None:
            update_data["metadata"] = article_update.metadata.dict() if hasattr(article_update.metadata, "dict") else article_update.metadata
        
        # Add update metadata
        update_data["lastUpdatedAt"] = datetime.now()
        update_data["lastUpdatedBy"] = current_user["_id"]
        
        # Get edit comment (if provided)
        edit_comment = "Updated article"
        if hasattr(article_update, "editComment") and article_update.editComment:
            edit_comment = article_update.editComment
        
        # Create revision
        revision = {
            "articleId": ObjectId(id),
            "content": article["content"],  # Save the old content
            "createdBy": current_user["_id"],
            "createdAt": datetime.now(),
            "comment": edit_comment
        }
        
        await db["revisions"].insert_one(revision)
        
        # Update the article
        await db["articles"].update_one(
            {"_id": ObjectId(id)},
            {"$set": update_data}
        )
        
        # Update search index
        if search is not None:
            try:
                search_update = {k: v for k, v in update_data.items() if k in ["title", "content", "summary", "categories", "tags"]}
                search_update["updated"] = datetime.now().isoformat()
                search_update["updatedBy"] = current_user["username"]
                
                await search.update(
                    index="articles",
                    id=id,
                    document=search_update
                )
            except Exception as e:
                logger.error(f"Error updating article in search: {e}")
        
        # Invalidate cache
        await cache.delete(f"article:{id}")
        if "slug" in update_data:
            await cache.delete(f"article:{article['slug']}")
        
        # Increment user's edit count
        await db["users"].update_one(
            {"_id": current_user["_id"]},
            {"$inc": {"contributions.editsPerformed": 1}}
        )
        
        # Get updated article
        updated_article = await db["articles"].find_one({"_id": ObjectId(id)})
        return updated_article
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating article: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update article: {str(e)}"
        )
