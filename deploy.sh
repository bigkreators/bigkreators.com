#!/bin/bash

# Cryptopedia Deployment Script
# This script sets up the environment and starts the FastAPI service

echo "===== Cryptopedia Backend Deployment ====="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "pip3 is not installed. Please install pip for Python 3."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install requirements
echo "Installing requirements..."
pip install -r requirements.txt

# Create media directory if it doesn't exist
if [ ! -d "media" ]; then
    echo "Creating media directory..."
    mkdir -p media
fi

# Set up environment variables
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cat > .env << EOL
# Database Configuration
MONGO_URI=mongodb://localhost:27017
DB_NAME=cryptopedia

# JWT Configuration
JWT_SECRET=your-secret-key-change-this-in-production

# Storage Configuration
STORAGE_TYPE=local  # Options: local, s3
MEDIA_FOLDER=media

# S3 Configuration (only used if STORAGE_TYPE=s3)
S3_BUCKET=cryptopedia-media
AWS_ACCESS_KEY=
AWS_SECRET_KEY=
AWS_REGION=us-east-1

# Optional External Services (set to false to use local alternatives)
USE_ELASTICSEARCH=false
USE_REDIS=false

# External Service Configuration (only used if enabled above)
ES_HOST=http://localhost:9200
REDIS_HOST=localhost
REDIS_PORT=6379
EOL
    echo ".env file created. You can run with local alternatives by default."
fi

# Start the FastAPI application
echo "Starting Cryptopedia backend service..."
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
