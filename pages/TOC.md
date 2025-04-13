# Kryptopedia Technical Documentation Table of Contents

This document provides a comprehensive table of contents for the Kryptopedia application codebase. All major files are tracked here with links to their respective detailed documentation.

Last updated: April 13, 2025

## Core Application Files

- [main.py](main.py) - Main entry point for the FastAPI application
- [config.py](config.py) - Configuration settings loaded from environment variables
- [requirements.txt](requirements.txt) - Project dependencies
- [Dockerfile](Dockerfile) - Container configuration

## Page Routers

Handles web page rendering and user interface:

- [pages/__init__.py](pages/__init__.py) - Pages package initialization and combined router
- [pages/home.py](pages/home.py) - Home page and core navigation routes
- [pages/articles.py](pages/articles.py) - Article display and management pages
- [pages/admin.py](pages/admin.py) - Admin dashboard and management pages
- [pages/special.py](pages/special.py) - Special pages (stats, recent changes, etc.)
- [pages/proposals.py](pages/proposals.py) - Edit proposal pages
- [pages/search.py](pages/search.py) - Search functionality pages
- [pages/user_profile.py](pages/user_profile.py) - User profile pages
- [pages/errors.py](pages/errors.py) - Error handler pages

## API Routes

Handles REST API endpoints for data operations:

- [routes/__init__.py](routes/__init__.py) - Routes package initialization
- [routes/auth.py](routes/auth.py) - Authentication endpoints
- [routes/articles.py](routes/articles.py) - Article CRUD operations
- [routes/media.py](routes/media.py) - Media file operations
- [routes/proposals.py](routes/proposals.py) - Edit proposal operations
- [routes/rewards.py](routes/rewards.py) - User reward system
- [routes/special.py](routes/special.py) - Special statistics and operations
- [routes/profile.py](routes/profile.py) - User profile operations

## Models

Defines data structures using Pydantic:

- [models/__init__.py](models/__init__.py) - Models package initialization
- [models/base.py](models/base.py) - Base model classes
- [models/user.py](models/user.py) - User-related models
- [models/article.py](models/article.py) - Article-related models
- [models/revision.py](models/revision.py) - Revision history models
- [models/proposal.py](models/proposal.py) - Edit proposal models
- [models/media.py](models/media.py) - Media file models
- [models/reward.py](models/reward.py) - Reward system models

## Dependencies

Dependency injection for FastAPI endpoints:

- [dependencies/__init__.py](dependencies/__init__.py) - Dependencies package initialization
- [dependencies/database.py](dependencies/database.py) - Database connection
- [dependencies/auth.py](dependencies/auth.py) - Authentication and permission checking
- [dependencies/storage.py](dependencies/storage.py) - File storage access
- [dependencies/cache.py](dependencies/cache.py) - Caching functionality
- [dependencies/search.py](dependencies/search.py) - Search functionality

## Services

Core application services:

- [services/__init__.py](services/__init__.py) - Services package initialization
- [services/database.py](services/database.py) - Database service
- [services/storage/__init__.py](services/storage/__init__.py) - Storage service package
- [services/storage/base.py](services/storage/base.py) - Storage interface
- [services/storage/local.py](services/storage/local.py) - Local file storage
- [services/storage/s3.py](services/storage/s3.py) - AWS S3 storage
- [services/cache/__init__.py](services/cache/__init__.py) - Cache service package
- [services/cache/base.py](services/cache/base.py) - Cache interface
- [services/cache/memory.py](services/cache/memory.py) - In-memory cache
- [services/cache/redis.py](services/cache/redis.py) - Redis cache
- [services/search/__init__.py](services/search/__init__.py) - Search service package
- [services/search/base.py](services/search/base.py) - Search interface
- [services/search/elasticsearch.py](services/search/elasticsearch.py) - Elasticsearch implementation
- [services/search/mongo.py](services/search/mongo.py) - MongoDB text search implementation

## Utilities

Helper functions and tools:

- [utils/__init__.py](utils/__init__.py) - Utilities package initialization
- [utils/security.py](utils/security.py) - Password hashing and JWT
- [utils/slug.py](utils/slug.py) - URL slug generation
- [utils/template_filters.py](utils/template_filters.py) - Jinja2 template filters

## Templates

HTML templates for rendering pages:

