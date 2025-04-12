"""
Main entry point for the Kryptopedia application.
Uses a properly structured approach with separated modules.
"""
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import config
from services.database import Database

# First, initialize the template engine (this registers all filters)
from template_engine import templates

# Now, import the routes (they will use the already initialized template engine)
# Import the template routes using a different name to avoid confusion
# Note that we're using template_routes instead of templates to avoid naming confusion
from routes.template_routes import router as template_router
# Import other API routes as needed
from routes import auth, articles, media, proposals, rewards, special

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

# Include template routes at root level
app.include_router(template_router)

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
