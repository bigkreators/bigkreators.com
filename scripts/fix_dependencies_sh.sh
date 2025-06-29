#!/bin/bash
# File: fix_dependencies.sh
# Script to fix MongoDB/BSON dependency conflicts in Kryptopedia
# Handles Anaconda Python 3.12 specific issues

set -e  # Exit on any error

echo "=== Kryptopedia Dependency Fix Script ==="
echo "Fixing ImportError: cannot import name '_get_object_size' from 'bson'"
echo "Detected Python environment: $(python3 --version)"
echo "Python path: $(which python3)"
echo ""

# Force create a clean virtual environment
echo "Creating a completely clean virtual environment..."

# Remove old virtual environment if it exists
if [ -d "venv" ]; then
    echo "Removing existing virtual environment..."
    rm -rf venv
fi

# Create fresh virtual environment
echo "Creating new isolated virtual environment..."
python3 -m venv venv --clear

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo "Virtual environment activated: $VIRTUAL_ENV"

# Verify we're using the venv python
echo "Using Python: $(which python)"
echo "Python version: $(python --version)"

# Upgrade pip and setuptools to latest versions
echo "Upgrading pip and setuptools..."
python -m pip install --upgrade pip setuptools wheel

# Completely remove any existing MongoDB-related packages
echo "Aggressively removing ALL MongoDB-related packages..."
python -m pip uninstall -y motor pymongo bson dnspython gridfs pymongo-auth || true

# Also remove any potential conflicting packages
echo "Removing potential conflicting packages..."
python -m pip uninstall -y blinker bson-py3 || true

# Clear ALL caches
echo "Clearing all pip caches..."
python -m pip cache purge || true

# Verify clean slate
echo "Verifying clean environment..."
python -c "
import sys
print(f'Python executable: {sys.executable}')
print(f'Python path: {sys.path}')
try:
    import motor
    print('ERROR: motor still found')
    exit(1)
except ImportError:
    print('✅ motor successfully removed')

try:
    import pymongo
    print('ERROR: pymongo still found') 
    exit(1)
except ImportError:
    print('✅ pymongo successfully removed')

try:
    import bson
    print('ERROR: bson still found')
    exit(1)
except ImportError:
    print('✅ bson successfully removed')
"

# Install packages in very specific order with exact versions
echo ""
echo "Installing packages in specific order with exact versions..."

# Step 1: Install dnspython first (required by pymongo)
echo "1. Installing dnspython..."
python -m pip install dnspython==2.4.2

# Step 2: Install pymongo with specific version that has working bson
echo "2. Installing pymongo with compatible bson..."
python -m pip install pymongo==4.6.1

# Step 3: Install motor that's compatible with this pymongo version
echo "3. Installing compatible motor..."
python -m pip install motor==3.3.2

# Step 4: Verify bson imports work
echo "4. Testing bson imports..."
python -c "
try:
    from bson import ObjectId
    from bson.raw_bson import RawBSONDocument
    from bson import _get_object_size, _raw_to_dict
    print('✅ All bson imports successful')
except ImportError as e:
    print(f'❌ bson import still failing: {e}')
    exit(1)
"

# Install other core dependencies
echo ""
echo "Installing other core dependencies..."
python -m pip install fastapi==0.104.1
python -m pip install "uvicorn[standard]==0.24.0"
python -m pip install pydantic==2.5.0
python -m pip install pydantic-settings==2.1.0

# Install authentication packages
echo "Installing authentication packages..."
python -m pip install "python-jose[cryptography]==3.3.0"
python -m pip install "passlib[bcrypt]==1.7.4"
python -m pip install python-multipart==0.0.6

# Install utility packages
echo "Installing utility packages..."
python -m pip install python-dotenv==1.0.0
python -m pip install jinja2==3.1.2
python -m pip install aiofiles==23.2.1

# Final comprehensive test
echo ""
echo "Running comprehensive MongoDB test..."
python -c "
print('Testing all MongoDB imports...')
try:
    # Test basic bson imports
    from bson import ObjectId, BSON
    from bson.raw_bson import RawBSONDocument
    from bson import _get_object_size, _raw_to_dict
    print('✅ BSON core imports successful')
    
    # Test pymongo imports
    from pymongo import MongoClient
    from pymongo.collection import ReturnDocument
    print('✅ PyMongo imports successful')
    
    # Test motor imports
    from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
    print('✅ Motor imports successful')
    
    # Test creating objects
    oid = ObjectId()
    print(f'✅ ObjectId creation successful: {oid}')
    
    # Show versions
    import motor, pymongo
    print(f'✅ Motor version: {motor.version}')
    print(f'✅ PyMongo version: {pymongo.version}')
    
    print('')
    print('🎉 ALL TESTS PASSED! MongoDB integration is working correctly.')
    
except ImportError as e:
    print(f'❌ IMPORT ERROR: {e}')
    print('')
    print('Debug information:')
    import sys
    print(f'Python executable: {sys.executable}')
    print(f'Python version: {sys.version}')
    
    # Check what packages are installed
    import pkg_resources
    installed = [d.project_name for d in pkg_resources.working_set]
    mongo_packages = [p for p in installed if any(x in p.lower() for x in ['mongo', 'bson', 'motor'])]
    print(f'Installed MongoDB-related packages: {mongo_packages}')
    exit(1)
except Exception as e:
    print(f'❌ UNEXPECTED ERROR: {e}')
    exit(1)
"

echo ""
if [ $? -eq 0 ]; then
    echo "=== FIX SUCCESSFUL ==="
    echo "MongoDB/BSON dependency conflict has been resolved!"
    echo ""
    echo "Your virtual environment is ready. To use it:"
    echo "  source venv/bin/activate"
    echo "  uvicorn main:app --reload"
    echo ""
    echo "IMPORTANT: Always activate the venv before running the app:"
    echo "  source venv/bin/activate"
else
    echo ""
    echo "=== FIX FAILED ==="
    echo "The automated fix couldn't resolve the issue."
    echo "This may require manual intervention - see the alternative solutions below."
    exit 1
fi