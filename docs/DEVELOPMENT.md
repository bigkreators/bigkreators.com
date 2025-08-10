# Kryptopedia Installation and Setup Guide

This guide will walk you through the process of setting up the Kryptopedia wiki platform on your local machine for development or testing.

## Prerequisites

- Python 3.8 or higher
- MongoDB 4.0 or higher
- pip (Python package manager)
- Git (optional, for cloning the repository)

## Step 1: Clone the Repository

If you're starting with the Git repository, clone it to your local machine:

```bash
git clone https://github.com/yourusername/kryptopedia.git
cd kryptopedia
```

Alternatively, download and extract the source code to a directory of your choice.

## Step 2: Create a Virtual Environment

It's recommended to use a virtual environment to isolate the project dependencies:

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

## Step 3: Install Dependencies

Install all required packages:

```bash
pip install -r requirements.txt
```

If `requirements.txt` is not present, you can install the core dependencies manually:

```bash
pip install fastapi uvicorn motor pydantic python-multipart python-dotenv PyJWT bcrypt aiofiles jinja2
```

## Step 4: Setup MongoDB

Ensure MongoDB is installed and running on your system. For local development, the default connection string is `mongodb://localhost:27017`.

You can start MongoDB with:

```bash
# Create a data directory if it doesn't exist
mkdir -p mongodb_data

# Start MongoDB pointing to this data directory
mongod --dbpath=./mongodb_data
```

## Step 5: Configure Environment Variables

Create a `.env` file in the project root with the following content:

```
# Database Configuration
MONGO_URI=mongodb://localhost:27017
DB_NAME=kryptopedia

# JWT Configuration
JWT_SECRET=your-secret-key-change-this-in-production

# Storage Configuration
STORAGE_TYPE=local
MEDIA_FOLDER=media

# Optional External Services (set to false to use local alternatives)
USE_ELASTICSEARCH=false
USE_REDIS=false
API_DEBUG=true
```

Make sure to change `JWT_SECRET` to a secure random string in production.

## Step 6: Initialize the Database

Run the setup script to initialize the database with default data:

```bash
python setup-data.py
```

## Step 7: Start the Application

You can now start the application:

```bash
uvicorn main:app --reload
```

The `--reload` flag enables auto-reloading when code changes are detected, which is useful during development.

Your Kryptopedia instance should now be running at http://localhost:8000

## Step 8: Run Diagnostics (Optional)

If you encounter issues, you can run the diagnostic script to check for common problems:

```bash
python diagnose.py
```

This script will check your installation and suggest fixes for common issues.

## Directory Structure

Here's a brief overview of the project structure:

- `main.py`: Application entry point
- `config.py`: Configuration settings
- `models/`: Pydantic data models
- `routes/`: API and page routes
- `services/`: Business logic and external services
- `dependencies/`: FastAPI dependency injection
- `utils/`: Utility functions
- `templates/`: HTML templates
- `static/`: CSS, JavaScript, and other static files
- `media/`: Uploaded files storage (when using local storage)

## Common Issues and Solutions

### 404 Not Found for /special/recentchanges

If you encounter a 404 error for special pages:

1. Make sure the templates exist (`templates/recent_changes.html`, `templates/statistics.html`, etc.)
2. Check that the routes are correctly registered in the `routes/page_routes.py` file
3. Verify that the router is properly included in `main.py`

### CSS Not Loading

If your CSS is not loading:

1. Ensure that the `static/style.css` file exists
2. Check that you're mounting the static directory in `main.py`
3. Verify that the base template includes the correct CSS link tag
4. Add a redirect for `/style.css` to `/static/style.css` in `main.py`

### 401 Unauthorized for Protected Routes

If you're getting authentication errors:

1. Make sure your JWT configuration is correct in the `.env` file
2. Check that you're passing the token correctly in your requests
3. The token should be included as a Bearer token in the Authorization header

## Default Admin Account

After running the setup script, the following admin account is created:

- Username: `admin`
- Email: `admin@kryptopedia.local`
- Password: `admin123`

Make sure to change this password in a production environment.

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [MongoDB Documentation](https://docs.mongodb.com/)
- [Jinja2 Template Documentation](https://jinja.palletsprojects.com/)
- [JWT Documentation](https://jwt.io/)

## Getting Help

If you encounter issues not covered in this guide, please:

1. Run the diagnostic script (`python diagnose.py`)
2. Check the application logs for error messages
3. Look for similar issues in the project repository
4. Contact the project maintainers
