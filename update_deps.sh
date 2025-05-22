#!/bin/bash
# File: setup_dependencies.sh

echo "Setting up Kryptopedia dependencies..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install specific compatible versions
echo "Installing compatible MongoDB packages..."
pip install motor==3.3.2 pymongo==4.6.0

echo "Installing FastAPI and related packages..."
pip install fastapi==0.104.1 uvicorn[standard]==0.24.0

echo "Installing other dependencies..."
pip install python-dotenv==1.0.0 pydantic==2.5.0 jinja2==3.1.2 aiofiles==23.2.1

echo "Installing authentication packages..."
pip install python-jose[cryptography]==3.3.0 passlib[bcrypt]==1.7.4

echo "Installing development packages..."
pip install pytest==7.4.3 pytest-asyncio==0.21.1 httpx==0.25.2

echo "Dependencies installed successfully!"
echo "Activate the virtual environment with: source venv/bin/activate"

python3 -m venv venv_krypto
source venv_krypto/bin/activate 
pip install --upgrade pip
pip install motor==3.3.2 pymongo==4.6.0
pip install python-dotenv==1.0.0

python db_import_export.py stats
