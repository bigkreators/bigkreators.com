#!/bin/bash
# cleanup-old-files.sh
# This script backs up and cleans up the old monolithic structure before installing the new modular version

# Set colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== Kryptopedia - Cleanup Script ===${NC}"
echo -e "${YELLOW}This script will backup your old files and prepare for the new structure.${NC}"
echo -e "${RED}WARNING: This will move your current files to a backup folder.${NC}"

# Ask for confirmation
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    echo -e "${YELLOW}Operation cancelled.${NC}"
    exit 1
fi

# Create backup directory
BACKUP_DIR="kryptopedia_backup_$(date +"%Y%m%d_%H%M%S")"
mkdir -p "$BACKUP_DIR"

if [ ! -d "$BACKUP_DIR" ]; then
    echo -e "${RED}Failed to create backup directory. Aborting.${NC}"
    exit 1
fi

echo -e "${GREEN}Created backup directory: $BACKUP_DIR${NC}"

# Files and directories to backup
FILES_TO_BACKUP=(
    "main.py"
    "api_redirect.py"
    "deploy.sh"
    "docker-compose.yml"
    "Dockerfile"
    "requirements.txt"
    "LICENSE"
    "README.md"
    "FRONTEND.md"
    "STORAGE.md"
    "TOC.md"
    "BACKEND.md"
    ".gitignore"
    ".eslintrc.cjs"
    ".env"
)

DIRS_TO_BACKUP=(
    "templates"
    "static"
    "media"
    ".github"
)

# Backup individual files
for file in "${FILES_TO_BACKUP[@]}"; do
    if [ -f "$file" ]; then
        echo "Backing up $file..."
        cp "$file" "$BACKUP_DIR/"
    fi
done

# Backup directories
for dir in "${DIRS_TO_BACKUP[@]}"; do
    if [ -d "$dir" ]; then
        echo "Backing up directory $dir/..."
        cp -r "$dir" "$BACKUP_DIR/"
    fi
done

echo -e "${GREEN}Backup completed to $BACKUP_DIR${NC}"

# Clean up files that will be replaced
echo -e "${YELLOW}Cleaning up old files...${NC}"

# Files to delete (not directories, since they may contain user content)
FILES_TO_DELETE=(
    "main.py"
    "api_redirect.py"
)

for file in "${FILES_TO_DELETE[@]}"; do
    if [ -f "$file" ]; then
        echo "Removing $file..."
        rm "$file"
    fi
done

echo -e "${GREEN}Cleanup completed.${NC}"
echo -e "${YELLOW}Next, run the setup-directory-structure.sh script to create the new structure.${NC}"
