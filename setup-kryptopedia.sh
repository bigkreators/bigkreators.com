#!/bin/bash

# Kryptopedia - Setup and Configuration Script v0.1
# This script sets up local directories, seeds the database, and 
# performs basic configuration for Kryptopedia

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}====================================================${NC}"
echo -e "${BLUE}       Kryptopedia - Setup and Configuration         ${NC}"
echo -e "${BLUE}====================================================${NC}"

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to generate a random secret key
generate_secret_key() {
    openssl rand -hex 32
}

# Check for required dependencies
check_dependencies() {
    echo -e "\n${BLUE}Checking for required dependencies...${NC}"
    
    if ! command_exists python3; then
        echo -e "${RED}Python 3 is not installed. Please run install-dependencies.sh first.${NC}"
        exit 1
    fi
    
    if ! command_exists pip3; then
        echo -e "${RED}pip3 is not installed. Please run install-dependencies.sh first.${NC}"
        exit 1
    fi
    
    if ! command_exists mongod; then
        echo -e "${RED}MongoDB is not installed. Please run install-dependencies.sh first.${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}All required dependencies are installed.${NC}"
}

# Create virtual environment and install Python requirements
setup_python_environment() {
    echo -e "\n${BLUE}Setting up Python virtual environment...${NC}"
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        echo -e "${YELLOW}Creating virtual environment...${NC}"
        python3 -m venv venv
        if [ $? -ne 0 ]; then
            echo -e "${RED}Failed to create virtual environment.${NC}"
            exit 1
        fi
    else
        echo -e "${GREEN}Virtual environment already exists.${NC}"
    fi
    
    # Activate virtual environment
    echo -e "${YELLOW}Activating virtual environment...${NC}"
    source venv/bin/activate
    
    # Install requirements
    echo -e "${YELLOW}Installing Python requirements...${NC}"
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to install requirements.${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}Python environment setup complete.${NC}"
}

# Create required directories
create_directories() {
    echo -e "\n${BLUE}Creating required directories...${NC}"
    
    # Create directories if they don't exist
    for dir in "static" "templates" "media" "mongodb_data"; do
        if [ ! -d "$dir" ]; then
            echo -e "${YELLOW}Creating $dir directory...${NC}"
            mkdir -p "$dir"
        else
            echo -e "${GREEN}$dir directory already exists.${NC}"
        fi
    done
    
    echo -e "${GREEN}All required directories created.${NC}"
}

# Check and start MongoDB
setup_mongodb() {
    echo -e "\n${BLUE}Setting up MongoDB...${NC}"
    
    # Check if MongoDB is running
    mongo_running=false
    if command_exists mongod; then
        if pgrep mongod > /dev/null; then
            mongo_running=true
            echo -e "${GREEN}MongoDB is already running.${NC}"
        else
            echo -e "${YELLOW}MongoDB is not running. Starting MongoDB...${NC}"
        fi
    fi
    
    # Start MongoDB if it's not running
    if [ "$mongo_running" = false ]; then
        if [ ! -d "mongodb_data" ]; then
            mkdir -p mongodb_data
        fi
        
        echo -e "${YELLOW}Starting MongoDB...${NC}"
        mongod --dbpath=./mongodb_data --port 27017 --fork --logpath=./mongodb.log
        
        if [ $? -ne 0 ]; then
            echo -e "${RED}Failed to start MongoDB. Please start it manually.${NC}"
            echo -e "${YELLOW}Command: mongod --dbpath=./mongodb_data --port 27017${NC}"
            exit 1
        fi
        
        echo -e "${GREEN}MongoDB started successfully.${NC}"
    fi
}

