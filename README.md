# Kryptopedia Wiki Platform

A complete wiki platform built with FastAPI and MongoDB, designed for easy deployment and customization.

## Features

- **Full Wiki Functionality**
  - Create, read, update, and archive articles
  - Article revision history
  - Categorization and tagging
  - Rich text editor for content creation
  - Full-text search

- **User Management**
  - User registration and authentication
  - Role-based access control (admin, editor, user)
  - User profiles with contribution tracking

- **Community Features**
  - Edit proposals system
  - Contribution rewards
  - Activity tracking

- **Media Management**
  - Local or S3-based file storage
  - Image and file uploads
  - Media embedding in articles

- **Performance Optimizations**
  - Caching support (in-memory or Redis)
  - MongoDB text search (with optional Elasticsearch)
  - Optimized database queries

## Installation

### Requirements

- Python 3.8+
- MongoDB 4.0+
- Optional:
  - Redis (for enhanced caching)
  - Elasticsearch (for advanced search)
  - AWS S3 account (for S3 storage)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/kryptopedia.git
   cd kryptopedia
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file with your configuration:
   ```
   # Database Configuration
   MONGO_URI=mongodb://localhost:27017
   DB_NAME=kryptopedia

   # JWT Configuration
   JWT_SECRET=your-secret-key-change-this-in-production

   # Storage Configuration
   STORAGE_TYPE=local  # Options: local, s3
   MEDIA_FOLDER=media

   # Optional External Services (set to true to enable)
   USE_ELASTICSEARCH=false
   USE_REDIS=false
   ```

5. Initialize the database:
   ```bash
   python setup-data.py
   ```

6. Run the application:
   ```bash
   python main.py
   ```

7. Access the wiki at http://localhost:8000

## Directory Structure

```
kryptopedia/
├── main.py                  # Application entry point
├── config.py                # Configuration settings
├── models/                  # Pydantic models
├── routes/                  # API routes
├── services/                # Business logic
├── dependencies/            # FastAPI dependencies
├── utils/                   # Utility functions
├── static/                  # Static assets (CSS, JS)
├── templates/               # HTML templates
└── media/                   # Uploaded files
```

## API Documentation

Once the application is running, API documentation is available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Docker Deployment

A Docker Compose configuration is included for containerized deployment:

```bash
docker-compose up -d
```

## Default Admin Account

- Username: admin
- Password: admin123

Be sure to change the default admin password after first login.

## Customization

Cryptopedia is designed to be easily customizable:

- **Templates**: Modify HTML templates in the `templates/` directory
- **Styling**: Customize CSS in `static/style.css`
- **Functionality**: Extend JavaScript in `static/script.js`
- **Backend**: Modify API endpoints in the `routes/` directory

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
