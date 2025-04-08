@app.get("/api/media/{id}", response_model=Media)
async def get_media(
    id: str,
    db=Depends(get_mongo_db)
):
    # Check if media exists
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid media ID")
    
    media = await db["media"].find_one({"_id": ObjectId(id)})
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")
    
    return media# main.py
from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING, TEXT
from bson import ObjectId
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, timedelta
import jwt
import bcrypt
import os
import shutil
from dotenv import load_dotenv
import hashlib
import uuid
from elasticsearch import AsyncElasticsearch
import redis.asyncio as redis
import aiofiles

# Import boto3 for S3 storage option
try:
    import boto3
    S3_AVAILABLE = True
except ImportError:
    S3_AVAILABLE = False

# Load environment variables
load_dotenv()

app = FastAPI(title="Cryptopedia API", description="API for Cryptopedia Wiki")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "cryptopedia")

# JWT Configuration
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION = 24  # hours

# Storage configuration
STORAGE_TYPE = os.getenv("STORAGE_TYPE", "local").lower()  # Options: "local" or "s3"

# Local file storage configuration
MEDIA_FOLDER = os.getenv("MEDIA_FOLDER", "media")
# Create media folder if it doesn't exist
os.makedirs(MEDIA_FOLDER, exist_ok=True)

# S3 Configuration (only used if STORAGE_TYPE is "s3")
S3_BUCKET = os.getenv("S3_BUCKET", "cryptopedia-media")
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY", "")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY", "")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

# Optional Elasticsearch Configuration (with fallback to simple search)
USE_ELASTICSEARCH = os.getenv("USE_ELASTICSEARCH", "False").lower() == "true"
ES_HOST = os.getenv("ES_HOST", "http://localhost:9200") if USE_ELASTICSEARCH else None

# Optional Redis Configuration (with in-memory cache fallback)
USE_REDIS = os.getenv("USE_REDIS", "False").lower() == "true"
REDIS_HOST = os.getenv("REDIS_HOST", "localhost") if USE_REDIS else None
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379")) if USE_REDIS else None

# Initialize OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

# MongoDB Models
class PyObjectId(ObjectId):
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

# Models
class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None

class User(UserBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    role: str = "user"
    joinDate: datetime = Field(default_factory=datetime.now)
    lastLogin: Optional[datetime] = None
    reputation: int = 0
    contributions: Dict[str, int] = Field(default_factory=lambda: {
        "articlesCreated": 0,
        "editsPerformed": 0,
        "rewardsReceived": 0
    })

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class ArticleBase(BaseModel):
    title: str
    content: str
    summary: str
    categories: List[str] = []
    tags: List[str] = []
    metadata: Dict[str, bool] = Field(default_factory=lambda: {
        "hasAudio": False,
        "hasSpecialSymbols": False,
        "containsMadeUpContent": False
    })

class ArticleCreate(ArticleBase):
    pass

class ArticleUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    summary: Optional[str] = None
    categories: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, bool]] = None

