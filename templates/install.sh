#!/bin/bash

# Cryptopedia Install Script
# This script sets up everything needed for Cryptopedia

echo "=== Cryptopedia Installation ==="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Create necessary directories
echo "Creating necessary directories..."
mkdir -p templates static media

# Check if MongoDB is running
echo "Checking MongoDB connection..."
python3 -c "
from pymongo import MongoClient
try:
    client = MongoClient('mongodb://localhost:27017', serverSelectionTimeoutMS=5000)
    client.server_info()
    print('MongoDB is running')
except Exception as e:
    print(f'MongoDB is not running: {e}')
    exit(1)
"

if [ $? -ne 0 ]; then
    echo "MongoDB is not running. Please start MongoDB before continuing."
    echo "You can start MongoDB with: mongod --dbpath=./mongodb_data"
    exit 1
fi

# Create .env file
echo "Creating .env file..."
cat > .env << EOL
# Database Configuration
MONGO_URI=mongodb://localhost:27017
DB_NAME=kryptopedia

# JWT Configuration
JWT_SECRET=$(openssl rand -hex 32)

# Storage Configuration
STORAGE_TYPE=local
MEDIA_FOLDER=media

# Optional External Services (set to false to use local alternatives)
USE_ELASTICSEARCH=false
USE_REDIS=false
EOL

# Initialize database with sample content
echo "Initializing database with sample content..."
python3 init_kryptopedia.py

echo ""
echo "=== Installation Complete! ==="
echo "To start Cryptopedia, run: ./run.sh"
