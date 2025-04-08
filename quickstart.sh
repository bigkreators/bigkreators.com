#!/bin/bash

# Quickstart script for Cryptopedia Backend

echo "===== Cryptopedia Backend Quickstart ====="
echo "This script will help you quickly start the Cryptopedia backend service locally."

# Check for docker-compose
if command -v docker-compose &> /dev/null; then
    echo "Docker Compose found. Would you like to use Docker? (y/n)"
    read use_docker
    
    if [[ $use_docker == "y" || $use_docker == "Y" ]]; then
        # Use Docker
        echo "Starting services with Docker Compose..."
        docker-compose up -d
        
        echo ""
        echo "=== Cryptopedia Backend is now running! ==="
        echo "Access the API at: http://localhost:8000"
        echo "API Documentation: http://localhost:8000/docs"
        exit 0
    fi
fi

# Manual setup
echo "Setting up manually..."

# Create virtual environment
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

# Create media directory
if [ ! -d "media" ]; then
    echo "Creating media directory..."
    mkdir -p media
fi

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cat > .env << EOL
# Database Configuration
MONGO_URI=mongodb://localhost:27017
DB_NAME=cryptopedia

# JWT Configuration
JWT_SECRET=local-development-secret-key-not-for-production

# Media Storage Configuration
MEDIA_FOLDER=media

# Optional External Services (set to false to use local alternatives)
USE_ELASTICSEARCH=false
USE_REDIS=false
EOL
fi

# Check if MongoDB is running
mongo_running=false
if command -v mongod &> /dev/null; then
    if pgrep mongod > /dev/null; then
        mongo_running=true
    fi
fi

if [ "$mongo_running" = false ]; then
    echo "MongoDB is not running. Starting MongoDB in a new terminal..."
    
    # Check platform and open new terminal with MongoDB
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        osascript -e 'tell app "Terminal" to do script "cd '$(pwd)' && ./start-mongodb.sh"'
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        if command -v gnome-terminal &> /dev/null; then
            gnome-terminal -- bash -c "cd $(pwd) && ./start-mongodb.sh; exec bash"
        elif command -v xterm &> /dev/null; then
            xterm -e "cd $(pwd) && ./start-mongodb.sh" &
        else
            echo "Cannot start a new terminal automatically. Please run MongoDB manually:"
            echo "cd $(pwd) && ./start-mongodb.sh"
            exit 1
        fi
    else
        echo "Unsupported OS. Please start MongoDB manually in a separate terminal:"
        echo "cd $(pwd) && ./start-mongodb.sh"
        exit 1
    fi
    
    # Wait for MongoDB to start
    echo "Waiting for MongoDB to start..."
    sleep 5
fi

# Start the FastAPI application
echo ""
echo "Starting Cryptopedia backend service..."
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Note: This script can be improved with more error checking and validation
