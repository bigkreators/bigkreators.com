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
# Extended session duration - now defaults to 30 days like Wikipedia
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "720"))  # 720 hours = 30 days

# Option for shorter sessions if desired
JWT_SHORT_EXPIRATION_HOURS = int(os.getenv("JWT_SHORT_EXPIRATION_HOURS", "24"))  # 24 hours = 1 day

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
        "jwt_short_expiration_hours": JWT_SHORT_EXPIRATION_HOURS,
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

# Modern Solana and Token Configuration (v0.36.7)
SOLANA_RPC_URL = os.getenv("SOLANA_RPC_URL", "https://api.devnet.solana.com")
SOLANA_PRIVATE_KEY = os.getenv("SOLANA_PRIVATE_KEY", "")
TOKEN_MINT_ADDRESS = os.getenv("TOKEN_MINT_ADDRESS", "")

# Token system configuration
WEEKLY_TOKEN_POOL = float(os.getenv("WEEKLY_TOKEN_POOL", "10000.0"))
MIN_TOKENS_PER_USER = float(os.getenv("MIN_TOKENS_PER_USER", "1.0"))
