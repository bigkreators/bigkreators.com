@router.get("/edit-article/{id}", response_class=HTMLResponse)
async def edit_article_page(
    request: Request,
    id: str = Path(..., description="Article ID or slug"),
    db=Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Render the article editing page.
    """
    try:
        # Find the article
        article = None
        if ObjectId.is_valid(id):
            article = await db["articles"].find_one({"_id": ObjectId(id)})
        
        if not article:
            article = await db["articles"].find_one({"slug": id})
        
        if not article:
            return templates.TemplateResponse(
                "404.html",
                {"request": request, "message": "Article not found"},
                status_code=404
            )
        
        # Check permissions
        is_admin = current_user.get("role") == "admin"
        is_editor = current_user.get("role") == "editor"
        is_owner = str(article.get("createdBy", "")) == str(current_user.get("_id", ""))
        
        if not (is_admin or is_editor or is_owner):
            return templates.TemplateResponse(
                "403.html",
                {"request": request, "message": "You don't have permission to edit this article"},
                status_code=403
            )
        
        # Render template
        return templates.TemplateResponse(
            "edit_article.html",
            {"request": request, "article": article}
        )
    except Exception as e:
        logger.error(f"Error rendering edit article page: {e}")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": f"An error occurred while loading the edit page: {str(e)}"},
            status_code=500
        )
