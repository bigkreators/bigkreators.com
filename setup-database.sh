#!/bin/bash

# Cryptopedia Setup Script
# This script sets up and runs the Cryptopedia wiki platform

# Colors for prettier output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}====================================================${NC}"
echo -e "${BLUE}          Cryptopedia Wiki Setup Script             ${NC}"
echo -e "${BLUE}====================================================${NC}"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 is not installed. Please install Python 3.8 or higher.${NC}"
    exit 1
fi

# Check Python version
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
if (( $(echo "$python_version < 3.8" | bc -l) )); then
    echo -e "${RED}Python version $python_version detected. Cryptopedia requires Python 3.8 or higher.${NC}"
    exit 1
fi
echo -e "${GREEN}Python $python_version detected.${NC}"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "\n${BLUE}Creating virtual environment...${NC}"
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to create virtual environment. Please check your Python installation.${NC}"
        exit 1
    fi
    echo -e "${GREEN}Virtual environment created.${NC}"
else
    echo -e "${GREEN}Using existing virtual environment.${NC}"
fi

# Activate virtual environment
echo -e "\n${BLUE}Activating virtual environment...${NC}"
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to activate virtual environment.${NC}"
    exit 1
fi
echo -e "${GREEN}Virtual environment activated.${NC}"

# Install requirements
echo -e "\n${BLUE}Installing requirements...${NC}"
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to install requirements.${NC}"
    exit 1
fi
echo -e "${GREEN}Requirements installed.${NC}"

# Check if MongoDB is available
echo -e "\n${BLUE}Checking MongoDB connection...${NC}"
mongodb_running=false

# Get MongoDB URI from .env file if it exists
if [ -f ".env" ]; then
    source <(grep -v '^#' .env | sed -E 's/(.*)=.*/export \1/')
fi

# Use default if not set
MONGO_URI=${MONGO_URI:-"mongodb://localhost:27017"}
DB_NAME=${DB_NAME:-"cryptopedia"}

# Try to connect to MongoDB
python3 -c "
import sys
from pymongo import MongoClient
try:
    client = MongoClient('$MONGO_URI', serverSelectionTimeoutMS=5000)
    client.server_info()
    sys.exit(0)
except Exception as e:
    print(f'MongoDB connection error: {e}')
    sys.exit(1)
"

if [ $? -eq 0 ]; then
    mongodb_running=true
    echo -e "${GREEN}MongoDB is running and accessible.${NC}"
else
    echo -e "${YELLOW}MongoDB connection failed. Checking if MongoDB is installed...${NC}"
    
    if command -v mongod &> /dev/null; then
        echo -e "${YELLOW}MongoDB is installed but not running. Starting MongoDB...${NC}"
        
        # Create data directory if it doesn't exist
        if [ ! -d "mongodb_data" ]; then
            mkdir -p mongodb_data
        fi
        
        # Start MongoDB in the background
        mongod --dbpath=./mongodb_data --port 27017 --fork --logpath=./mongodb.log
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}MongoDB started successfully.${NC}"
            mongodb_running=true
        else
            echo -e "${RED}Failed to start MongoDB. Please start it manually or install it.${NC}"
            echo -e "${YELLOW}You can install MongoDB by following instructions at:${NC}"
            echo -e "${YELLOW}https://www.mongodb.com/docs/manual/installation/${NC}"
        fi
    else
        echo -e "${RED}MongoDB is not installed. Please install MongoDB or provide a valid MONGO_URI in .env file.${NC}"
        echo -e "${YELLOW}You can install MongoDB by following instructions at:${NC}"
        echo -e "${YELLOW}https://www.mongodb.com/docs/manual/installation/${NC}"
    fi
fi

# Create/update .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo -e "\n${BLUE}Creating .env file...${NC}"
    cat > .env << EOL
# Database Configuration
MONGO_URI=mongodb://localhost:27017
DB_NAME=cryptopedia

# JWT Configuration
JWT_SECRET=$(openssl rand -hex 32)

# Storage Configuration
STORAGE_TYPE=local
MEDIA_FOLDER=media

# Optional External Services (set to false to use local alternatives)
USE_ELASTICSEARCH=false
USE_REDIS=false
EOL
    echo -e "${GREEN}.env file created with default configuration.${NC}"
else
    echo -e "${GREEN}Using existing .env file.${NC}"
fi

# Initialize Cryptopedia
echo -e "\n${BLUE}Initializing Cryptopedia...${NC}"
if [ "$mongodb_running" = true ]; then
    python3 init_cryptopedia.py
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to initialize Cryptopedia.${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}Skipping initialization because MongoDB is not available.${NC}"
    echo -e "${YELLOW}Please set up MongoDB before running Cryptopedia.${NC}"
fi

# Setup complete
echo -e "\n${GREEN}✅ Cryptopedia setup complete!${NC}"
echo -e "\n${BLUE}====================================================${NC}"
echo -e "${BLUE}                   NEXT STEPS                       ${NC}"
echo -e "${BLUE}====================================================${NC}"
echo -e "${GREEN}To start Cryptopedia, run:${NC}"
echo -e "  ${YELLOW}source venv/bin/activate${NC}"
echo -e "  ${YELLOW}uvicorn main:app --reload --host 0.0.0.0 --port 8000${NC}"
echo -e "\n${GREEN}Then open a web browser and go to:${NC}"
echo -e "  ${YELLOW}http://localhost:8000${NC}"
echo -e "\n${GREEN}Default admin login:${NC}"
echo -e "  ${YELLOW}Username: admin${NC}"
echo -e "  ${YELLOW}Password: admin123${NC}"
echo -e "${RED}Remember to change the admin password after first login!${NC}"

echo -e "\n${BLUE}Would you like to start Cryptopedia now? (y/n)${NC}"
read -r start_now

if [[ $start_now == "y" || $start_now == "Y" ]]; then
    echo -e "\n${BLUE}Starting Cryptopedia...${NC}"
    uvicorn main:app --reload --host 0.0.0.0 --port 8000
else
    echo -e "\n${GREEN}You can start Cryptopedia later using the commands above.${NC}"
fi