# Create or update .env file
setup_env_file() {
    echo -e "\n${BLUE}Setting up environment configuration...${NC}"
    
    # Create .env file if it doesn't exist
    if [ ! -f ".env" ]; then
        echo -e "${YELLOW}Creating .env file...${NC}"
        
        # Generate JWT secret
        JWT_SECRET=$(generate_secret_key)
        
        cat > .env << EOL
# Database Configuration
MONGO_URI=mongodb://localhost:27017
DB_NAME=cryptopedia

# JWT Configuration
JWT_SECRET=${JWT_SECRET}

# Storage Configuration
STORAGE_TYPE=local
MEDIA_FOLDER=media

# Optional External Services (set to false to use local alternatives)
USE_ELASTICSEARCH=false
USE_REDIS=false
EOL
        echo -e "${GREEN}.env file created.${NC}"
    else
        echo -e "${GREEN}.env file already exists.${NC}"
    fi
}

# Initialize database with demo content
seed_database() {
    echo -e "\n${BLUE}Initializing database with demo content...${NC}"
    
    # Check if the initialization script exists
    if [ -f "setup-data.sh" ]; then
        echo -e "${YELLOW}Running database initialization script...${NC}"
        python3 setup-data.sh
        
        if [ $? -ne 0 ]; then
            echo -e "${RED}Failed to initialize database.${NC}"
            exit 1
        fi
        
        echo -e "${GREEN}Database initialized successfully.${NC}"
    else
        echo -e "${RED}Database initialization script (setup-data.sh) not found.${NC}"
        echo -e "${YELLOW}You will need to set up the initial data manually.${NC}"
    fi
}

# Verify installation
verify_installation() {
    echo -e "\n${BLUE}Verifying installation...${NC}"
    
    # Check for essential components
    missing_components=false
    
    if [ ! -d "venv" ]; then
        echo -e "${RED}✗ Python virtual environment is missing.${NC}"
        missing_components=true
    else
        echo -e "${GREEN}✓ Python virtual environment exists.${NC}"
    fi
    
    if [ ! -f ".env" ]; then
        echo -e "${RED}✗ Environment configuration (.env) is missing.${NC}"
        missing_components=true
    else
        echo -e "${GREEN}✓ Environment configuration (.env) exists.${NC}"
    fi
    
    for dir in "static" "templates" "media"; do
        if [ ! -d "$dir" ]; then
            echo -e "${RED}✗ $dir directory is missing.${NC}"
            missing_components=true
        else
            echo -e "${GREEN}✓ $dir directory exists.${NC}"
        fi
    done
    
    # Verify MongoDB is running
    if pgrep mongod > /dev/null; then
        echo -e "${GREEN}✓ MongoDB is running.${NC}"
    else
        echo -e "${RED}✗ MongoDB is not running.${NC}"
        missing_components=true
    fi
    
    if [ "$missing_components" = true ]; then
        echo -e "\n${RED}Some components are missing. Please check the errors above.${NC}"
        return 1
    else
        echo -e "\n${GREEN}All components are installed correctly.${NC}"
        return 0
    fi
}

# Main setup process
main() {
    echo -e "\n${BLUE}Starting Kryptopedia setup...${NC}"
    
    # Check dependencies
    check_dependencies
    
    # Create directories
    create_directories
    
    # Setup MongoDB
    setup_mongodb
    
    # Setup Python environment
    setup_python_environment
    
    # Setup environment configuration
    setup_env_file
    
    # Seed database
    seed_database
    
    # Verify installation
    verify_installation
    
    if [ $? -eq 0 ]; then
        echo -e "\n${BLUE}====================================================${NC}"
        echo -e "${GREEN}Kryptopedia setup complete!${NC}"
        echo -e "${BLUE}====================================================${NC}"
        echo -e "${YELLOW}Next steps:${NC}"
        echo -e "1. Start Kryptopedia using start-local.sh (for local deployment) or"
        echo -e "   start-docker.sh (for Docker-based deployment)"
        echo -e "2. Access the application at http://localhost:8000"
        echo -e "\n${YELLOW}Default admin account:${NC}"
        echo -e "  Username: admin"
        echo -e "  Password: admin123"
        echo -e "${RED}Remember to change the default admin password after first login!${NC}"
        echo -e "${BLUE}====================================================${NC}"
    else
        echo -e "\n${RED}Kryptopedia setup failed. Please check the errors above.${NC}"
        exit 1
    fi
}

# Run the main function
main
