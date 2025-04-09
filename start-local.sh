#!/bin/bash

# Kryptopedia - Local Startup Script v0.1
# This script starts the Kryptopedia application locally (without Docker)

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}====================================================${NC}"
echo -e "${BLUE}       Kryptopedia - Local Startup Script           ${NC}"
echo -e "${BLUE}====================================================${NC}"

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if MongoDB is running
check_mongodb() {
    if command_exists mongod; then
        if pgrep mongod > /dev/null; then
            return 0
        fi
    fi
    return 1
}

# Start MongoDB if it's not running
start_mongodb() {
    echo -e "\n${BLUE}Checking MongoDB status...${NC}"
    
    if check_mongodb; then
        echo -e "${GREEN}MongoDB is already running.${NC}"
    else
        echo -e "${YELLOW}MongoDB is not running. Starting MongoDB...${NC}"
        
        # Create data directory if it doesn't exist
        if [ ! -d "mongodb_data" ]; then
            echo -e "${YELLOW}Creating MongoDB data directory...${NC}"
            mkdir -p mongodb_data
        fi
        
        # Start MongoDB
        mongod --dbpath=./mongodb_data --port 27017 --fork --logpath=./mongodb.log
        
        if [ $? -ne 0 ]; then
            echo -e "${RED}Failed to start MongoDB.${NC}"
            echo -e "${YELLOW}Try running it manually: mongod --dbpath=./mongodb_data --port 27017${NC}"
            exit 1
        fi
        
        echo -e "${GREEN}MongoDB started successfully.${NC}"
    fi
}

# Check virtual environment and activate it
activate_venv() {
    echo -e "\n${BLUE}Setting up Python environment...${NC}"
    
    if [ ! -d "venv" ]; then
        echo -e "${RED}Virtual environment not found. Please run setup-kryptopedia.sh first.${NC}"
        exit 1
    fi
    
    echo -e "${YELLOW}Activating virtual environment...${NC}"
    source venv/bin/activate
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to activate virtual environment.${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}Virtual environment activated.${NC}"
}

# Check if required files exist
check_required_files() {
    echo -e "\n${BLUE}Checking required files...${NC}"
    
    missing_files=false
    
    if [ ! -f "main.py" ]; then
        echo -e "${RED}main.py not found. Please make sure you're in the correct directory.${NC}"
        missing_files=true
    fi
    
    if [ ! -f "requirements.txt" ]; then
        echo -e "${RED}requirements.txt not found. Please make sure you're in the correct directory.${NC}"
        missing_files=true
    fi
    
    if [ ! -f ".env" ]; then
        echo -e "${RED}.env file not found. Please run setup-kryptopedia.sh first.${NC}"
        missing_files=true
    fi
    
    if [ "$missing_files" = true ]; then
        exit 1
    fi
    
    echo -e "${GREEN}All required files found.${NC}"
}

# Apply any pending migrations or initializations
initialize_app() {
    echo -e "\n${BLUE}Initializing application...${NC}"
    
    # Check if the app has been initialized before
    if [ ! -f ".initialized" ]; then
        echo -e "${YELLOW}First-time initialization...${NC}"
        
        # Run initialization script if it exists
        if [ -f "setup-data.sh" ]; then
            echo -e "${YELLOW}Running database initialization script...${NC}"
            python3 setup-data.sh
            
            if [ $? -ne 0 ]; then
                echo -e "${RED}Database initialization failed.${NC}"
                exit 1
            fi
            
            # Create the initialized marker file
            touch .initialized
            
            echo -e "${GREEN}Application initialized successfully.${NC}"
        else
            echo -e "${YELLOW}No initialization script found (setup-data.sh). Skipping initialization.${NC}"
            touch .initialized
        fi
    else
        echo -e "${GREEN}Application already initialized.${NC}"
    fi
}

# Start the application
start_application() {
    echo -e "\n${BLUE}Starting Kryptopedia application...${NC}"
    
    # Set PORT environment variable if not already set
    PORT=${PORT:-8000}
    HOST=${HOST:-0.0.0.0}
    
    echo -e "${YELLOW}Starting FastAPI server on ${HOST}:${PORT}...${NC}"
    echo -e "${YELLOW}Press Ctrl+C to stop the server.${NC}"
    
    # Start the application using uvicorn
    uvicorn main:app --host $HOST --port $PORT --reload
}

# Main function
main() {
    # Check required files
    check_required_files
    
    # Start MongoDB
    start_mongodb
    
    # Activate virtual environment
    activate_venv
    
    # Initialize application
    initialize_app
    
    # Start the application
    start_application
}

# Run the main function
main
