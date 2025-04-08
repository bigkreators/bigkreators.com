#!/bin/bash

# Script to start MongoDB for local development

echo "===== Starting MongoDB for local development ====="

# Check if MongoDB is installed
if ! command -v mongod &> /dev/null; then
    echo "MongoDB is not installed. Please install MongoDB before continuing."
    echo "Visit https://www.mongodb.com/docs/manual/installation/ for instructions."
    exit 1
fi

# Create data directory if it doesn't exist
if [ ! -d "mongodb_data" ]; then
    echo "Creating data directory..."
    mkdir -p mongodb_data
fi

# Start MongoDB using the data directory
echo "Starting MongoDB..."
mongod --dbpath=./mongodb_data --port 27017

# Note: Press Ctrl+C to stop MongoDB
