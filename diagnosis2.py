#!/usr/bin/env python3
"""
Kryptopedia Diagnostic Script

This script checks for common issues in the Kryptopedia application and suggests fixes.
"""
import os
import sys
import importlib.util
import subprocess
import requests
from pathlib import Path
from time import sleep
from urllib.parse import urlparse

# ANSI color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(message):
    """Print a formatted header."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 60}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD} {message} {Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 60}{Colors.END}\n")

def print_success(message):
    """Print a success message."""
    print(f"{Colors.GREEN}✓ {message}{Colors.END}")

def print_error(message):
    """Print an error message."""
    print(f"{Colors.RED}✗ {message}{Colors.END}")

def print_warning(message):
    """Print a warning message."""
    print(f"{Colors.WARNING}! {message}{Colors.END}")

def print_info(message):
    """Print an info message."""
    print(f"{Colors.BLUE}ℹ {message}{Colors.END}")

def check_python_version():
    """Check if Python version is compatible."""
    print_header("Checking Python Version")
    
    major, minor, _ = sys.version_info
    print_info(f"Found Python {major}.{minor}")
    
    if major < 3 or (major == 3 and minor < 8):
        print_error("Python 3.8 or higher is required.")
        print_info("Please upgrade your Python installation.")
        return False
    
    print_success("Python version is compatible.")
    return True

def check_dependencies():
    """Check if required Python packages are installed."""
    print_header("Checking Python Dependencies")
    
    required_packages = [
        'fastapi',
        'uvicorn',
        'motor',
        'pydantic',
        'python-multipart',
        'python-dotenv',
        'PyJWT',
        'bcrypt',
        'aiofiles',
        'jinja2'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        spec = importlib.util.find_spec(package)
        if spec is None:
            print_error(f"Package '{package}' is not installed.")
            missing_packages.append(package)
        else:
            print_success(f"Package '{package}' is installed.")
    
    if missing_packages:
        print_warning("Some required packages are missing.")
        cmd = f"pip install {' '.join(missing_packages)}"
        print_info(f"You can install them with: {cmd}")
        
        choice = input("Install missing packages now? (y/n): ")
        if choice.lower() == 'y':
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing_packages)
                print_success("Successfully installed missing packages.")
            except subprocess.CalledProcessError:
                print_error("Failed to install packages.")
                return False
    
    return True

def check_mongodb():
    """Check if MongoDB is running."""
    print_header("Checking MongoDB Connection")
    
    try:
        import motor.motor_asyncio
        import asyncio
        
        async def test_connection():
            try:
                client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://localhost:27017", serverSelectionTimeoutMS=2000)
                await client.server_info()
                print_success("MongoDB is running.")
                return True
            except Exception as e:
                print_error(f"MongoDB connection failed: {e}")
                print_info("Make sure MongoDB is installed and running.")
                return False
            
        return asyncio.run(test_connection())
    except ImportError:
        print_error("The motor package is not installed.")
        print_info("Install it with: pip install motor")
        return False

def check_directory_structure():
    """Check if required directories and files exist."""
    print_header("Checking Directory Structure")
    
    required_dirs = [
        "models",
        "routes",
        "services",
        "dependencies",
        "templates",
        "static",
        "utils",
        "media"
    ]
    
    for directory in required_dirs:
        if os.path.isdir(directory):
            print_success(f"Directory '{directory}' exists.")
        else:
            print_error(f"Directory '{directory}' is missing.")
            os.makedirs(directory, exist_ok=True)
            print_info(f"Created '{directory}' directory.")
    
    required_files = [
        "main.py",
        "config.py",
        "static/style.css",
        "templates/base.html"
    ]
    
    for file in required_files:
        if os.path.isfile(file):
            print_success(f"File '{file}' exists.")
        else:
            print_error(f"File '{file}' is missing.")
    
    return True

def check_server_running():
    """Check if the Kryptopedia server is running."""
    print_header("Checking Server Status")
    
    try:
        response = requests.get("http://localhost:8000", timeout=2)
        print_success(f"Server is running (Status code: {response.status_code}).")
        
        # Check if HTML is returned
        if "text/html" in response.headers.get("Content-Type", ""):
            print_success("Server is returning HTML content.")
        else:
            print_warning(f"Server is returning non-HTML content: {response.headers.get('Content-Type', 'unknown')}.")
        
        return True
    except requests.exceptions.ConnectionError:
        print_error("Server is not running or not accessible.")
        print_info("Start the server with: uvicorn main:app --reload")
        return False
    except requests.exceptions.Timeout:
        print_error("Server request timed out.")
        return False

def check_routes():
    """Check common routes to see if they're working."""
    print_header("Checking API Routes")
    
    if not check_server_running():
        print_warning("Skipping route checks as server is not running.")
        return False
    
    routes = [
        {"url": "/", "name": "Home page"},
        {"url": "/static/style.css", "name": "CSS file"},
        {"url": "/style.css", "name": "CSS redirect"},
        {"url": "/api/articles/", "name": "Articles API"},
        {"url": "/special/recentchanges", "name": "Recent changes page"},
        {"url": "/special/statistics", "name": "Statistics page"},
    ]
    
    for route in routes:
        try:
            response = requests.get(f"http://localhost:8000{route['url']}", timeout=2)
            if response.status_code == 200:
                print_success(f"Route '{route['name']}' ({route['url']}) is working.")
            else:
                print_error(f"Route '{route['name']}' ({route['url']}) returned status code {response.status_code}.")
                
                # For special pages, check if the templates exist
                if route['url'].startswith('/special/'):
                    page_name = route['url'].split('/')[-1]
                    template_path = f"templates/{page_name}.html"
                    
                    if not os.path.exists(template_path):
                        print_warning(f"Template '{template_path}' does not exist.")
                        print_info(f"Create {template_path} for this route to work.")
        except requests.exceptions.RequestException as e:
            print_error(f"Failed to access route '{route['name']}' ({route['url']}): {e}")
    
    return True

