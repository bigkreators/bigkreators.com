#!/bin/bash

# Script to start MongoDB for Cryptopedia

echo "=== Starting MongoDB ==="

# Create data directory if it doesn't exist
if [ ! -d "mongodb_data" ]; then
    echo "Creating MongoDB data directory..."
    mkdir -p mongodb_data
fi

# Start MongoDB
echo "Starting MongoDB server..."
mongod --dbpath=./mongodb_data

# Note: This script will keep running with MongoDB in the foreground
# Press Ctrl+C to stop MongoDB