- [templates/base.html](templates/base.html) - Base template with common elements
- [templates/index.html](templates/index.html) - Homepage template
- [templates/article.html](templates/article.html) - Article view template
- [templates/articles_list.html](templates/articles_list.html) - Article listing template
- [templates/create_article.html](templates/create_article.html) - Article creation form
- [templates/edit_article.html](templates/edit_article.html) - Article editing form
- [templates/article_history.html](templates/article_history.html) - Revision history
- [templates/article_revision.html](templates/article_revision.html) - View specific revision
- [templates/article_compare.html](templates/article_compare.html) - Compare revisions
- [templates/article_restore_confirm.html](templates/article_restore_confirm.html) - Restore revision
- [templates/search_results.html](templates/search_results.html) - Search results
- [templates/user_profile.html](templates/user_profile.html) - User profile
- [templates/profile_edit.html](templates/profile_edit.html) - Edit user profile
- [templates/quick_edit.html](templates/quick_edit.html) - Quick editing interface
- [templates/proposals_list.html](templates/proposals_list.html) - List edit proposals
- [templates/proposal_view.html](templates/proposal_view.html) - View proposal details
- [templates/propose_edit.html](templates/propose_edit.html) - Create edit proposal
- [templates/categories.html](templates/categories.html) - Browse categories
- [templates/tags.html](templates/tags.html) - Browse tags
- [templates/404.html](templates/404.html) - Not found page
- [templates/403.html](templates/403.html) - Forbidden page
- [templates/error.html](templates/error.html) - Generic error page
- [templates/statistics.html](templates/statistics.html) - Wiki statistics
- [templates/recent_changes.html](templates/recent_changes.html) - Recent changes
- [templates/admin_dashboard.html](templates/admin_dashboard.html) - Admin dashboard
- [templates/article_management.html](templates/article_management.html) - Article management
- [templates/user_management.html](templates/user_management.html) - User management
- [templates/user_profile_edit.html](templates/user_profile_edit.html) - Edit user profile (admin)

## Static Assets

- [static/style.css](static/style.css) - Main CSS stylesheet
- [static/script.js](static/script.js) - Main JavaScript

## Development and Deployment

- [utils/cleanup-old-files.sh](utils/cleanup-old-files.sh) - Cleanup script
- [utils/copy-refactored-files.sh](utils/copy-refactored-files.sh) - Refactoring script

## Schema Information

- [services/mongodb.txt](services/mongodb.txt) - MongoDB schema examples

## Project Structure Overview

```
kryptopedia/
├── main.py
├── config.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── pages/
│   ├── __init__.py
│   ├── home.py
│   ├── articles.py
│   ├── admin.py
│   ├── special.py
│   ├── proposals.py
│   ├── search.py
│   ├── user_profile.py
│   └── errors.py
├── routes/
│   ├── __init__.py
│   ├── auth.py
│   ├── articles.py
│   ├── media.py
│   ├── proposals.py
│   ├── rewards.py
│   ├── special.py
│   └── profile.py
├── models/
│   ├── __init__.py
│   ├── base.py
│   ├── user.py
│   ├── article.py
│   ├── revision.py
│   ├── proposal.py
│   ├── media.py
│   └── reward.py
├── dependencies/
│   ├── __init__.py
│   ├── database.py
│   ├── auth.py
│   ├── storage.py
│   ├── cache.py
│   └── search.py
├── services/
│   ├── __init__.py
│   ├── database.py
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── local.py
│   │   └── s3.py
│   ├── cache/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── memory.py
│   │   └── redis.py
│   └── search/
│       ├── __init__.py
│       ├── base.py
│       ├── elasticsearch.py
│       └── mongo.py
├── utils/
│   ├── __init__.py
│   ├── security.py
│   ├── slug.py
│   └── template_filters.py
├── templates/
│   ├── base.html
│   ├── index.html
│   └── ... (all templates)
├── static/
│   ├── style.css
│   └── script.js
└── media/
```

## Recent Changes and Refactoring

The codebase has recently undergone a significant refactoring to improve modularity and organization:

1. Moved page rendering routes from `routes/page_routes.py` to the dedicated `pages/` package with specialized modules
2. Enhanced error handling with centralized error pages
3. Improved template organization
4. Added comprehensive documentation

This structure follows best practices for FastAPI applications, with clear separation of concerns between:
- API endpoints (routes/)
- Web pages (pages/)
- Data models (models/)
- Business logic (services/)
- Helper functions (utils/)
