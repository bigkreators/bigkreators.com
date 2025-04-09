# Kryptopedia Project - Table of Contents v0.2

This document serves as a master table of contents for the Kryptopedia setup and configuration scripts.

## Installation and Setup Scripts

| Version | File | Description | Status |
|---------|------|-------------|--------|
| v0.1 | `install-dependencies.sh` | Installs all required dependencies including Python, MongoDB, Docker, and optionally Node.js | Complete |
| v0.1 | `setup-kryptopedia.sh` | Sets up local directories, configures environment settings, and seeds the database | Complete |
| v0.1 | `start-local.sh` | Starts Kryptopedia locally without Docker | Complete |
| v0.1 | `start-docker.sh` | Starts Kryptopedia using Docker and Docker Compose | Complete |

## Setup Process

The recommended setup process follows these steps:

1. Run `install-dependencies.sh` to install all required system dependencies
2. Run `setup-kryptopedia.sh` to configure the application and initialize the database
3. Choose one of the following to start the application:
   - `start-local.sh` for local deployment without containers
   - `start-docker.sh` for Docker-based deployment

## Default Admin Account

After installation, you can log in with the following default admin account:
- Username: `admin`
- Password: `admin123`

**Important:** Remember to change the default admin password after the first login.

## System Requirements

- Python 3.8+
- MongoDB 4.0+
- Docker and Docker Compose (for containerized deployment)
- Node.js (optional, for frontend development)

## Directory Structure

```
kryptopedia/
├── install-dependencies.sh   # Dependency installation script
├── setup-kryptopedia.sh      # Application setup script
├── start-local.sh            # Local startup script
├── start-docker.sh           # Docker-based startup script
├── main.py                   # Main application entry point
├── requirements.txt          # Python dependencies
├── docker-compose.yml        # Docker Compose configuration
├── Dockerfile                # Docker image definition
├── .env                      # Environment configuration
├── static/                   # Static files directory
├── templates/                # HTML templates directory
├── media/                    # Media uploads directory
└── mongodb_data/             # MongoDB data directory (local deployment)
```
