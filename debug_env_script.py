# File: debug_env.py
"""
Debug script to check .env file loading issues in Kryptopedia
"""
import os
import sys

def debug_env_loading():
    print("=== Kryptopedia Environment Debug ===\n")
    
    # Check current working directory
    print(f"Current working directory: {os.getcwd()}")
    
    # Check if .env file exists
    env_file = ".env"
    env_exists = os.path.exists(env_file)
    print(f".env file exists: {env_exists}")
    
    if env_exists:
        # Show .env file content
        print(f"\n.env file content:")
        print("-" * 40)
        try:
            with open(env_file, 'r') as f:
                content = f.read()
                print(content)
        except Exception as e:
            print(f"Error reading .env file: {e}")
        print("-" * 40)
    else:
        print("Creating a basic .env file...")
        with open(".env", "w") as f:
            f.write("""# Database Configuration
MONGO_URI=mongodb://localhost:27017
DB_NAME=kryptopedia

# JWT Configuration
JWT_SECRET=your-secret-key-change-this-in-production

# Storage Configuration
STORAGE_TYPE=local
MEDIA_FOLDER=media

# Optional External Services
USE_ELASTICSEARCH=false
USE_REDIS=false
API_DEBUG=true
""")
        print("Created .env file with default values.")
    
    # Check if python-dotenv is installed
    print(f"\nChecking python-dotenv installation...")
    try:
        import dotenv
        print("✓ python-dotenv is installed")
        try:
            # Try to get version, but don't fail if not available
            import pkg_resources
            version = pkg_resources.get_distribution("python-dotenv").version
            print(f"  Version: {version}")
        except:
            print("  Version: (unable to determine)")
    except ImportError:
        print("✗ python-dotenv is NOT installed")
        print("  Install it with: pip install python-dotenv")
        return False
    
    # Test loading .env file
    print(f"\nTesting .env file loading...")
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✓ load_dotenv() executed successfully")
    except Exception as e:
        print(f"✗ Error loading .env file: {e}")
        return False
    
    # Check specific environment variables
    print(f"\nChecking environment variables:")
    env_vars = ["MONGO_URI", "DB_NAME", "JWT_SECRET", "STORAGE_TYPE", "API_DEBUG"]
    
    for var in env_vars:
        value = os.getenv(var)
        if value:
            # Hide sensitive values
            if "SECRET" in var or "PASSWORD" in var:
                display_value = "***hidden***"
            else:
                display_value = value
            print(f"  {var}: {display_value}")
        else:
            print(f"  {var}: NOT SET")
    
    # Test the actual config import
    print(f"\nTesting config.py import...")
    try:
        sys.path.insert(0, os.getcwd())
        import config
        print("✓ config.py imported successfully")
        
        # Check if MONGO_URI is available
        if hasattr(config, 'MONGO_URI'):
            print(f"✓ config.MONGO_URI is available: {config.MONGO_URI}")
        else:
            print("✗ config.MONGO_URI is NOT available")
            
        if hasattr(config, 'DB_NAME'):
            print(f"✓ config.DB_NAME is available: {config.DB_NAME}")
        else:
            print("✗ config.DB_NAME is NOT available")
            
    except Exception as e:
        print(f"✗ Error importing config: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print(f"\n=== Debug Complete ===")
    return True

if __name__ == "__main__":
    debug_env_loading()