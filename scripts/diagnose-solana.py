#!/usr/bin/env python3
"""
Diagnostic script to identify and fix Solana service loading issues
Run this script to check your configuration and identify problems
"""

import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Colors for output
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
NC = '\033[0m'  # No Color

def print_section(title):
    print(f"\n{BLUE}{'='*50}{NC}")
    print(f"{BLUE}{title}{NC}")
    print(f"{BLUE}{'='*50}{NC}")

def print_success(msg):
    print(f"{GREEN}✅ {msg}{NC}")

def print_warning(msg):
    print(f"{YELLOW}⚠️  {msg}{NC}")

def print_error(msg):
    print(f"{RED}❌ {msg}{NC}")

def print_info(msg):
    print(f"{BLUE}ℹ️  {msg}{NC}")

async def diagnose_solana_service():
    """Diagnose Solana service configuration issues"""
    
    print_section("Solana Service Diagnostic Tool")
    
    # Step 1: Check environment file
    print("\n1. Checking environment configuration...")
    
    env_file = Path(".env")
    if env_file.exists():
        print_success(".env file found")
        load_dotenv()
    else:
        print_error(".env file not found")
        print_info("Create a .env file in your project root")
    
    # Step 2: Check required environment variables
    print("\n2. Checking required environment variables...")
    
    required_vars = {
        "SOLANA_RPC_URL": os.getenv("SOLANA_RPC_URL"),
        "SOLANA_PRIVATE_KEY": os.getenv("SOLANA_PRIVATE_KEY"),
        "TOKEN_MINT_ADDRESS": os.getenv("TOKEN_MINT_ADDRESS"),
    }
    
    missing_vars = []
    for var_name, var_value in required_vars.items():
        if var_value:
            if var_name == "SOLANA_PRIVATE_KEY":
                print_success(f"{var_name}: [HIDDEN - {len(var_value)} chars]")
            else:
                print_success(f"{var_name}: {var_value}")
        else:
            print_error(f"{var_name}: Not set")
            missing_vars.append(var_name)
    
    # Step 3: Check Python dependencies
    print("\n3. Checking Python dependencies...")
    
    dependencies = {
        "solana": None,
        "solders": None,
        "base58": None,
        "httpx": None,
    }
    
    for dep in dependencies:
        try:
            module = __import__(dep)
            version = getattr(module, "__version__", "unknown")
            dependencies[dep] = version
            print_success(f"{dep}: {version}")
        except ImportError:
            print_error(f"{dep}: Not installed")
            dependencies[dep] = None
    
    # Step 4: Check service files
    print("\n4. Checking service files...")
    
    service_files = [
        "services/solana_service.py",
        "models/token.py",
        "routes/token.py",
        "config.py"
    ]
    
    missing_files = []
    for file_path in service_files:
        if Path(file_path).exists():
            print_success(f"{file_path}: Found")
        else:
            print_error(f"{file_path}: Missing")
            missing_files.append(file_path)
    
    # Step 5: Try to import and initialize service
    print("\n5. Testing service initialization...")
    
    if not missing_vars and all(dependencies.values()):
        try:
            # Try importing config
            import config
            print_success("Config module imported successfully")
            
            # Check which service is available
            service_imported = False
            service_class = None
            
            try:
                from services.solana_service import ModernSolanaService
                service_class = ModernSolanaService
                print_success("ModernSolanaService (Solana 0.36.7) imported")
                service_imported = True
            except ImportError as e:
                print_warning(f"ModernSolanaService not available: {e}")
                
                try:
                    from services.solana_service import SimplifiedSolanaService
                    service_class = SimplifiedSolanaService
                    print_success("SimplifiedSolanaService (fallback) imported")
                    service_imported = True
                except ImportError as e2:
                    print_error(f"SimplifiedSolanaService not available: {e2}")
            
            if service_imported and service_class:
                # Try to initialize service
                try:
                    service = service_class(
                        rpc_url=config.SOLANA_RPC_URL,
                        private_key=config.SOLANA_PRIVATE_KEY,
                        token_mint=getattr(config, 'TOKEN_MINT_ADDRESS', None)
                    )
                    print_success(f"Service initialized successfully")
                    
                    # Test basic functionality
                    if hasattr(service.authority, 'pubkey'):
                        authority_address = str(service.authority.pubkey())
                    else:
                        authority_address = str(service.authority.public_key)
                    
                    print_info(f"Authority wallet: {authority_address}")
                    
                    # Test RPC connection
                    try:
                        balance = await service.get_sol_balance(authority_address)
                        print_success(f"RPC connection working - Balance: {balance} SOL")
                    except Exception as e:
                        print_error(f"RPC connection failed: {e}")
                    
                    # Close connection if available
                    if hasattr(service, 'close'):
                        await service.close()
                    
                except Exception as e:
                    print_error(f"Service initialization failed: {e}")
            
        except ImportError as e:
            print_error(f"Failed to import required modules: {e}")
    else:
        print_warning("Skipping service test due to missing requirements")
    
    # Step 6: Generate fixes
    print_section("Recommended Fixes")
    
    if missing_vars:
        print("\n📝 Missing Environment Variables:")
        print("Add these to your .env file:")
        print()
        for var in missing_vars:
            if var == "SOLANA_RPC_URL":
                print(f"{var}=https://api.devnet.solana.com")
            elif var == "SOLANA_PRIVATE_KEY":
                print(f"{var}=YOUR_BASE58_ENCODED_PRIVATE_KEY")
            elif var == "TOKEN_MINT_ADDRESS":
                print(f"{var}=YOUR_TOKEN_MINT_ADDRESS")
    
    if any(dep is None for dep in dependencies.values()):
        print("\n📦 Missing Python Dependencies:")
        print("Install missing dependencies:")
        print()
        
        missing_deps = [dep for dep, version in dependencies.items() if version is None]
        
        if "solana" in missing_deps or "solders" in missing_deps:
            print("For modern setup (recommended):")
            print("pip install solana==0.36.7 solders==0.23.1")
            print()
            print("For simplified setup (if modern fails):")
            print("pip install solana==0.32.1")
        
        if "base58" in missing_deps:
            print("pip install base58==2.1.1")
        
        if "httpx" in missing_deps:
            print("pip install httpx==0.25.2")
    
    if missing_files:
        print("\n📁 Missing Files:")
        print("These files need to be created:")
        for file in missing_files:
            print(f"  - {file}")
        print()
        print("Run the appropriate setup script:")
        print("  bash token_backend_setup_preferred.sh  # For modern setup")
        print("  bash token_backend_setup_script.sh     # For simplified setup")
    
    # Step 7: Quick setup commands
    if missing_vars or missing_files:
        print_section("Quick Setup Commands")
        
        if not Path("kontrib_token_config.json").exists():
            print("\n1. Create your token (if not done yet):")
            print("   python create_token_modern.py  # or create_token_simple.py")
            print()
        
        print("2. Add environment variables from generated file:")
        print("   cat .env.kontrib.generated >> .env")
        print()
        
        print("3. Install dependencies:")
        print("   pip install -r requirements.txt")
        print()
        
        print("4. Test the service:")
        print("   python test_token_modern.py  # or test_token_simple.py")
        print()
        
        print("5. Start your server:")
        print("   uvicorn main:app --reload")
    else:
        print_success("\nYour Solana service appears to be configured correctly!")
        print_info("If you're still having issues, check the server logs for more details")

if __name__ == "__main__":
    asyncio.run(diagnose_solana_service())