#!/bin/bash

# Kryptopedia - Docker-based Startup Script v0.1
# This script starts the Kryptopedia application using Docker and Docker Compose

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}====================================================${NC}"
echo -e "${BLUE}     Kryptopedia - Docker-based Startup Script      ${NC}"
echo -e "${BLUE}====================================================${NC}"

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check Docker and Docker Compose
check_docker() {
    echo -e "\n${BLUE}Checking Docker installation...${NC}"
    
    if ! command_exists docker; then
        echo -e "${RED}Docker is not installed. Please run install-dependencies.sh first.${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}Docker is installed.${NC}"
    
    echo -e "\n${BLUE}Checking Docker Compose installation...${NC}"
    
    if ! command_exists docker-compose; then
        echo -e "${RED}Docker Compose is not installed. Please run install-dependencies.sh first.${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}Docker Compose is installed.${NC}"
    
    # Check if Docker daemon is running
    docker info > /dev/null 2>&1
    if [ $? -ne 0 ]; then
        echo -e "${RED}Docker daemon is not running. Please start Docker first.${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}Docker daemon is running.${NC}"
}

# Check if required files exist
check_required_files() {
    echo -e "\n${BLUE}Checking required files...${NC}"
    
    missing_files=false
    
    if [ ! -f "docker-compose.yml" ]; then
        echo -e "${RED}docker-compose.yml not found. Please make sure you're in the correct directory.${NC}"
        missing_files=true
    fi
    
    if [ ! -f "Dockerfile" ]; then
        echo -e "${RED}Dockerfile not found. Please make sure you're in the correct directory.${NC}"
        missing_files=true
    fi
    
    if [ "$missing_files" = true ]; then
        exit 1
    fi
    
    echo -e "${GREEN}All required files found.${NC}"
}

# Create .env file for Docker if it doesn't exist
setup_docker_env() {
    echo -e "\n${BLUE}Setting up environment for Docker...${NC}"
    
    if [ ! -f ".env" ]; then
        echo -e "${YELLOW}Creating .env file for Docker...${NC}"
        
        # Generate JWT secret
        JWT_SECRET=$(openssl rand -hex 32)
        
        cat > .env << EOL
# Database Configuration
MONGO_URI=mongodb://mongodb:27017
DB_NAME=kryptopedia

# JWT Configuration
JWT_SECRET=${JWT_SECRET}

# Storage Configuration
STORAGE_TYPE=local
MEDIA_FOLDER=media

# Optional External Services (set to false to use local alternatives)
USE_ELASTICSEARCH=false
USE_REDIS=false
EOL
        echo -e "${GREEN}.env file created for Docker.${NC}"
    else
        echo -e "${GREEN}.env file already exists.${NC}"
        
        # Check if MONGO_URI is set for Docker
        if grep -q "MONGO_URI=mongodb://localhost" .env; then
            echo -e "${YELLOW}Updating MONGO_URI in .env for Docker...${NC}"
            sed -i 's/MONGO_URI=mongodb:\/\/localhost/MONGO_URI=mongodb:\/\/mongodb/g' .env
            
            if [ $? -ne 0 ]; then
                echo -e "${YELLOW}Could not automatically update MONGO_URI. Please ensure it's set to:${NC}"
                echo -e "${YELLOW}MONGO_URI=mongodb://mongodb:27017${NC}"
            else
                echo -e "${GREEN}MONGO_URI updated for Docker.${NC}"
            fi
        fi
    fi
}

# Build Docker images
build_images() {
    echo -e "\n${BLUE}Building Docker images...${NC}"
    
    docker-compose build
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to build Docker images.${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}Docker images built successfully.${NC}"
}

# Start Docker containers
start_containers() {
    echo -e "\n${BLUE}Starting Docker containers...${NC}"
    
    # Check if containers are already running
    if docker-compose ps | grep -q "Up"; then
        echo -e "${YELLOW}Some containers are already running. Stopping them first...${NC}"
        docker-compose down
    fi
    
    # Start containers in detached mode
    docker-compose up -d
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to start Docker containers.${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}Docker containers started successfully.${NC}"
}

# Initialize application data
initialize_app() {
    echo -e "\n${BLUE}Initializing application data...${NC}"
    
    # Check if the app has been initialized before
    if [ ! -f ".docker_initialized" ]; then
        echo -e "${YELLOW}First-time initialization in Docker...${NC}"
        
        # Wait a bit for the database to be ready
        echo -e "${YELLOW}Waiting for MongoDB to be ready...${NC}"
        sleep 5
        
        # Run the initialization script inside the container
        echo -e "${YELLOW}Running database initialization script inside Docker...${NC}"
        docker-compose exec -T api python setup-data.sh
        
        if [ $? -ne 0 ]; then
            echo -e "${RED}Database initialization in Docker failed.${NC}"
            echo -e "${YELLOW}The application might still work if the database is already initialized.${NC}"
        else
            # Create the initialization marker file
            touch .docker_initialized
            echo -e "${GREEN}Application data initialized successfully in Docker.${NC}"
        fi
    else
        echo -e "${GREEN}Application data already initialized in Docker.${NC}"
    fi
}

# Show application access information
show_access_info() {
    echo -e "\n${BLUE}====================================================${NC}"
    echo -e "${GREEN}Kryptopedia is now running in Docker!${NC}"
    echo -e "${BLUE}====================================================${NC}"
    
    # Get the container ports
    API_PORT=$(docker-compose port api 8000 2>/dev/null | cut -d: -f2)
    if [ -z "$API_PORT" ]; then
        API_PORT=8000  # Default port if mapping couldn't be determined
    fi
    
    echo -e "${YELLOW}Access the application at:${NC} http://localhost:${API_PORT}"
    echo -e "${YELLOW}API Documentation at:${NC} http://localhost:${API_PORT}/docs"
    
    echo -e "\n${YELLOW}Default admin account:${NC}"
    echo -e "  Username: admin"
    echo -e "  Password: admin123"
    echo -e "${RED}Remember to change the default admin password after first login!${NC}"
    
    echo -e "\n${YELLOW}Docker container management commands:${NC}"
    echo -e "  View logs: ${GREEN}docker-compose logs -f${NC}"
    echo -e "  Stop containers: ${GREEN}docker-compose down${NC}"
    echo -e "  Restart containers: ${GREEN}docker-compose restart${NC}"
    echo -e "${BLUE}====================================================${NC}"
}

# Main function
main() {
    # Check Docker and Docker Compose
    check_docker
    
    # Check required files
    check_required_files
    
    # Setup environment for Docker
    setup_docker_env
    
    # Build Docker images
    build_images
    
    # Start Docker containers
    start_containers
    
    # Initialize application
    initialize_app
    
    # Show access information
    show_access_info
}

# Run the main function
main
