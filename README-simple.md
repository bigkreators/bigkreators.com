# Kryptopedia Wiki

A simple wiki platform built with FastAPI and MongoDB.

## Installation and Running

### Step 1: Install

Run the installation script:

```bash
chmod +x install.sh
./install.sh
```

This will:
- Create a Python virtual environment
- Install all dependencies
- Set up MongoDB (if running)
- Initialize the wiki with sample content

### Step 2: Run

Start the wiki with:

```bash
chmod +x run.sh
./run.sh
```

This will:
- Start MongoDB if needed
- Start the FastAPI server
- Make the wiki available at http://localhost:8000

### Default Admin Account

- Username: admin
- Password: admin123

## Requirements

- Python 3.8+
- MongoDB

## Files and Structure

- `main.py` - The main FastAPI application
- `templates/` - HTML templates
- `static/` - CSS and JavaScript files
- `media/` - Uploaded files
- `install.sh` - Installation script
- `run.sh` - Run script
- `init_cryptopedia.py` - Database initialization

## Features

- Create and edit wiki articles
- User accounts and authentication
- File uploads
- Article categories and tags
- Search functionality
- Revision history
