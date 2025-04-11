#!/bin/bash
# setup-directory-structure.sh
# This script creates the directory structure for the refactored Kryptopedia application

# Set colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== Kryptopedia - Directory Structure Setup ===${NC}"
echo -e "${YELLOW}This script will create the new directory structure for the refactored application.${NC}"

# Check if the directories already exist
if [ -d "models" ] || [ -d "routes" ] || [ -d "services" ] || [ -d "dependencies" ] || [ -d "utils" ]; then
    echo -e "${YELLOW}Some directories already exist. This may overwrite files.${NC}"
    read -p "Continue? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]
    then
        echo -e "${YELLOW}Operation cancelled.${NC}"
        exit 1
    fi
fi

# Create main directory structure
echo -e "${GREEN}Creating directory structure...${NC}"

# Create directories
mkdir -p models
mkdir -p routes
mkdir -p services/storage
mkdir -p services/cache
mkdir -p services/search
mkdir -p dependencies
mkdir -p utils
mkdir -p static
mkdir -p templates
mkdir -p media

# Create __init__.py files in each Python package directory
touch models/__init__.py
touch routes/__init__.py
touch services/__init__.py
touch services/storage/__init__.py
touch services/cache/__init__.py
touch services/search/__init__.py
touch dependencies/__init__.py
touch utils/__init__.py

# Ensure directory permissions are correct
chmod -R 755 models routes services dependencies utils

# Create empty placeholder files if they don't exist yet
touch config.py
touch main.py
touch setup-data.py
touch add-test-data.py
touch requirements.txt
touch README.md

# Create the .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Creating sample .env file...${NC}"
    cat > .env << EOL
# Database Configuration
MONGO_URI=mongodb://localhost:27017
DB_NAME=kryptopedia

# JWT Configuration
JWT_SECRET=$(openssl rand -hex 32)

# Storage Configuration
STORAGE_TYPE=local
MEDIA_FOLDER=media

# Optional External Services
USE_ELASTICSEARCH=false
USE_REDIS=false
API_DEBUG=true
EOL
fi

# Create .gitignore if it doesn't exist
if [ ! -f ".gitignore" ]; then
    echo -e "${YELLOW}Creating .gitignore file...${NC}"
    cat > .gitignore << EOL
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
ENV/

# Media files
media/

# MongoDB
mongodb_data/

# Environment variables
.env

# IDE
.idea/
.vscode/
*.swp
*.swo

# Logs
*.log
mongodb.log

# Backups
kryptopedia_backup_*/

# Docker
.docker/
EOL
fi

echo -e "${GREEN}Directory structure created successfully!${NC}"
echo -e "${YELLOW}Next steps:${NC}"
echo -e "1. Copy your refactored code files to their respective directories"
echo -e "2. Install dependencies with: pip install -r requirements.txt"
echo -e "3. Initialize the database with: python setup-data.py"
echo -e "4. Start the application with: python main.py"
