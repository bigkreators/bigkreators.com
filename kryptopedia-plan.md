# Kryptopedia - Master Table of Contents

## Overview
Kryptopedia is a collaborative knowledge base wiki platform built with FastAPI and MongoDB. This document provides a comprehensive table of contents for the entire codebase.

## Core Files

| File | Description |
|------|-------------|
| [main.py](main.py) | Application entry point - defines FastAPI app, routes, middleware |
| [config.py](config.py) | Configuration settings - loads environment variables |
| [setup-data.py](setup-data.py) | Initialization script for setting up initial data |
| [Dockerfile](Dockerfile) | Docker configuration for containerization |
| [docker-compose.yml](docker-compose.yml) | Docker Compose services definition |
| [requirements.txt](requirements.txt) | Python dependencies |
| [BACKEND.md](BACKEND.md) | Backend architecture documentation |
| [FRONTEND.md](FRONTEND.md) | Frontend architecture documentation |
| [STORAGE.md](STORAGE.md) | Storage configuration documentation |
| [README.md](README.md) | Project overview and instructions |
| [LICENSE](LICENSE) | MIT No Attribution license file |

## Models

| File | Description |
|------|-------------|
| [models/\_\_init\_\_.py](models/__init__.py) | Models package initialization |
| [models/base.py](models/base.py) | Base models and shared data types |
| [models/article.py](models/article.py) | Article-related models |
| [models/user.py](models/user.py) | User-related models |
| [models/media.py](models/media.py) | Media-related models |
| [models/revision.py](models/revision.py) | Revision-related models |
| [models/proposal.py](models/proposal.py) | Proposal-related models |
| [models/reward.py](models/reward.py) | Reward-related models |

## Routes

| File | Description |
|------|-------------|
| [routes/\_\_init\_\_.py](routes/__init__.py) | Routes package initialization |
| [routes/auth.py](routes/auth.py) | Authentication routes |
| [routes/articles.py](routes/articles.py) | Article CRUD routes |
| [routes/media.py](routes/media.py) | Media upload/retrieve routes |
| [routes/proposals.py](routes/proposals.py) | Edit proposal routes |
| [routes/rewards.py](routes/rewards.py) | Contributor reward routes |
| [routes/special.py](routes/special.py) | Special pages routes (statistics, recent changes) |
| [routes/page_routes.py](routes/page_routes.py) | Frontend page rendering routes |

## Services

| File | Description |
|------|-------------|
| [services/\_\_init\_\_.py](services/__init__.py) | Services package initialization |
| [services/database.py](services/database.py) | MongoDB database service |
| **Storage Services** | |
| [services/storage/\_\_init\_\_.py](services/storage/__init__.py) | Storage services initialization |
| [services/storage/base.py](services/storage/base.py) | Storage interface definition |
| [services/storage/local.py](services/storage/local.py) | Local filesystem storage |
| [services/storage/s3.py](services/storage/s3.py) | Amazon S3 storage |
| **Cache Services** | |
| [services/cache/\_\_init\_\_.py](services/cache/__init__.py) | Cache services initialization |
| [services/cache/base.py](services/cache/base.py) | Cache interface definition |
| [services/cache/memory.py](services/cache/memory.py) | In-memory cache implementation |
| [services/cache/redis.py](services/cache/redis.py) | Redis cache implementation |
| **Search Services** | |
| [services/search/\_\_init\_\_.py](services/search/__init__.py) | Search services initialization |
| [services/search/base.py](services/search/base.py) | Search interface definition |
| [services/search/mongo.py](services/search/mongo.py) | MongoDB text search implementation |
| [services/search/elasticsearch.py](services/search/elasticsearch.py) | Elasticsearch implementation |

## Dependencies

| File | Description |
|------|-------------|
| [dependencies/\_\_init\_\_.py](dependencies/__init__.py) | Dependencies package initialization |
| [dependencies/auth.py](dependencies/auth.py) | Authentication dependencies |
| [dependencies/database.py](dependencies/database.py) | Database connection dependency |
| [dependencies/storage.py](dependencies/storage.py) | Storage service dependency |
| [dependencies/cache.py](dependencies/cache.py) | Cache service dependency |
| [dependencies/search.py](dependencies/search.py) | Search service dependency |

## Utilities

| File | Description |
|------|-------------|
| [utils/\_\_init\_\_.py](utils/__init__.py) | Utilities package initialization |
| [utils/security.py](utils/security.py) | Security utilities (passwords, JWT) |
| [utils/slug.py](utils/slug.py) | URL slug generation utilities |
| [utils/template_filters.py](utils/template_filters.py) | Jinja2 template filters |
| [utils/cleanup-old-files.sh](utils/cleanup-old-files.sh) | Script to clean up old files |
| [utils/copy-refactored-files.sh](utils/copy-refactored-files.sh) | Script to copy refactored files |

## Templates

