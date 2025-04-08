# Cryptopedia Wiki Platform

A complete wiki platform built with FastAPI and MongoDB, designed for easy local deployment and customization.

![Cryptopedia Screenshot](https://example.com/screenshot.png)

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

## Quick Start

The easiest way to get started is to use the setup script:

```bash
# Clone the repository
git clone https://github.com/yourusername/cryptopedia.git
cd cryptopedia

# Run the setup script
chmod +x setup.sh
./setup.sh
```

The setup script will:
1. Create a virtual environment
2. Install dependencies
3. Set up the database
4. Initialize the wiki with sample content
5. Start the application

Once started, visit http://localhost:8000 in your browser.

Default admin login:
- Username: admin
- Password: admin123

## Manual Installation

If you prefer to set things up manually:

1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Create a `.env` file (see `.env.example`)
6. Run the initialization script: `python init_cryptopedia.py`
7. Start the application: `uvicorn main:app --reload`

## System Requirements

- Python 3.8+
- MongoDB 4.0+
- Optional:
  - Redis (for enhanced caching)
  - Elasticsearch (for advanced search)
  - AWS S3 account (for S3 storage)

## Configuration

Configuration is done through environment variables or a `.env` file:

| Variable | Description | Default |
|----------|-------------|---------|
| MONGO_URI | MongoDB connection URI | mongodb://localhost:27017 |
| DB_NAME | Database name | cryptopedia |
| JWT_SECRET | Secret key for JWT tokens | (random generated) |
| STORAGE_TYPE | Storage type (local or s3) | local |
| MEDIA_FOLDER | Local media folder path | media |
| USE_ELASTICSEARCH | Enable Elasticsearch | false |
| USE_REDIS | Enable Redis caching | false |

See [STORAGE.md](STORAGE.md) for more details on storage configuration.

## Project Structure

- **Backend**: FastAPI application in `main.py`
- **Frontend**: HTML templates in `templates/` directory
- **Database**: MongoDB schemas and models
- **Static Assets**: CSS and JavaScript in `static/` directory
- **Media**: Uploaded files in `media/` directory (when using local storage)

For more information on the frontend implementation, see [FRONTEND.md](FRONTEND.md).

## API Documentation

Once the application is running, API documentation is available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Customization

Cryptopedia is designed to be easily customizable:

- **Templates**: Modify HTML templates in the `templates/` directory
- **Styling**: Customize CSS in `static/style.css`
- **Functionality**: Extend JavaScript in `static/script.js`
- **Backend**: Modify API endpoints in `main.py`

## Docker Deployment

A Docker Compose configuration is included for containerized deployment:

```bash
docker-compose up -d
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
