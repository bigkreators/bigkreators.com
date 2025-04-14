"""
Main entry point for the Kryptopedia application.
Uses a properly structured approach with separated modules.
"""
import os
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse

import config
from services.database import Database
from utils.template_filters import strftime_filter, truncate_filter, strip_html_filter, format_number_filter, escapejs_filter

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if config.API_DEBUG else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("kryptopedia")

# Import the routes
from routes import auth, articles, media, proposals, rewards, special, profile
from pages import router as page_router, add_error_handlers, community, donate, help, admin


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

# Add debug middleware in development mode
if config.API_DEBUG:
    @app.middleware("http")
    async def debug_request(request: Request, call_next):
        """
        Debug middleware to log requests and responses in development mode.
        """
        logger.debug(f"Request: {request.method} {request.url.path}")
        
        try:
            response = await call_next(request)
            logger.debug(f"Response: {response.status_code}")
            return response
        except Exception as e:
            logger.exception(f"Error handling request: {e}")
            raise

# Initialize database service
db_service = Database(mongo_uri=config.MONGO_URI, db_name=config.DB_NAME)

# Initialize templates - create the global instance that all routes will use
templates = Jinja2Templates(directory=config.TEMPLATES_DIR)

# Register template filters
templates.env.filters["strftime"] = strftime_filter
templates.env.filters["truncate"] = truncate_filter
templates.env.filters["strip_html"] = strip_html_filter
templates.env.filters["format_number"] = format_number_filter
templates.env.filters["escapejs"] = escapejs_filter

# Make templates available to the page_router by adding it to app.state
# This ensures all routes use the same template instance
app.state.templates = templates

# Mount static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Mount media directory if using local storage
if config.STORAGE_TYPE == "local":
    os.makedirs(config.MEDIA_FOLDER, exist_ok=True)
    app.mount("/media", StaticFiles(directory=config.MEDIA_FOLDER), name="media")

# Include API routes
app.include_router(auth.router, prefix=f"{config.API_PREFIX}/auth", tags=["Authentication"])
app.include_router(articles.router, prefix=f"{config.API_PREFIX}/articles", tags=["Articles"])
app.include_router(media.router, prefix=f"{config.API_PREFIX}/media", tags=["Media"])
app.include_router(proposals.router, prefix=f"{config.API_PREFIX}/proposals", tags=["Proposals"])
app.include_router(rewards.router, prefix=f"{config.API_PREFIX}/rewards", tags=["Rewards"])
app.include_router(special.router, prefix=f"{config.API_PREFIX}/special", tags=["Special Pages"])
app.include_router(profile.router, prefix=f"{config.API_PREFIX}/users", tags=["User Profiles"])
app.include_router(community.router, prefix=f"{config.API_PREFIX}/community", tags=["Community"])
app.include_router(donate.router, prefix=f"{config.API_PREFIX}/donate", tags=["Donations"])
app.include_router(admin.router, prefix=f"{config.API_PREFIX}/admin", tags=["Admin"])


# Include page routes at root level
app.include_router(page_router)

# Add error handlers
add_error_handlers(app)

# Add a redirect for the misaddressed CSS file
@app.get("/style.css")
async def redirect_to_css():
    """
    Redirect /style.css to /static/style.css
    """
    logger.info("Redirecting from /style.css to /static/style.css")
    return RedirectResponse(url="/static/style.css")

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
    
    logger.info(f"Kryptopedia is running in {'production' if not config.API_DEBUG else 'development'} mode")
    logger.info(f"Templates directory: {config.TEMPLATES_DIR}")
    logger.info(f"Static files: /static -> {os.path.abspath('static')}")
    if config.STORAGE_TYPE == "local":
        logger.info(f"Media files: /media -> {os.path.abspath(config.MEDIA_FOLDER)}")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """
    Clean up resources on application shutdown.
    """
    # Close database connection
    await db_service.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=config.API_DEBUG)
