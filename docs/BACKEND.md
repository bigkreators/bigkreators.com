# Cryptopedia Backend Architecture

## Technology Stack
- **Language/Framework**: Python with FastAPI/Uvicorn
- **Database**: MongoDB (for flexible schema)
- **Search Engine**: Elasticsearch for full-text search capabilities
- **Authentication**: JWT (JSON Web Tokens) for authentication
- **File Storage**: Amazon S3 or similar for media files
- **Caching**: Redis for performance optimization

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - User login
- `GET /api/auth/me` - Get current user info
- `PUT /api/auth/me` - Update user profile

### Articles
- `GET /api/articles` - List articles (with pagination & filters)
- `GET /api/articles/featured` - Get featured article
- `GET /api/articles/random` - Get random article
- `GET /api/articles/{id}` - Get specific article
- `POST /api/articles` - Create new article
- `PUT /api/articles/{id}` - Update article
- `DELETE /api/articles/{id}` - Delete article (admin only)
- `GET /api/articles/{id}/history` - Get article revision history
- `GET /api/articles/{id}/revisions/{revId}` - Get specific revision

### Search
- `GET /api/search?q={query}` - Search across articles

### Community Features
- `POST /api/articles/{id}/proposals` - Submit edit proposal
- `GET /api/articles/{id}/proposals` - Get all proposals for article
- `PUT /api/articles/{id}/proposals/{propId}` - Approve/reject proposal
- `POST /api/articles/{id}/rewards` - Reward an edit contribution

### Media
- `POST /api/media/upload` - Upload media file
- `GET /api/media/{id}` - Get media file metadata

### Special Pages
- `GET /api/special/recentchanges` - Get list of recent changes
- `GET /api/special/statistics` - Get wiki statistics