class Article(ArticleBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    slug: str
    createdBy: PyObjectId
    createdAt: datetime = Field(default_factory=datetime.now)
    lastUpdatedAt: Optional[datetime] = None
    lastUpdatedBy: Optional[PyObjectId] = None
    featuredUntil: Optional[datetime] = None
    status: str = "published"
    views: int = 0

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class RevisionCreate(BaseModel):
    content: str
    comment: str

class Revision(RevisionCreate):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    articleId: PyObjectId
    createdBy: PyObjectId
    createdAt: datetime = Field(default_factory=datetime.now)
    diff: Optional[str] = None

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class ProposalCreate(BaseModel):
    content: str
    summary: str

class Proposal(ProposalCreate):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    articleId: PyObjectId
    proposedBy: PyObjectId
    proposedAt: datetime = Field(default_factory=datetime.now)
    status: str = "pending"
    reviewedBy: Optional[PyObjectId] = None
    reviewedAt: Optional[datetime] = None
    reviewComment: Optional[str] = None

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class MediaCreate(BaseModel):
    filename: str
    originalName: str
    mimeType: str
    size: int
    path: str
    metadata: Dict[str, Any] = {}

class Media(MediaCreate):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    uploadedBy: PyObjectId
    uploadedAt: datetime = Field(default_factory=datetime.now)
    usedInArticles: List[PyObjectId] = []

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class RewardCreate(BaseModel):
    rewardType: str
    points: int

class Reward(RewardCreate):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    articleId: PyObjectId
    revisionId: Optional[PyObjectId] = None
    rewardedUser: PyObjectId
    rewardedBy: PyObjectId
    rewardedAt: datetime = Field(default_factory=datetime.now)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime

class TokenData(BaseModel):
    user_id: Optional[str] = None

# Database connections
async def get_mongo_db():
    client = AsyncIOMotorClient(MONGO_URI)
    try:
        yield client[DB_NAME]
    finally:
        client.close()

# Storage interface for file handling
class StorageInterface:
    """Abstract interface for file storage operations"""
    async def save_file(self, file_content: bytes, filename: str, content_type: str = None) -> str:
        """Save a file and return its path/URL"""
        pass
    
    async def get_file(self, filename: str) -> bytes:
        """Get a file's content"""
        pass
    
    async def delete_file(self, filename: str) -> bool:
        """Delete a file"""
        pass

class LocalStorage(StorageInterface):
    """Local file system storage implementation"""
    def __init__(self, media_folder: str):
        self.media_folder = media_folder
        os.makedirs(media_folder, exist_ok=True)
    
    async def save_file(self, file_content: bytes, filename: str, content_type: str = None) -> str:
        """Save a file to local storage and return its path"""
        file_path = os.path.join(self.media_folder, filename)
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(file_content)
        return f"/media/{filename}"  # Return relative URL path
    
    async def get_file(self, filename: str) -> bytes:
        """Get a file's content from local storage"""
        file_path = os.path.join(self.media_folder, filename)
        if not os.path.exists(file_path):
            return None
        async with aiofiles.open(file_path, "rb") as f:
            return await f.read()
    
    async def delete_file(self, filename: str) -> bool:
        """Delete a file from local storage"""
        file_path = os.path.join(self.media_folder, filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False

class S3Storage(StorageInterface):
    """Amazon S3 storage implementation"""
    def __init__(self, bucket: str, region: str, access_key: str = None, secret_key: str = None):
        self.bucket = bucket
        self.region = region
        
        # Initialize S3 client
        if access_key and secret_key:
            self.s3 = boto3.client(
                's3',
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name=region
            )
        else:
            # Use IAM role or environment variables
            self.s3 = boto3.client('s3', region_name=region)
    
    async def save_file(self, file_content: bytes, filename: str, content_type: str = None) -> str:
        """Save a file to S3 and return its URL"""
        try:
            self.s3.put_object(
                Bucket=self.bucket,
                Key=filename,
                Body=file_content,
                ContentType=content_type or 'application/octet-stream'
            )
            return f"https://{self.bucket}.s3.{self.region}.amazonaws.com/{filename}"
        except Exception as e:
            # Log error and re-raise
            print(f"S3 upload error: {str(e)}")
            raise
    
    async def get_file(self, filename: str) -> bytes:
        """Get a file's content from S3"""
        try:
            response = self.s3.get_object(
                Bucket=self.bucket,
                Key=filename
            )
            return response['Body'].read()
        except Exception as e:
            # Log error and return None
            print(f"S3 download error: {str(e)}")
            return None
    
    async def delete_file(self, filename: str) -> bool:
        """Delete a file from S3"""
        try:
            self.s3.delete_object(
                Bucket=self.bucket,
                Key=filename
            )
            return True
        except Exception as e:
            # Log error and return False
            print(f"S3 delete error: {str(e)}")
            return False

# Function to get the appropriate storage interface
def get_storage_interface() -> StorageInterface:
    """Get the configured storage interface based on environment settings"""
    if STORAGE_TYPE == "s3":
        if not S3_AVAILABLE:
            print("Warning: S3 storage requested but boto3 is not installed. Falling back to local storage.")
            return LocalStorage(MEDIA_FOLDER)
        
        # Check if S3 credentials are available
        if not (AWS_ACCESS_KEY and AWS_SECRET_KEY):
            print("Warning: S3 storage requested but credentials are not configured. Falling back to local storage.")
            return LocalStorage(MEDIA_FOLDER)
        
        return S3Storage(S3_BUCKET, AWS_REGION, AWS_ACCESS_KEY, AWS_SECRET_KEY)
    else:
        # Default to local storage
        return LocalStorage(MEDIA_FOLDER)

# Initialize storage
storage = get_storage_interface()

# Simple in-memory cache as Redis alternative
class InMemoryCache:
    """Simple in-memory cache as Redis alternative"""
    _cache = {}
    _expiry = {}
    
    async def get(self, key):
        """Get value from cache if not expired"""
        if key in self._cache:
            # Check if expired
            if key in self._expiry and self._expiry[key] < datetime.now():
                # Expired, remove and return None
                del self._cache[key]
                del self._expiry[key]
                return None
            return self._cache[key]
        return None
    
    async def set(self, key, value, ex=None):
        """Set value in cache with optional expiry in seconds"""
        self._cache[key] = value
        if ex:
            self._expiry[key] = datetime.now() + timedelta(seconds=ex)
    
    async def delete(self, key):
        """Delete key from cache"""
        if key in self._cache:
            del self._cache[key]
        if key in self._expiry:
            del self._expiry[key]
    
    async def close(self):
        """No need to close in-memory cache"""
        pass

# Simple search class as Elasticsearch alternative
class SimpleSearch:
    """Simple search class for when Elasticsearch is not available"""
    def __init__(self):
        self.db = None
    
    async def set_db(self, db):
        """Set database reference"""
        self.db = db
    
    async def index(self, index, id, document=None, doc=None):
        """Stub for elasticsearch index method (no-op in simple search)"""
        pass
    
    async def update(self, index, id, doc=None):
        """Stub for elasticsearch update method (no-op in simple search)"""
        pass
    
    async def delete(self, index, id):
        """Stub for elasticsearch delete method (no-op in simple search)"""
        pass
    
    async def search(self, index, body):
        """Simple search implementation using MongoDB text search"""
        if not self.db:
            return {"hits": {"hits": []}}
        
        query = body.get("query", {}).get("multi_match", {}).get("query", "")
        from_val = body.get("from", 0)
        size = body.get("size", 10)
        
        # Use MongoDB text search
        results = await self.db["articles"].find(
            {"$text": {"$search": query}, "status": "published"},
            {"score": {"$meta": "textScore"}}
        ).sort([("score", {"$meta": "textScore"})]).skip(from_val).limit(size).to_list(length=size)
        
        # Convert to elasticsearch-like response format
        hits = []
        for doc in results:
            hits.append({
                "_id": str(doc["_id"]),
                "_source": doc
            })
        
        return {"hits": {"hits": hits}}
    
    async def close(self):
        """No need to close simple search"""
        pass

# Elasticsearch connection (with fallback to simple search)
async def get_elasticsearch(db=Depends(get_mongo_db)):
    if USE_ELASTICSEARCH:
        es = AsyncElasticsearch(ES_HOST)
        try:
            yield es
        finally:
            await es.close()
    else:
        # Use simple search
        simple_search = SimpleSearch()
        await simple_search.set_db(db)
        try:
            yield simple_search
        finally:
            await simple_search.close()

# Redis connection (with fallback to in-memory cache)
async def get_redis():
    if USE_REDIS:
        r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
        try:
            yield r
        finally:
            await r.close()
    else:
        # Use in-memory cache
        cache = InMemoryCache()
        try:
            yield cache
        finally:
            await cache.close()

# Authentication functions
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt, expire

async def get_current_user(token: str = Depends(oauth2_scheme), db=Depends(get_mongo_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        token_data = TokenData(user_id=user_id)
    except jwt.PyJWTError:
        raise credentials_exception
    
    user = await db["users"].find_one({"_id": ObjectId(token_data.user_id)})
    if user is None:
        raise credentials_exception
    return user

# Slug generator
def generate_slug(title: str):
    # Convert to lowercase and replace spaces with hyphens
    slug = title.lower().replace(" ", "-")
    # Remove special characters
    slug = "".join(c for c in slug if c.isalnum() or c == "-")
    # Add timestamp to ensure uniqueness
    slug = f"{slug}-{int(datetime.now().timestamp())}"
    return slug

# Mount static file directory for media files (only if using local storage)
if STORAGE_TYPE == "local":
    app.mount("/media", StaticFiles(directory=MEDIA_FOLDER), name="media")

# Startup event
@app.on_event("startup")
async def startup_db_client():
    app.mongodb_client = AsyncIOMotorClient(MONGO_URI)
    app.mongodb = app.mongodb_client[DB_NAME]
    
    # Create indices
    await app.mongodb["articles"].create_index([("title", TEXT), ("content", TEXT), ("summary", TEXT)])
    await app.mongodb["articles"].create_index([("slug", ASCENDING)], unique=True)
    await app.mongodb["users"].create_index([("username", ASCENDING)], unique=True)
    await app.mongodb["users"].create_index([("email", ASCENDING)], unique=True)
    
    # Create directories if they don't exist
    os.makedirs(MEDIA_FOLDER, exist_ok=True)
    os.makedirs("static", exist_ok=True)
    os.makedirs("templates", exist_ok=True)

# Shutdown event
@app.on_event("shutdown")
async def shutdown_db_client():
    app.mongodb_client.close()

# Routes
@app.get("/", response_class=templates.TemplateResponse)
async def root(request: Request, db=Depends(get_mongo_db), redis_client=Depends(get_redis)):
    """Main page - renders the wiki homepage"""
    # Get featured article
    featured_article = None
    try:
        # Try to get from cache
        cached = await redis_client.get("featured_article")
        if cached:
            featured_article = eval(cached)
        else:
            # Get a featured article that's still featured (featuredUntil > now)
            featured_article = await db["articles"].find_one({
                "featuredUntil": {"$gt": datetime.now()},
                "status": "published"
            })
            
            # If no article is currently featured, get the most viewed article
            if not featured_article:
                featured_article = await db["articles"].find_one(
                    {"status": "published"},
                    sort=[("views", -1)]
                )
            
            # Cache for 1 hour if found
            if featured_article:
                await redis_client.set("featured_article", str(featured_article), ex=3600)
    except Exception as e:
        print(f"Error getting featured article: {str(e)}")
    
    # Get recent articles
    recent_articles = []
    try:
        cursor = db["articles"].find({"status": "published"}).sort("createdAt", -1).limit(3)
        recent_articles = await cursor.to_list(length=3)
    except Exception as e:
        print(f"Error getting recent articles: {str(e)}")
    
    # Return template with data
    return templates.TemplateResponse(
        "index.html", 
        {
            "request": request,
            "featured_article": featured_article,
            "recent_articles": recent_articles
        }
    )

@app.get("/api")
async def api_root():
    return {"message": "Welcome to the Cryptopedia API"}

# Auth Routes
@app.post("/api/auth/register", response_model=User)
async def register(user: UserCreate, db=Depends(get_mongo_db)):
    # Check if username or email already exists
    if await db["users"].find_one({"username": user.username}):
        raise HTTPException(status_code=400, detail="Username already registered")
    if await db["users"].find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash the password
    hashed_password = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt())
    
    user_dict = {
        "username": user.username,
        "email": user.email,
        "passwordHash": hashed_password.decode('utf-8'),
        "role": "user",
        "joinDate": datetime.now(),
        "reputation": 0,
        "contributions": {
            "articlesCreated": 0,
            "editsPerformed": 0,
            "rewardsReceived": 0
        }
    }
    
    result = await db["users"].insert_one(user_dict)
    
    # Return the created user
    created_user = await db["users"].find_one({"_id": result.inserted_id})
    return created_user

@app.post("/api/auth/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db=Depends(get_mongo_db)):
    user = await db["users"].find_one({"username": form_data.username})
    
    if not user:
        user = await db["users"].find_one({"email": form_data.username})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    # Verify password
    if not bcrypt.checkpw(form_data.password.encode('utf-8'), user["passwordHash"].encode('utf-8')):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Update last login
    await db["users"].update_one(
        {"_id": user["_id"]},
        {"$set": {"lastLogin": datetime.now()}}
    )
    
    # Create access token
    access_token, expires_at = create_access_token(data={"sub": str(user["_id"])})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_at": expires_at
    }

@app.get("/api/auth/me", response_model=User)
async def get_me(current_user: dict = Depends(get_current_user)):
    return current_user

@app.put("/api/auth/me", response_model=User)
async def update_me(
    user_update: UserUpdate,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_mongo_db)
):
    # Create update dict
    update_data = {}
    
    if user_update.username:
        # Check if username already exists for another user
        existing = await db["users"].find_one({"username": user_update.username})
        if existing and str(existing["_id"]) != str(current_user["_id"]):
            raise HTTPException(status_code=400, detail="Username already taken")
        update_data["username"] = user_update.username
    
    if user_update.email:
        # Check if email already exists for another user
        existing = await db["users"].find_one({"email": user_update.email})
        if existing and str(existing["_id"]) != str(current_user["_id"]):
            raise HTTPException(status_code=400, detail="Email already registered")
        update_data["email"] = user_update.email
    
    if user_update.password:
        # Hash the new password
        hashed_password = bcrypt.hashpw(user_update.password.encode('utf-8'), bcrypt.gensalt())
        update_data["passwordHash"] = hashed_password.decode('utf-8')
    
    if update_data:
        await db["users"].update_one(
            {"_id": current_user["_id"]},
            {"$set": update_data}
        )
    
    # Return updated user
    updated_user = await db["users"].find_one({"_id": current_user["_id"]})
    return updated_user

# Article Routes
@app.get("/api/articles", response_model=List[Article])
async def get_articles(
    skip: int = 0,
    limit: int = 10,
    category: Optional[str] = None,
    tag: Optional[str] = None,
    db=Depends(get_mongo_db),
    redis_client=Depends(get_redis)
):
    # Create cache key based on parameters
    cache_key = f"articles:{skip}:{limit}:{category}:{tag}"
    
    # Try to get from cache
    cached = await redis_client.get(cache_key)
    if cached:
        return eval(cached)
    
    # Build query
    query = {"status": "published"}
    if category:
        query["categories"] = category
    if tag:
        query["tags"] = tag
    
    # Execute query
    cursor = db["articles"].find(query).skip(skip).limit(limit).sort("createdAt", -1)
    articles = await cursor.to_list(length=limit)
    
    # Cache results for 5 minutes
    await redis_client.set(cache_key, str(articles), ex=300)
    
    return articles

@app.get("/api/articles/featured", response_model=Article)
async def get_featured_article(db=Depends(get_mongo_db), redis_client=Depends(get_redis)):
    # Try to get from cache
    cached = await redis_client.get("featured_article")
    if cached:
        return eval(cached)
    
    # Get proposals
    cursor = db["proposals"].find(query).sort("proposedAt", -1).skip(skip).limit(limit)
    proposals = await cursor.to_list(length=limit)
    
    return proposals

@app.put("/api/articles/{id}/proposals/{prop_id}", response_model=Proposal)
async def review_proposal(
    id: str,
    prop_id: str,
    status: str = Query(..., regex="^(approved|rejected)$"),
    comment: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_mongo_db),
    es=Depends(get_elasticsearch),
    redis_client=Depends(get_redis)
):
    # Check if IDs are valid
    if not ObjectId.is_valid(id) or not ObjectId.is_valid(prop_id):
        raise HTTPException(status_code=400, detail="Invalid ID format")
    
    # Check if user is admin or editor
    if current_user["role"] not in ["admin", "editor"]:
        raise HTTPException(status_code=403, detail="Not authorized to review proposals")
    
    # Get proposal
    proposal = await db["proposals"].find_one({
        "_id": ObjectId(prop_id),
        "articleId": ObjectId(id)
    })
    
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    
    # Update proposal status
    await db["proposals"].update_one(
        {"_id": ObjectId(prop_id)},
        {"$set": {
            "status": status,
            "reviewedBy": current_user["_id"],
            "reviewedAt": datetime.now(),
            "reviewComment": comment
        }}
    )
    
    # If approved, update the article
    if status == "approved":
        article = await db["articles"].find_one({"_id": ObjectId(id)})
        
        await db["articles"].update_one(
            {"_id": ObjectId(id)},
            {"$set": {
                "content": proposal["content"],
                "lastUpdatedAt": datetime.now(),
                "lastUpdatedBy": proposal["proposedBy"]
            }}
        )
        
        # Create a revision
        revision = {
            "articleId": ObjectId(id),
            "content": proposal["content"],
            "createdBy": proposal["proposedBy"],
            "createdAt": datetime.now(),
            "comment": proposal["summary"]
        }
        
        await db["revisions"].insert_one(revision)
        
        # Update Elasticsearch
        await es.update(
            index="articles",
            id=id,
            doc={
                "content": proposal["content"],
                "updated": datetime.now().isoformat()
            }
        )
        
        # Invalidate cache
        await redis_client.delete(f"article:{id}")
        
        # Update user's contribution count
        await db["users"].update_one(
            {"_id": proposal["proposedBy"]},
            {"$inc": {"contributions.editsPerformed": 1}}
        )
    
    # Return updated proposal
    updated_proposal = await db["proposals"].find_one({"_id": ObjectId(prop_id)})
    return updated_proposal

# Reward Routes
@app.post("/api/articles/{id}/rewards", response_model=Reward)
async def create_reward(
    id: str,
    revision_id: Optional[str] = None,
    reward: RewardCreate = Depends(),
    current_user: dict = Depends(get_current_user),
    db=Depends(get_mongo_db)
):
    # Check if article exists
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid article ID")
    
    article = await db["articles"].find_one({"_id": ObjectId(id)})
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    # Check if revision exists if provided
    revision_obj_id = None
    if revision_id:
        if not ObjectId.is_valid(revision_id):
            raise HTTPException(status_code=400, detail="Invalid revision ID")
        
        revision = await db["revisions"].find_one({
            "_id": ObjectId(revision_id),
            "articleId": ObjectId(id)
        })
        
        if not revision:
            raise HTTPException(status_code=404, detail="Revision not found")
        
        revision_obj_id = ObjectId(revision_id)
        rewarded_user_id = revision["createdBy"]
    else:
        # Reward goes to article creator
        rewarded_user_id = article["createdBy"]
    
    # Don't allow self-rewarding
    if str(rewarded_user_id) == str(current_user["_id"]):
        raise HTTPException(status_code=400, detail="Cannot reward your own content")
    
    # Validate reward type
    valid_reward_types = ["helpful", "insightful", "comprehensive"]
    if reward.rewardType not in valid_reward_types:
        raise HTTPException(status_code=400, detail=f"Invalid reward type. Must be one of: {', '.join(valid_reward_types)}")
    
    # Create reward
    new_reward = {
        "articleId": ObjectId(id),
        "revisionId": revision_obj_id,
        "rewardedUser": rewarded_user_id,
        "rewardedBy": current_user["_id"],
        "rewardedAt": datetime.now(),
        "rewardType": reward.rewardType,
        "points": reward.points
    }
    
    result = await db["rewards"].insert_one(new_reward)
    
    # Update user's reputation and rewards count
    await db["users"].update_one(
        {"_id": rewarded_user_id},
        {"$inc": {
            "reputation": reward.points,
            "contributions.rewardsReceived": 1
        }}
    )
    
    # Return created reward
    created_reward = await db["rewards"].find_one({"_id": result.inserted_id})
    return created_reward

# Media Routes
@app.post("/api/media/upload", response_model=Media)
async def upload_media(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db=Depends(get_mongo_db)
):
    # Generate unique filename
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    
    # Save file using storage interface
    try:
        file_content = await file.read()
        file_url = await storage.save_file(file_content, unique_filename, file.content_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")
    
    # Create metadata based on file type
    metadata = {}
    
    # For audio files
    if file.content_type.startswith("audio/"):
        # This would require additional libraries to extract duration
        metadata = {"duration": 0}  # Placeholder
    
    # For image files
    elif file.content_type.startswith("image/"):
        # This would require additional libraries to extract dimensions
        metadata = {"dimensions": {"width": 0, "height": 0}}  # Placeholder
    
    # Create media entry
    new_media = {
        "filename": unique_filename,
        "originalName": file.filename,
        "mimeType": file.content_type,
        "size": len(file_content),
        "path": file_url,
        "uploadedBy": current_user["_id"],
        "uploadedAt": datetime.now(),
        "metadata": metadata,
        "usedInArticles": []
    }
    
    result = await db["media"].insert_one(new_media)
    
    # Return created media
    created_media = await db["media"].find_one({"_id": result.inserted_id})
    return created_media

@app.get("/api/media/{filename}/content")
async def get_media_content(
    filename: str,
    db=Depends(get_mongo_db)
):
    """Get media file content directly (useful for S3 stored files)"""
    # Verify the file exists in the database
    media = await db["media"].find_one({"filename": filename})
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")
    
    # Get file content from storage
    content = await storage.get_file(filename)
    if not content:
        raise HTTPException(status_code=404, detail="File content not found")
    
    # Determine content type
    content_type = media.get("mimeType", "application/octet-stream")
    
    # Return file content with proper content type
    from fastapi.responses import Response
    return Response(content=content, media_type=content_type)

# Special Pages
@app.get("/api/special/recentchanges", response_model=List[Dict])
async def get_recent_changes(
    skip: int = 0,
    limit: int = 20,
    db=Depends(get_mongo_db),
    redis_client=Depends(get_redis)
):
    # Try to get from cache
    cache_key = f"recentchanges:{skip}:{limit}"
    cached = await redis_client.get(cache_key)
    if cached:
        return eval(cached)
    
    # Get recent revisions
    rev_cursor = db["revisions"].find().sort("createdAt", -1).skip(skip).limit(limit)
    revisions = await rev_cursor.to_list(length=limit)
    
    # Enhance with article info
    result = []
    for rev in revisions:
        article = await db["articles"].find_one({"_id": rev["articleId"]})
        user = await db["users"].find_one({"_id": rev["createdBy"]})
        
        if article and user:
            result.append({
                "type": "revision",
                "id": str(rev["_id"]),
                "timestamp": rev["createdAt"],
                "articleId": str(rev["articleId"]),
                "articleTitle": article.get("title", "Unknown"),
                "userId": str(rev["createdBy"]),
                "username": user.get("username", "Unknown"),
                "comment": rev.get("comment", "")
            })
    
    # Cache results for 5 minutes
    await redis_client.set(cache_key, str(result), ex=300)
    
    return result

@app.get("/api/special/statistics")
async def get_statistics(
    db=Depends(get_mongo_db),
    redis_client=Depends(get_redis)
):
    # Try to get from cache
    cached = await redis_client.get("statistics")
    if cached:
        return eval(cached)
    
    # Get statistics
    articles_count = await db["articles"].count_documents({"status": "published"})
    users_count = await db["users"].count_documents({})
    revisions_count = await db["revisions"].count_documents({})
    
    # Most viewed article
    most_viewed = await db["articles"].find_one(
        {"status": "published"},
        sort=[("views", -1)]
    )
    
    # Most active user (by edits)
    most_active = await db["users"].find_one(
        sort=[("contributions.editsPerformed", -1)]
    )
    
    # Recent activity (last 24 hours)
    yesterday = datetime.now() - timedelta(days=1)
    recent_revisions = await db["revisions"].count_documents({"createdAt": {"$gte": yesterday}})
    recent_proposals = await db["proposals"].count_documents({"proposedAt": {"$gte": yesterday}})
    
    statistics = {
        "articles": articles_count,
        "users": users_count,
        "revisions": revisions_count,
        "mostViewedArticle": {
            "id": str(most_viewed["_id"]) if most_viewed else None,
            "title": most_viewed.get("title") if most_viewed else None,
            "views": most_viewed.get("views") if most_viewed else 0
        },
        "mostActiveUser": {
            "id": str(most_active["_id"]) if most_active else None,
            "username": most_active.get("username") if most_active else None,
            "edits": most_active.get("contributions", {}).get("editsPerformed", 0) if most_active else 0
        },
        "recentActivity": {
            "revisions": recent_revisions,
            "proposals": recent_proposals,
            "total": recent_revisions + recent_proposals
        }
    }
    
    # Cache for 1 hour
    await redis_client.set("statistics", str(statistics), ex=3600)
    
    return statistics

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) a featured article that's still featured (featuredUntil > now)
    article = await db["articles"].find_one({
        "featuredUntil": {"$gt": datetime.now()},
        "status": "published"
    })
    
    # If no article is currently featured, get the most viewed article
    if not article:
        article = await db["articles"].find_one(
            {"status": "published"},
            sort=[("views", -1)]
        )
    
    if not article:
        raise HTTPException(status_code=404, detail="No articles found")
    
    # Cache for 1 hour
    await redis_client.set("featured_article", str(article), ex=3600)
    
    return article

@app.get("/api/articles/random", response_model=Article)
async def get_random_article(db=Depends(get_mongo_db)):
    # Get a random article using MongoDB's aggregation framework
    pipeline = [
        {"$match": {"status": "published"}},
        {"$sample": {"size": 1}}
    ]
    
    result = await db["articles"].aggregate(pipeline).to_list(length=1)
    
    if not result:
        raise HTTPException(status_code=404, detail="No articles found")
    
    return result[0]

@app.get("/api/articles/{id}", response_model=Article)
async def get_article(
    id: str,
    db=Depends(get_mongo_db),
    redis_client=Depends(get_redis)
):
    # Try to get from cache
    cached = await redis_client.get(f"article:{id}")
    if cached:
        # Increment view count in background
        await db["articles"].update_one(
            {"_id": ObjectId(id)},
            {"$inc": {"views": 1}}
        )
        return eval(cached)
    
    # Check if ID is valid
    if not ObjectId.is_valid(id):
        # Try to find by slug instead
        article = await db["articles"].find_one({"slug": id})
    else:
        # Find by ID
        article = await db["articles"].find_one({"_id": ObjectId(id)})
    
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    # Increment view count
    await db["articles"].update_one(
        {"_id": article["_id"]},
        {"$inc": {"views": 1}}
    )
    
    # Cache for 5 minutes
    await redis_client.set(f"article:{id}", str(article), ex=300)
    
    return article

@app.post("/api/articles", response_model=Article)
async def create_article(
    article: ArticleCreate,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_mongo_db),
    es=Depends(get_elasticsearch)
):
    # Generate slug from title
    slug = generate_slug(article.title)
    
    # Create article object
    new_article = {
        "title": article.title,
        "slug": slug,
        "content": article.content,
        "summary": article.summary,
        "createdBy": current_user["_id"],
        "createdAt": datetime.now(),
        "status": "published",
        "categories": article.categories,
        "tags": article.tags,
        "views": 0,
        "metadata": article.metadata
    }
    
    # Insert into database
    result = await db["articles"].insert_one(new_article)
    
    # Update user's contribution count
    await db["users"].update_one(
        {"_id": current_user["_id"]},
        {"$inc": {"contributions.articlesCreated": 1}}
    )
    
    # Index in Elasticsearch for search
    await es.index(
        index="articles",
        id=str(result.inserted_id),
        document={
            "title": article.title,
            "content": article.content,
            "summary": article.summary,
            "categories": article.categories,
            "tags": article.tags,
            "author": current_user["username"],
            "created": datetime.now().isoformat()
        }
    )
    
    # Return the created article
    created_article = await db["articles"].find_one({"_id": result.inserted_id})
    return created_article

