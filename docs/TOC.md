# Kryptopedia Refactored Application Structure

## Project Structure Overview

```
cryptopedia/
├── main.py                  # Application entry point
├── config.py                # Configuration settings
│
├── models/                  # Pydantic models
│   ├── __init__.py
│   ├── base.py              # Base models and shared types
│   ├── user.py              # User models
│   ├── article.py           # Article models
│   ├── revision.py          # Revision models
│   ├── proposal.py          # Proposal models
│   ├── media.py             # Media models
│   └── reward.py            # Reward models
│
├── routes/                  # API routes
│   ├── __init__.py
│   ├── auth.py              # Authentication routes
│   ├── articles.py          # Article CRUD routes
│   ├── media.py             # Media upload/retrieve
│   ├── proposals.py         # Edit proposals
│   ├── rewards.py           # Reward system
│   ├── special.py           # Special pages (stats, recent changes)
│   └── templates.py         # Template routes
│
├── services/                # Business logic
│   ├── __init__.py
│   ├── database.py          # MongoDB connection & helpers
│   ├── storage/             # Storage services
│   │   ├── __init__.py
│   │   ├── base.py          # Storage interface
│   │   ├── local.py         # Local storage
│   │   └── s3.py            # S3 storage
│   ├── cache/               # Caching services
│   │   ├── __init__.py
│   │   ├── base.py          # Cache interface
│   │   ├── memory.py        # In-memory cache
│   │   └── redis.py         # Redis cache
│   └── search/              # Search services
│       ├── __init__.py
│       ├── base.py          # Search interface
│       ├── mongo.py         # MongoDB search
│       └── elasticsearch.py # Elasticsearch search
│
├── dependencies/            # FastAPI dependencies
│   ├── __init__.py
│   ├── auth.py              # Authentication dependencies
│   ├── database.py          # Database dependencies
│   ├── storage.py           # Storage dependencies
│   ├── cache.py             # Cache dependencies
│   └── search.py            # Search dependencies
│
└── utils/                   # Utility functions
    ├── __init__.py
    ├── security.py          # JWT and password handling
    ├── slug.py              # Slug generation
    └── template_filters.py  # Jinja2 template filters
```

## Key Components

### Configuration (config.py)
- Environment variable loading
- Application settings

### Models
- Data validation models using Pydantic
- Database schema definitions

### Services
- Core business logic
- Database interactions
- Storage abstraction (local/S3)
- Caching strategies (memory/Redis)
- Search functionality (MongoDB/Elasticsearch)

### Dependencies
- FastAPI dependency injection
- Authentication middleware
- Resource management

### Routes
- API endpoints
- Template rendering
- Request handling

### Utilities
- Helper functions
- Security utilities
- Template filters

## Main Fixed Issues

1. **Await Statement Error**: Fixed the issue where `await` was used outside async functions
2. **Code Organization**: Modularized code for better maintainability
3. **Dependency Injection**: Properly isolated dependencies
4. **Error Handling**: Consistent error handling patterns
5. **Storage Abstraction**: Clean separation for storage strategies

## Migration Strategy

The code has been refactored in a way that:

1. Maintains the same functionality as the original
2. Fixes the await statement error
3. Makes the codebase more maintainable
4. Follows proper Python and FastAPI practices

To migrate:

1. Create the directory structure
2. Copy each file to its proper location
3. Test functionality incrementally
4. Update any references in templates or static files to match the new structure

## Usage

To run the application:

```bash
python main.py
```

Or with uvicorn directly:

```bash
uvicorn main:app --reload
```

## API Documentation

With this refactoring, API docs are available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
