# Kryptopedia 

A collaborative knowledge base wiki platform built with FastAPI and MongoDB.

![Kryptopedia Screenshot](https://via.placeholder.com/800x400?text=Kryptopedia+Wiki+Platform)

## Features

- **Full Wiki Functionality**
  - Create, read, update, and archive articles
  - Article revision history
  - Categorization and tagging
  - Rich text content editing
  - Full-text search capabilities

- **User Management**
  - User registration and authentication
  - Role-based access control (admin, editor, user)
  - User profiles with contribution tracking

- **Community Features**
  - Edit proposals system
  - Contribution rewards
  - Activity tracking and statistics
  - Recent changes page

- **Media Management**
  - Local file storage (with optional S3 storage)
  - Image and file uploads
  - Media embedding in articles

- **Performance Optimizations**
  - Caching support (memory or Redis)
  - Database query optimization
  - Content delivery optimization

## Tech Stack

- **Backend**: Python 3.8+ with FastAPI
- **Database**: MongoDB
- **Frontend**: Jinja2 Templates, Vanilla JavaScript, and CSS
- **Authentication**: JWT-based auth
- **Deployment**: Docker support (optional)

## Quick Start

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/kryptopedia.git
   cd kryptopedia
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Make sure MongoDB is running:
   ```bash
   mongod --dbpath=./mongodb_data
   ```

5. Initialize the database:
   ```bash
   python setup-data.py
   ```

6. Start the application:
   ```bash
   uvicorn main:app --reload
   ```

7. Open http://localhost:8000 in your browser

For detailed installation instructions, see [INSTALLATION.md](INSTALLATION.md).

## Default Admin Account

After running the setup script, the following admin account is created:

- Username: `admin`
- Email: `admin@kryptopedia.local`
- Password: `admin123`

Make sure to change this password in a production environment.

## Project Structure

```
kryptopedia/
├── main.py                  # Application entry point
├── config.py                # Configuration settings
├── models/                  # Pydantic models for data validation
├── routes/                  # API routes
├── services/                # Business logic
├── dependencies/            # FastAPI dependencies
├── utils/                   # Utility functions
├── static/                  # Static assets
├── templates/               # HTML templates
└── media/                   # Uploaded files (when using local storage)
```

## API Documentation

Once the application is running, API documentation is available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Development

For development, run the diagnostic script to ensure everything is set up correctly:

```bash
python diagnose.py
```

This script will check your setup and suggest fixes for common issues.

## Docker Deployment

A Dockerfile and docker-compose.yml file are included for containerized deployment:

```bash
docker-compose up -d
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Troubleshooting

If you encounter issues, check out the common problems and solutions in our [INSTALLATION.md](INSTALLATION.md) guide or run the diagnostic script:

```bash
python diagnose.py
```
