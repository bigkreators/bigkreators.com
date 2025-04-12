# File: config.py
"""
Configuration settings for the Kryptopedia application.
Loads environment variables and provides configuration for various components.
"""
import os
from dotenv import load_dotenv
from typing import Optional, List

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

# Template directory and settings
TEMPLATES_DIR = os.getenv("TEMPLATES_DIR", "templates")
TEMPLATES_AUTO_RELOAD = os.getenv("TEMPLATES_AUTO_RELOAD", "True").lower() == "true"
TEMPLATES_CACHE_SIZE = int(os.getenv("TEMPLATES_CACHE_SIZE", "300"))

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
        "templates_auto_reload": TEMPLATES_AUTO_RELOAD,
        "templates_cache_size": TEMPLATES_CACHE_SIZE,
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