def fix_common_issues():
    """Fix some common issues automatically."""
    print_header("Fixing Common Issues")
    
    # Fix #1: Create .env file if missing
    if not os.path.exists(".env"):
        print_warning(".env file is missing. Creating default .env file.")
        
        with open(".env", "w") as f:
            f.write("""# Database Configuration
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
""")
        print_success("Created default .env file.")
    
    # Fix #2: Create empty __init__.py files if missing
    package_dirs = ["models", "routes", "services", "dependencies", "utils"]
    for directory in package_dirs:
        init_file = os.path.join(directory, "__init__.py")
        if os.path.isdir(directory) and not os.path.exists(init_file):
            print_warning(f"{init_file} is missing. Creating empty file.")
            with open(init_file, "w") as f:
                pass
            print_success(f"Created empty {init_file}.")
    
    # Fix #3: Create redirect rule for CSS if needed
    if os.path.exists("main.py"):
        with open("main.py", "r") as f:
            content = f.read()
        
        if "/style.css" not in content:
            print_warning("Missing redirect for /style.css in main.py.")
            print_info("Add the following route to main.py:")
            print("""
@app.get("/style.css")
async def redirect_to_css():
    \"\"\"
    Redirect /style.css to /static/style.css
    \"\"\"
    return RedirectResponse(url="/static/style.css")
""")
    
    return True

def main():
    """Main diagnostic function."""
    print_header("Kryptopedia Diagnostic Tool")
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Directory Structure", check_directory_structure),
        ("MongoDB Connection", check_mongodb),
        ("Routes", check_routes),
    ]
    
    results = {}
    
    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            print_error(f"Check '{name}' failed with an error: {e}")
            results[name] = False
    
    try:
        fix_common_issues()
    except Exception as e:
        print_error(f"Failed to fix common issues: {e}")
    
    # Print summary
    print_header("Diagnostic Summary")
    
    all_checks_passed = all(results.values())
    
    for name, result in results.items():
        if result:
            print_success(f"{name}: Passed")
        else:
            print_error(f"{name}: Failed")
    
    if all_checks_passed:
        print("\n" + Colors.GREEN + Colors.BOLD + "✓ All checks passed!" + Colors.END)
        print("Your Kryptopedia installation appears to be configured correctly.")
    else:
        print("\n" + Colors.RED + Colors.BOLD + "✗ Some checks failed." + Colors.END)
        print("Please fix the issues mentioned above.")
        
        print_info("\nCommon troubleshooting steps:")
        print_info("1. Make sure MongoDB is running")
        print_info("2. Check that all required packages are installed")
        print_info("3. Verify directory structure and required files")
        print_info("4. Restart the application with 'uvicorn main:app --reload'")
    
    return 0 if all_checks_passed else 1

if __name__ == "__main__":
    sys.exit(main())
