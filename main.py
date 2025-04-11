"""
Main entry point for the Kryptopedia application.
"""
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import config
from services.database import Database
from utils.template_filters import strftime_filter, truncate_filter, strip_html_filter, format_number_filter
from routes import auth, articles, media, proposals, rewards, special, templates

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

# Initialize templates
templates = Jinja2Templates(directory=config.TEMPLATES_DIR)

# Add template filters
templates.env.filters["strftime"] = strftime_filter
templates.env.filters["truncate"] = truncate_filter
templates.env.filters["strip_html"] = strip_html_filter
templates.env.filters["format_number"] = format_number_filter

# Initialize database service
db_service = Database(mongo_uri=config.MONGO_URI, db_name=config.DB_NAME)

# Mount static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Mount media directory if using local storage
if config.STORAGE_TYPE == "local":
    os.makedirs(config.MEDIA_FOLDER, exist_ok=True)
    app.mount("/media", StaticFiles(directory=config.MEDIA_FOLDER), name="media")

# Include routes
app.include_router(auth.router, prefix=f"{config.API_PREFIX}/auth", tags=["Authentication"])
app.include_router(articles.router, prefix=f"{config.API_PREFIX}/articles", tags=["Articles"])
app.include_router(media.router, prefix=f"{config.API_PREFIX}/media", tags=["Media"])
app.include_router(proposals.router, prefix=f"{config.API_PREFIX}/proposals", tags=["Proposals"])
app.include_router(rewards.router, prefix=f"{config.API_PREFIX}/rewards", tags=["Rewards"])
app.include_router(special.router, prefix=f"{config.API_PREFIX}/special", tags=["Special Pages"])

# Include template routes at root level
app.include_router(templates.router)

# Startup event
@app.on_event("startup")
async def startup_event():
    """
    Initialize services on application startup.
    """
    # Connect to database
    await db_service.connect()
    
    # Create required directories
    os.makedirs("static", exist_ok=True)
    os.makedirs(config.TEMPLATES_DIR, exist_ok=True)
    os.makedirs(config.MEDIA_FOLDER, exist_ok=True)
    
    print(f"Kryptopedia is running in {'production' if not config.API_DEBUG else 'development'} mode")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """
    Clean up resources on application shutdown.
    """
    # Close database connection
    await db_service.close()

# Error handler for 404 Not Found
@app.exception_handler(404)
async def not_found_exception_handler(request: Request, exc):
    """
    Custom 404 error handler to return the 404 template.
    """
    return templates.TemplateResponse(
        "404.html",
        {"request": request, "message": "Page not found"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=config.API_DEBUG)