@app.put("/api/articles/{id}", response_model=Article)
async def update_article(
    id: str,
    article_update: ArticleUpdate,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_mongo_db),
    es=Depends(get_elasticsearch),
    redis_client=Depends(get_redis)
):
    # Check if article exists
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid article ID")
    
    article = await db["articles"].find_one({"_id": ObjectId(id)})
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    # Check if user is authorized (admin or original creator)
    if str(article["createdBy"]) != str(current_user["_id"]) and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to edit this article")
    
    # Create update object
    update_data = {}
    
    # Only update fields that were provided
    if article_update.title:
        update_data["title"] = article_update.title
        # Generate new slug if title changes
        update_data["slug"] = generate_slug(article_update.title)
    
    if article_update.content:
        update_data["content"] = article_update.content
    
    if article_update.summary:
        update_data["summary"] = article_update.summary
    
    if article_update.categories:
        update_data["categories"] = article_update.categories
    
    if article_update.tags:
        update_data["tags"] = article_update.tags
    
    if article_update.metadata:
        update_data["metadata"] = article_update.metadata
    
    # Add update metadata
    update_data["lastUpdatedAt"] = datetime.now()
    update_data["lastUpdatedBy"] = current_user["_id"]
    
    # Update article
    if update_data:
        await db["articles"].update_one(
            {"_id": ObjectId(id)},
            {"$set": update_data}
        )
        
        # Create a revision
        revision = {
            "articleId": ObjectId(id),
            "content": article_update.content or article["content"],
            "createdBy": current_user["_id"],
            "createdAt": datetime.now(),
            "comment": "Article updated"  # Could be taken from request if needed
        }
        
        await db["revisions"].insert_one(revision)
        
        # Update user's contribution count
        await db["users"].update_one(
            {"_id": current_user["_id"]},
            {"$inc": {"contributions.editsPerformed": 1}}
        )
        
        # Update in Elasticsearch
        await es.update(
            index="articles",
            id=id,
            doc={
                "title": article_update.title or article["title"],
                "content": article_update.content or article["content"],
                "summary": article_update.summary or article["summary"],
                "categories": article_update.categories or article["categories"],
                "tags": article_update.tags or article["tags"],
                "updated": datetime.now().isoformat()
            }
        )
        
        # Invalidate cache
        await redis_client.delete(f"article:{id}")
    
    # Return updated article
    updated_article = await db["articles"].find_one({"_id": ObjectId(id)})
    return updated_article

