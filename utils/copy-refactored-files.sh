#!/bin/bash
# copy-refactored-files.sh
# This script copies all the refactored files to their correct locations

# Set colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== Kryptopedia - Copy Refactored Files ===${NC}"
echo -e "${YELLOW}This script will copy all the refactored code files to their correct locations.${NC}"

# Check if the directory structure exists
if [ ! -d "models" ] || [ ! -d "routes" ] || [ ! -d "services" ]; then
    echo -e "${RED}Directory structure not found. Please run setup-directory-structure.sh first.${NC}"
    exit 1
fi

# Copy config.py
echo -e "${GREEN}Copying config.py...${NC}"
cat > config.py << 'EOL'
"""
Configuration settings for the Kryptopedia application.
Loads environment variables and provides configuration for various components.
"""
import os
from dotenv import load_dotenv
from typing import Optional

# Load environment variables from .env file
load_dotenv()

# Database settings
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "kryptopedia")

# JWT settings
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-this-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))

# Storage settings
STORAGE_TYPE = os.getenv("STORAGE_TYPE", "local").lower()  # Options: "local" or "s3"
MEDIA_FOLDER = os.getenv("MEDIA_FOLDER", "media")

# S3 settings (only used if STORAGE_TYPE is "s3")
S3_BUCKET = os.getenv("S3_BUCKET", "kryptopedia-media")
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY", "")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY", "")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

# Elasticsearch settings
USE_ELASTICSEARCH = os.getenv("USE_ELASTICSEARCH", "False").lower() == "true"
ES_HOST = os.getenv("ES_HOST", "http://localhost:9200") if USE_ELASTICSEARCH else None

# Redis settings
USE_REDIS = os.getenv("USE_REDIS", "False").lower() == "true"
REDIS_HOST = os.getenv("REDIS_HOST", "localhost") if USE_REDIS else None
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379")) if USE_REDIS else None

# Template directory
TEMPLATES_DIR = os.getenv("TEMPLATES_DIR", "templates")

# API settings
API_PREFIX = os.getenv("API_PREFIX", "/api")
API_DEBUG = os.getenv("API_DEBUG", "True").lower() == "true"

# CORS settings
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

def get_settings():
    """Return a dictionary of all settings for easy access"""
    return {
        "mongo_uri": MONGO_URI,
        "db_name": DB_NAME,
        "jwt_secret": JWT_SECRET,
        "jwt_algorithm": JWT_ALGORITHM,
        "jwt_expiration_hours": JWT_EXPIRATION_HOURS,
        "storage_type": STORAGE_TYPE,
        "media_folder": MEDIA_FOLDER,
        "s3_bucket": S3_BUCKET,
        "aws_access_key": AWS_ACCESS_KEY,
        "aws_secret_key": AWS_SECRET_KEY,
        "aws_region": AWS_REGION,
        "use_elasticsearch": USE_ELASTICSEARCH,
        "es_host": ES_HOST,
        "use_redis": USE_REDIS,
        "redis_host": REDIS_HOST,
        "redis_port": REDIS_PORT,
        "templates_dir": TEMPLATES_DIR,
        "api_prefix": API_PREFIX,
        "api_debug": API_DEBUG,
        "cors_origins": CORS_ORIGINS,
    }

def check_dependencies():
    """Check if all required dependencies are available"""
    dependencies = {
        "elasticsearch": False,
        "redis": False,
        "boto3": False,
        "aiofiles": False
    }
    
    try:
        import elasticsearch
        dependencies["elasticsearch"] = True
    except ImportError:
        pass
    
    try:
        import redis
        dependencies["redis"] = True
    except ImportError:
        pass
    
    try:
        import boto3
        dependencies["boto3"] = True
    except ImportError:
        pass
    
    try:
        import aiofiles
        dependencies["aiofiles"] = True
    except ImportError:
        pass
    
    return dependencies
EOL

# Copy main.py
echo -e "${GREEN}Copying main.py...${NC}"
cat > main.py << 'EOL'
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
EOL

# Copy models/base.py
echo -e "${GREEN}Copying models/base.py...${NC}"
cat > models/base.py << 'EOL'
"""
Base models and shared data types for the Kryptopedia application.
"""
from bson import ObjectId
from pydantic import BaseModel, Field, validator
from typing import Dict, Any, Optional

class PyObjectId(ObjectId):
    """
    Custom type for handling MongoDB ObjectIDs with Pydantic
    """
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")

class DBModel(BaseModel):
    """
    Base model for all database models.
    Includes common fields and configuration for MongoDB documents.
    """
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str
        }

class DateTimeModelMixin(BaseModel):
    """
    Mixin for models that include created/updated timestamps
    """
    created_at: Optional[Any] = None
    updated_at: Optional[Any] = None

class StatusModelMixin(BaseModel):
    """
    Mixin for models that include a status field
    """
    status: str = "active"

class MetadataModelMixin(BaseModel):
    """
    Mixin for models that include a metadata dictionary
    """
    metadata: Dict[str, Any] = Field(default_factory=dict)
EOL

echo -e "${GREEN}All core files have been copied!${NC}"
echo -e "${YELLOW}Now you can copy the rest of the refactored files to their respective directories.${NC}"
echo -e "${YELLOW}Once done, run: python setup-data.py${NC}"
