# File: main.py
"""
Main entry point for the Kryptopedia application.
This consolidated version includes all necessary features and proper error handling.
"""
import os
import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates

import config
from services.database import Database

# Configure logging
logging.basicConfig(
    level=logging.INFO if not config.API_DEBUG else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Kryptopedia API",
    description="API for Kryptopedia Wiki",
    version="0.1.0",
    debug=config.API_DEBUG
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database service
db_service = Database(mongo_uri=config.MONGO_URI, db_name=config.DB_NAME)

# Initialize templates
try:
    # Ensure template directory exists
    os.makedirs(config.TEMPLATES_DIR, exist_ok=True)
    
    # Create Jinja2Templates instance
    templates = Jinja2Templates(directory=config.TEMPLATES_DIR)
    
    # Register template filters
    try:
        from utils.template_filters import (
            strftime_filter, 
            truncate_filter, 
            strip_html_filter, 
            format_number_filter
        )
        
        templates.env.filters["strftime"] = strftime_filter
        templates.env.filters["truncate"] = truncate_filter
        templates.env.filters["strip_html"] = strip_html_filter
        templates.env.filters["format_number"] = format_number_filter
        
        logger.info(f"Template filters registered: {list(templates.env.filters.keys())}")
    except Exception as e:
        logger.error(f"Failed to register template filters: {e}")
    
    # Store templates globally for use in routes
    from template_engine import templates as global_templates
    global_templates = templates
    logger.info("Template engine initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize templates: {e}")
    templates = None

# Mount static files directory
try:
    os.makedirs("static", exist_ok=True)
    app.mount("/static", StaticFiles(directory="static"), name="static")
    logger.info("Static files directory mounted")
except Exception as e:
    logger.error(f"Failed to mount static files directory: {e}")

# Mount media directory if using local storage
if config.STORAGE_TYPE == "local":
    try:
        os.makedirs(config.MEDIA_FOLDER, exist_ok=True)
        app.mount("/media", StaticFiles(directory=config.MEDIA_FOLDER), name="media")
        logger.info(f"Media directory mounted: {config.MEDIA_FOLDER}")
    except Exception as e:
        logger.error(f"Failed to mount media directory: {e}")

# Register API routes
def register_api_routes():
    """Register all API routes with proper error handling"""
    route_modules = [
        {"name": "auth", "prefix": f"{config.API_PREFIX}/auth", "tags": ["Authentication"]},
        {"name": "articles", "prefix": f"{config.API_PREFIX}/articles", "tags": ["Articles"]},
        {"name": "media", "prefix": f"{config.API_PREFIX}/media", "tags": ["Media"]},
        {"name": "proposals", "prefix": f"{config.API_PREFIX}/proposals", "tags": ["Proposals"]},
        {"name": "rewards", "prefix": f"{config.API_PREFIX}/rewards", "tags": ["Rewards"]},
        {"name": "special", "prefix": f"{config.API_PREFIX}/special", "tags": ["Special Pages"]},
    ]
    
    for route_module in route_modules:
        try:
            module = __import__(f"routes.{route_module['name']}", fromlist=["router"])
            app.include_router(module.router, prefix=route_module["prefix"], tags=route_module["tags"])
            logger.info(f"Registered {route_module['name']} routes")
        except Exception as e:
            logger.error(f"Failed to register {route_module['name']} routes: {e}")

# Register page routes (no prefix)
try:
    from routes.page_routes import router as page_router
    app.include_router(page_router)
    logger.info("Page routes registered successfully")
except Exception as e:
    logger.error(f"Failed to register page routes: {e}")

# Register API routes
register_api_routes()

# Global exception handler for 500 errors
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler for uncaught exceptions.
    """
    logger.error(f"Uncaught exception: {str(exc)}", exc_info=True)
    
    # Return JSON for API endpoints, HTML for pages
    if request.url.path.startswith(config.API_PREFIX):
        return JSONResponse(
            status_code=500,
            content={"detail": "An internal server error occurred. Please try again later."}
        )
    
    if templates:
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": "An unexpected error occurred. Please try again later."},
            status_code=500
        )
    
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please try again later."}
    )

# Error handler for 404 Not Found
@app.exception_handler(404)
async def not_found_exception_handler(request: Request, exc):
    """
    Custom 404 error handler to return the 404 template or JSON response.
    """
    if request.url.path.startswith(config.API_PREFIX):
        return JSONResponse(
            status_code=404,
            content={"detail": "The requested resource was not found"}
        )
    
    if templates:
        return templates.TemplateResponse(
            "404.html",
            {"request": request, "message": "Page not found"},
            status_code=404
        )
    
    return JSONResponse(
        status_code=404,
        content={"detail": "The requested resource was not found"}
    )

# Startup event
@app.on_event("startup")
async def startup_event():
    """
    Initialize services on application startup.
    """
    try:
        # Connect to database
        await db_service.connect()
        logger.info(f"Connected to database: {config.DB_NAME}")
        
        # Create required directories
        os.makedirs("static", exist_ok=True)
        os.makedirs(config.TEMPLATES_DIR, exist_ok=True)
        os.makedirs(config.MEDIA_FOLDER, exist_ok=True)
        
        # Initialize search index if needed
        try:
            from dependencies.search import get_search
            search_service = await anext(get_search())
            # Create necessary indices
            await search_service.create_index("articles", {
                "properties": {
                    "title": {"type": "text"},
                    "content": {"type": "text"},
                    "summary": {"type": "text"},
                    "categories": {"type": "keyword"},
                    "tags": {"type": "keyword"}
                }
            })
            logger.info("Search indices initialized")
        except Exception as e:
            logger.warning(f"Search service initialization skipped: {e}")
        
        logger.info(f"Kryptopedia is running in {'production' if not config.API_DEBUG else 'development'} mode")
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """
    Clean up resources on application shutdown.
    """
    try:
        # Close database connection
        await db_service.close()
        logger.info("Database connection closed")
        
        # Close cache connection if applicable
        try:
            from dependencies.cache import get_cache
            cache_service = await anext(get_cache())
            await cache_service.close()
            logger.info("Cache connection closed")
        except Exception as e:
            logger.debug(f"No cache connection to close: {e}")
        
        # Close search connection if applicable
        try:
            from dependencies.search import get_search
            search_service = await anext(get_search())
            await search_service.close()
            logger.info("Search connection closed")
        except Exception as e:
            logger.debug(f"No search connection to close: {e}")
        
        logger.info("Kryptopedia shutdown complete")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")
    
    # Print startup message
    print(f"\n{'='*60}")
    print(f"Kryptopedia starting on http://{host}:{port}")
    print(f"API documentation: http://{host}:{port}/docs")
    print(f"Environment: {'Development' if config.API_DEBUG else 'Production'}")
    print(f"{'='*60}\n")
    
    uvicorn.run("main:app", host=host, port=port, reload=config.API_DEBUG)