@app.delete("/api/articles/{id}")
async def delete_article(
    id: str,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_mongo_db),
    es=Depends(get_elasticsearch),
    redis_client=Depends(get_redis)
):
    # Check if article exists
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid article ID")
    
    article = await db["articles"].find_one({"_id": ObjectId(id)})
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    # Only admins can delete articles
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admins can delete articles")
    
    # Delete the article (or mark as archived)
    await db["articles"].update_one(
        {"_id": ObjectId(id)},
        {"$set": {"status": "archived"}}
    )
    
    # Delete from Elasticsearch
    await es.delete(index="articles", id=id)
    
    # Invalidate cache
    await redis_client.delete(f"article:{id}")
    
    return {"message": "Article archived successfully"}

@app.get("/api/articles/{id}/history", response_model=List[Revision])
async def get_article_history(
    id: str,
    skip: int = 0,
    limit: int = 10,
    db=Depends(get_mongo_db)
):
    # Check if article exists
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid article ID")
    
    article = await db["articles"].find_one({"_id": ObjectId(id)})
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    # Get revisions
    cursor = db["revisions"].find({"articleId": ObjectId(id)}).sort("createdAt", -1).skip(skip).limit(limit)
    revisions = await cursor.to_list(length=limit)
    
    return revisions

@app.get("/api/articles/{id}/revisions/{rev_id}", response_model=Revision)
async def get_article_revision(
    id: str,
    rev_id: str,
    db=Depends(get_mongo_db)
):
    # Check if IDs are valid
    if not ObjectId.is_valid(id) or not ObjectId.is_valid(rev_id):
        raise HTTPException(status_code=400, detail="Invalid ID format")
    
    # Get revision
    revision = await db["revisions"].find_one({
        "_id": ObjectId(rev_id),
        "articleId": ObjectId(id)
    })
    
    if not revision:
        raise HTTPException(status_code=404, detail="Revision not found")
    
    return revision