| File | Description |
|------|-------------|
| [templates/base.html](templates/base.html) | Base template with common layout |
| [templates/index.html](templates/index.html) | Homepage template |
| [templates/article.html](templates/article.html) | Article view template |
| [templates/articles_list.html](templates/articles_list.html) | Article listing template |
| [templates/search_results.html](templates/search_results.html) | Search results template |
| [templates/create_article.html](templates/create_article.html) | Article creation template |
| [templates/edit_article.html](templates/edit_article.html) | Article editing template |
| [templates/article_history.html](templates/article_history.html) | Article revision history template |
| [templates/article_revision.html](templates/article_revision.html) | Single revision view template |
| [templates/article_compare.html](templates/article_compare.html) | Revision comparison template |
| [templates/article_restore_confirm.html](templates/article_restore_confirm.html) | Revision restore confirmation |
| [templates/propose_edit.html](templates/propose_edit.html) | Edit proposal creation template |
| [templates/proposal_view.html](templates/proposal_view.html) | Proposal view template |
| [templates/proposals_list.html](templates/proposals_list.html) | Proposals listing template |
| [templates/categories.html](templates/categories.html) | Categories listing template |
| [templates/tags.html](templates/tags.html) | Tags listing template |
| [templates/quick_edit.html](templates/quick_edit.html) | Quick edit page for testing |
| [templates/statistics.html](templates/statistics.html) | Wiki statistics page |
| [templates/recent_changes.html](templates/recent_changes.html) | Recent changes page |
| [templates/404.html](templates/404.html) | 404 Not Found error page |
| [templates/403.html](templates/403.html) | 403 Forbidden error page |
| [templates/error.html](templates/error.html) | Generic error page |
| [templates/login_test.html](templates/login_test.html) | Login test page |
| [templates/article_management.html](templates/article_management.html) | Admin article management page |
| [templates/admin_dashboard.html](templates/admin_dashboard.html) | Admin dashboard |
| [templates/user_management.html](templates/user_management.html) | User management page |
| [templates/user_profile.html](templates/user_profile.html) | User profile page |
| [templates/user_profile_edit.html](templates/user_profile_edit.html) | User profile edit page |

## Static Assets

| File | Description |
|------|-------------|
| [static/style.css](static/style.css) | Main stylesheet |
| [static/script.js](static/script.js) | Main JavaScript file |

## Scripts

| File | Description |
|------|-------------|
| [install.sh](install.sh) | Installation script |
| [setup-dependencies.sh](setup-dependencies.sh) | Dependencies installation script |
| [setup-directory-structure.sh](setup-directory-structure.sh) | Directory structure setup script |
| [start-local.sh](start-local.sh) | Local startup script |
| [docker-start.sh](docker-start.sh) | Docker-based startup script |
| [docker-deploy.sh](docker-deploy.sh) | Docker deployment script |
| [debug_dependencies.py](debug_dependencies.py) | Diagnostic tool for troubleshooting dependencies |

## Configuration Files

| File | Description |
|------|-------------|
| [.gitignore](.gitignore) | Git ignored files |
| [.github/workflows/python-app.yml](.github/workflows/python-app.yml) | GitHub Actions workflow |
| [.eslintrc.cjs](.eslintrc.cjs) | ESLint configuration |
| [source.env](source.env) | Sample environment variables |
| [.initialized](.initialized) | Initialization marker |

## Admin/User Management Features

| Feature | Implemented In | Status |
|---------|----------------|--------|
| User Registration | routes/auth.py | ✅ Complete |
| User Login | routes/auth.py | ✅ Complete |
| Profile Management | routes/auth.py | ⚠️ Partial |
| Role-based Access | dependencies/auth.py | ✅ Complete |
| Admin Dashboard | routes/page_routes.py | ⚠️ Missing UI |
| User Listing | routes/special.py | ✅ API Complete |
| User Role Management | routes/special.py | ✅ API Complete |
| Article Management | routes/articles.py | ✅ Complete |

## Implementation Status

| Page/Feature | Implementation Status | Notes |
|--------------|------------------------|-------|
| Admin Dashboard | ✅ Complete | Created admin_dashboard.html with navigation |
| User Management UI | ✅ Complete | Created user_management.html with CRUD functionality |
| User Profile Page | ✅ Complete | Created user_profile.html to display user info |
| Admin Statistics Dashboard | ✅ Complete | Integrated into admin dashboard |
| User Roles Management UI | ✅ Complete | Integrated into user management page |

## Common URL Paths

| Path | Description | Implementation Status |
|------|-------------|------------------------|
| `/` | Homepage | ✅ Complete |
| `/articles` | Articles list | ✅ Complete |
| `/articles/{slug}` | Article view | ✅ Complete |
| `/create-article` | Create article | ✅ Complete |
| `/edit-article/{id}` | Edit article | ✅ Complete |
| `/articles/{id}/history` | Article history | ✅ Complete |
| `/articles/{id}/propose` | Propose edit | ✅ Complete |
| `/proposals` | Proposals list | ✅ Complete |
| `/categories` | Categories list | ✅ Complete |
| `/tags` | Tags list | ✅ Complete |
| `/special/recentchanges` | Recent changes | ✅ Complete |
| `/special/statistics` | Statistics | ✅ Complete |
| `/admin` | Admin dashboard | ✅ Complete |
| `/admin/articles` | Admin article management | ✅ Complete |
| `/admin/users` | Admin user management | ✅ Complete |
| `/users/{id}` | User profile | ✅ Complete |
| `/users/{id}/edit` | Edit user profile | ✅ Complete |
| `/search` | Search results | ✅ Complete |

## Known Issues

1. **Missing Admin UI**: While API routes for user management exist, the admin dashboard and user management UI pages are incomplete.
2. **Navigation to Admin**: No clear navigation path to admin pages exists in the UI.
3. **User Profile Management**: User profile viewing and editing capabilities are not fully implemented.
4. **Role Management UI**: No interface for changing user roles, though the API exists.

## Next Steps for Development

1. Implement the missing admin dashboard UI at `/admin`
2. Create a user management interface at `/admin/users`
3. Add user profile pages at `/user/profile` and `/user/{username}`
4. Add navigation links to admin sections for admin/editor users
5. Implement role management UI in the admin section
