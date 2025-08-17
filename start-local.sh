#!/bin/bash
# File: ./start-local.sh

# Kryptopedia - Local Startup Script v0.4
# This script starts the Kryptopedia application locally (without Docker)
# Fixed python/pip aliases for systems using python3/pip3

# Set up aliases for python3/pip3 to work as python/pip in this script
shopt -s expand_aliases
alias python='python3'
alias pip='pip3'

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

# Function to load environment variables from .env file
load_env_file() {
    if [ -f ".env" ]; then
        echo -e "${YELLOW}Loading environment variables from .env file...${NC}"
        # Export variables from .env file (ignore comments and empty lines)
        set -a
        source .env
        set +a
        echo -e "${GREEN}Environment variables loaded.${NC}"
    else
        echo -e "${YELLOW}No .env file found. Creating default .env file...${NC}"
        create_default_env
    fi
}

# Function to create default .env file
create_default_env() {
    cat > .env << 'EOL'
# Database Configuration
MONGO_URI=mongodb://localhost:27017
DB_NAME=kryptopedia

# JWT Configuration
JWT_SECRET=your-secret-key-change-this-in-production

# Storage Configuration
STORAGE_TYPE=local
MEDIA_FOLDER=media

# Optional External Services (set to false to use local alternatives)
USE_ELASTICSEARCH=false
USE_REDIS=false
API_DEBUG=true
EOL
    echo -e "${GREEN}Default .env file created.${NC}"
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
        if command_exists mongod; then
            mongod --dbpath=./mongodb_data --port 27017 --fork --logpath=./mongodb.log
            
            if [ $? -ne 0 ]; then
                echo -e "${RED}Failed to start MongoDB.${NC}"
                echo -e "${YELLOW}Try running it manually: mongod --dbpath=./mongodb_data --port 27017${NC}"
                exit 1
            fi
            
            echo -e "${GREEN}MongoDB started successfully.${NC}"
        else
            echo -e "${YELLOW}MongoDB not found. Please install MongoDB or ensure it's running.${NC}"
            echo -e "${YELLOW}You can also use a remote MongoDB instance by updating MONGO_URI in .env${NC}"
        fi
    fi
}

# Check and setup virtual environment
setup_venv() {
    echo -e "\n${BLUE}Setting up Python environment...${NC}"
    
    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        echo -e "${YELLOW}Virtual environment not found. Creating one...${NC}"
        python -m venv venv
        
        if [ $? -ne 0 ]; then
            echo -e "${RED}Failed to create virtual environment.${NC}"
            echo -e "${YELLOW}Please ensure Python 3.8+ is installed.${NC}"
            exit 1
        fi
        
        echo -e "${GREEN}Virtual environment created.${NC}"
    fi
    
    # Activate virtual environment
    echo -e "${YELLOW}Activating virtual environment...${NC}"
    source venv/bin/activate
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to activate virtual environment.${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}Virtual environment activated.${NC}"
    
    # Check if uvicorn is installed in the virtual environment
    if ! command_exists uvicorn; then
        echo -e "${YELLOW}uvicorn not found. Installing dependencies...${NC}"
        install_dependencies
    else
        echo -e "${GREEN}uvicorn is available.${NC}"
    fi
}

# Install dependencies
install_dependencies() {
    echo -e "\n${BLUE}Installing Python dependencies...${NC}"
    
    # Upgrade pip first
    pip install --upgrade pip
    
    if [ -f "requirements.txt" ]; then
        echo -e "${YELLOW}Installing from requirements.txt...${NC}"
        pip install -r requirements.txt
    else
        echo -e "${YELLOW}requirements.txt not found. Installing core dependencies...${NC}"
        pip install fastapi uvicorn[standard] motor pydantic python-multipart python-dotenv python-jose[cryptography] passlib[bcrypt] aiofiles jinja2
    fi
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to install dependencies.${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}Dependencies installed successfully.${NC}"
}

# Check if required files exist
check_required_files() {
    echo -e "\n${BLUE}Checking required files...${NC}"
    
    missing_files=false
    
    if [ ! -f "main.py" ]; then
        echo -e "${RED}main.py not found. Please make sure you're in the correct directory.${NC}"
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
    
    # Create media directory if it doesn't exist
    if [ ! -d "media" ]; then
        echo -e "${YELLOW}Creating media directory...${NC}"
        mkdir -p media
    fi
    
    # Check if the app has been initialized before
    if [ ! -f ".initialized" ]; then
        echo -e "${YELLOW}First-time initialization...${NC}"
        
        # Check if setup-data.py exists and run it
        if [ -f "setup-data.py" ]; then
            echo -e "${YELLOW}Running database initialization...${NC}"
            python setup-data.py
        else
            echo -e "${YELLOW}No initialization script found (setup-data.py). Skipping database initialization.${NC}"
        fi
        
        touch .initialized
    else
        echo -e "${GREEN}Application already initialized.${NC}"
    fi
}

# Check if uvicorn is working properly
test_uvicorn() {
    echo -e "\n${BLUE}Testing uvicorn installation...${NC}"
    
    # Test if uvicorn can be imported
    python -c "import uvicorn; print('uvicorn version:', uvicorn.__version__)" 2>/dev/null
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}uvicorn is properly installed and working.${NC}"
        return 0
    else
        echo -e "${RED}uvicorn test failed. Reinstalling...${NC}"
        pip install --force-reinstall uvicorn[standard]
        return $?
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
    echo -e "${BLUE}Application will be available at: http://localhost:${PORT}${NC}"
    echo ""
    
    # Start the application using uvicorn with explicit path
    if command_exists uvicorn; then
        uvicorn main:app --host $HOST --port $PORT --reload
    else
        # Fallback: use python -m uvicorn
        echo -e "${YELLOW}Using python -m uvicorn as fallback...${NC}"
        python -m uvicorn main:app --host $HOST --port $PORT --reload
    fi
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to start the application.${NC}"
        echo -e "${YELLOW}Troubleshooting tips:${NC}"
        echo -e "${YELLOW}1. Make sure you're in the project directory${NC}"
        echo -e "${YELLOW}2. Check that main.py exists and contains a FastAPI app${NC}"
        echo -e "${YELLOW}3. Verify virtual environment is activated${NC}"
        echo -e "${YELLOW}4. Try running: python -c 'import main; print(main.app)'${NC}"
        exit 1
    fi
}

# Main function
main() {
    # Load environment variables from .env file
    load_env_file
    
    # Check required files
    check_required_files
    
    # Start MongoDB (if needed)
    start_mongodb
    
    # Setup and activate virtual environment
    setup_venv
    
    # Test uvicorn
    test_uvicorn
    
    # Initialize application
    initialize_app
    
    # Start the application
    start_application
}

# Cleanup function for graceful shutdown
cleanup() {
    echo -e "\n${YELLOW}Shutting down...${NC}"
    # Add any cleanup tasks here if needed
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Check if script is being sourced or executed
if [ "${BASH_SOURCE[0]}" == "${0}" ]; then
    # Script is being executed directly
    main "$@"
else
    # Script is being sourced
    echo -e "${YELLOW}Script is being sourced. Run 'main' to start the application.${NC}"
fi