#!/bin/bash

# Cryptopedia Run Script
# This script starts the Cryptopedia application

echo "=== Starting Cryptopedia ==="

# Activate virtual environment if not already activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

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
    echo "MongoDB is not running. Starting MongoDB..."
    
    # Create data directory if it doesn't exist
    if [ ! -d "mongodb_data" ]; then
        mkdir -p mongodb_data
    fi
    
    # Start MongoDB in background
    mongod --dbpath=./mongodb_data --fork --logpath=./mongodb.log
    
    if [ $? -ne 0 ]; then
        echo "Failed to start MongoDB. Please start it manually before running Cryptopedia."
        exit 1
    fi
    
    echo "MongoDB started successfully."
else
    echo "MongoDB is already running."
fi

# Start the application
echo "Starting Cryptopedia server..."
uvicorn main:app --reload --host 0.0.0.0 --port 8000

echo "Cryptopedia is now running at http://localhost:8000"
