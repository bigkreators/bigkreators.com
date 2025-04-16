# Kryptopedia 

A collaborative knowledge base wiki platform built with FastAPI and MongoDB.

![birdLogo](https://github.com/user-attachments/assets/5e2a39c4-eeb3-48cd-86a5-c9aefd28bb74)

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

## Installation

### Quick Start (Automated)

The easiest way to get started is using our automated installation script:

```bash
# Clone the repository
git clone https://github.com/yourusername/kryptopedia.git
cd kryptopedia

# Run the installation script
./install.sh
```

This script will:
- Create a virtual environment
- Install all required dependencies
- Set up MongoDB connection
- Initialize the database with sample content
- Create necessary directories

### Step-by-Step Installation

If you prefer to install manually or the automated script doesn't work for your system, follow these steps:

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/kryptopedia.git
   cd kryptopedia
   ```

2. **Install dependencies:**
   Run the dependencies installation script which will set up Python, MongoDB, Docker, and optional Node.js:
   ```bash
   ./setup-dependencies.sh
   ```

3. **Set up directory structure:**
   Create the necessary directory structure for the application:
   ```bash
   ./setup-directory-structure.sh
   ```

4. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

5. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

6. **Make sure MongoDB is running:**
   ```bash
   # Create a directory for MongoDB data if it doesn't exist
   mkdir -p mongodb_data
   
   # Start MongoDB
   mongod --dbpath=./mongodb_data
   ```

7. **Initialize the database:**
   This will create the initial admin user and demo article:
   ```bash
   python setup-data.py
   ```

8. **Start the application:**
   ```bash
   ./start-local.sh
   ```
   Or if you prefer to run it manually:
   ```bash
   uvicorn main:app --reload
   ```

9. **Open http://localhost:8000 in your browser**

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

### Common Issues

1. **MongoDB connection fails**: 
   - Ensure MongoDB is running with `mongod --dbpath=./mongodb_data`
   - Check the MongoDB URI in your `.env` file

2. **Missing dependencies**:
   - Run `./setup-dependencies.sh` to ensure all system dependencies are installed

3. **Permission issues**:
   - Make sure scripts are executable with `chmod +x *.sh`

4. **Directory structure issues**:
   - Run `./setup-directory-structure.sh` to recreate the correct directory structure