# Search API
@app.get("/api/search", response_model=List[Article])
async def search(
    q: str = Query(..., min_length=1),
    skip: int = 0,
    limit: int = 10,
    es=Depends(get_elasticsearch),
    db=Depends(get_mongo_db)
):
    # Search in Elasticsearch
    results = await es.search(
        index="articles",
        body={
            "from": skip,
            "size": limit,
            "query": {
                "multi_match": {
                    "query": q,
                    "fields": ["title^3", "content", "summary^2", "categories", "tags"]
                }
            },
            "highlight": {
                "fields": {
                    "title": {},
                    "content": {},
                    "summary": {}
                }
            }
        }
    )
    
    # Get article IDs from search results
    article_ids = [ObjectId(hit["_id"]) for hit in results["hits"]["hits"]]
    
    # Get full articles from MongoDB
    articles = []
    if article_ids:
        articles = await db["articles"].find({"_id": {"$in": article_ids}}).to_list(length=limit)
        
        # Sort articles to match search results order
        id_to_pos = {str(hit["_id"]): i for i, hit in enumerate(results["hits"]["hits"])}
        articles.sort(key=lambda x: id_to_pos.get(str(x["_id"]), 999))
    
    return articles

# Proposal Routes
@app.post("/api/articles/{id}/proposals", response_model=Proposal)
async def create_proposal(
    id: str,
    proposal: ProposalCreate,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_mongo_db)
):
    # Check if article exists
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid article ID")
    
    article = await db["articles"].find_one({"_id": ObjectId(id)})
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    # Create proposal
    new_proposal = {
        "articleId": ObjectId(id),
        "proposedBy": current_user["_id"],
        "proposedAt": datetime.now(),
        "content": proposal.content,
        "summary": proposal.summary,
        "status": "pending"
    }
    
    result = await db["proposals"].insert_one(new_proposal)
    
    # Return created proposal
    created_proposal = await db["proposals"].find_one({"_id": result.inserted_id})
    return created_proposal

@app.get("/api/articles/{id}/proposals", response_model=List[Proposal])
async def get_proposals(
    id: str,
    skip: int = 0,
    limit: int = 10,
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_mongo_db)
):
    # Check if article exists
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid article ID")
    
    article = await db["articles"].find_one({"_id": ObjectId(id)})
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    # Build query
    query = {"articleId": ObjectId(id)}
    if status:
        query["status"] = status
    
    # Get