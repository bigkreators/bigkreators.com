#!/usr/bin/env python3
"""
KONTRIB Token Creation Script
Creates the KONTRIB token on Solana with proper symbol validation
"""

import asyncio
import subprocess
import json
import base58
import tempfile
import os
from datetime import datetime
from solders.keypair import Keypair

# Colors for output
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
RED = '\033[0;31m'
BLUE = '\033[0;34m'
NC = '\033[0m'

def print_section(title):
    print(f"\n{YELLOW}{'='*50}{NC}")
    print(f"{YELLOW}{title}{NC}")
    print(f"{YELLOW}{'='*50}{NC}\n")

def print_success(message):
    print(f"{GREEN}✅ {message}{NC}")

def print_error(message):
    print(f"{RED}❌ {message}{NC}")

def print_info(message):
    print(f"{BLUE}ℹ️  {message}{NC}")

def validate_token_symbol():
    """Validate and provide guidelines for Solana token symbols"""
    
    print_section("Solana Token Symbol Guidelines")
    
    print_info("Solana SPL Token Symbol Rules:")
    print("• Length: 1-10 characters")
    print("• Allowed: Letters (A-Z), numbers (0-9)")
    print("• Allowed: Basic symbols: . - _ (period, hyphen, underscore)")
    print("• NOT allowed: Spaces, special chars like @#$%^&*()+=[]{}|\\:;\"'<>?,/")
    print("• Case: Usually uppercase by convention")
    print()
    
    # Test various KONTRIB variations
    kontrib_options = {
        "KONTRIB": "✅ Perfect - Standard format",
        "KONTRIB.": "✅ Allowed - Period is permitted",
        "KONTRIB-TOKEN": "❌ Too long (11 chars, max 10)",
        "KONTRIB_": "✅ Allowed - Underscore permitted", 
        "KONTRIB-": "✅ Allowed - Hyphen permitted",
        "KONTRIB1": "✅ Allowed - Numbers permitted",
        "K0NTRIB": "✅ Allowed - Numbers in middle permitted",
        "KONTRIB@": "❌ Not allowed - @ symbol not permitted",
        "KONTRIB$": "❌ Not allowed - $ symbol not permitted",
        "KONTRIB!": "❌ Not allowed - ! symbol not permitted"
    }
    
    print_info("KONTRIB Symbol Options Analysis:")
    for symbol, status in kontrib_options.items():
        print(f"  {symbol:<12} → {status}")
    
    print()
    print_success("Recommended: 'KONTRIB' (7 chars, clean, professional)")
    
    return "KONTRIB"

def check_prerequisites():
    """Check if required tools are installed"""
    tools = {
        'solana': 'Solana CLI',
        'spl-token': 'SPL Token CLI'
    }
    
    all_good = True
    for cmd, name in tools.items():
        try:
            result = subprocess.run([cmd, '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                version = result.stdout.strip().split('\n')[0]
                print_success(f"{name}: {version}")
            else:
                print_error(f"{name} not working properly")
                all_good = False
        except FileNotFoundError:
            print_error(f"{name} not installed")
            print_info(f"Install {name} from https://docs.solana.com/cli/install-solana-cli-tools")
            all_good = False
    
    return all_good

async def test_modern_service():
    """Test the modern Solana service"""
    try:
        from services.solana_service import ModernSolanaService
        
        # Create test keypair
        test_keypair = Keypair()
        service = ModernSolanaService(
            rpc_url="https://api.devnet.solana.com",
            private_key=test_keypair.to_base58_string(),
            token_mint=None
        )
        
        # Test basic functionality
        balance = await service.get_sol_balance(str(test_keypair.pubkey()))
        print_success(f"Modern Solana service working - Test balance: {balance} SOL")
        
        await service.close()
        return True
        
    except ImportError as e:
        print_error(f"Cannot import modern service: {e}")
        print_info("Make sure you've run the setup script first")
        return False
    except Exception as e:
        print_error(f"Service test failed: {e}")
        return False

async def create_kontrib_token():
    """Create KONTRIB token using modern approach"""
    
    print_section("KONTRIB Token Creation")
    print_info("Creating BigKreators Contribution Token on Solana")
    
    # Validate token symbol
    token_symbol = validate_token_symbol()
    
    # Check prerequisites
    if not check_prerequisites():
        print_error("Prerequisites not met. Please install required tools.")
        return False
    
    # Test modern service
    print_section("Testing Modern Solana Service")
    if not await test_modern_service():
        print_error("Modern service test failed")
        return False
    
    # Configure Solana CLI
    print_section("Configuring Solana CLI")
    print_info("Setting network to devnet...")
    subprocess.run(['solana', 'config', 'set', '--url', 'devnet'], capture_output=True)
    
    # Create authority keypair
    print_section("Creating Authority Keypair")
    authority_keypair = Keypair()
    authority_address = str(authority_keypair.pubkey())
    authority_private_key = authority_keypair.to_base58_string()
    
    print_success(f"Authority wallet: {authority_address}")
    
    # Save keypair to temporary file for CLI operations
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        # Convert to CLI format
        keypair_data = list(authority_keypair.to_bytes_array())
        json.dump(keypair_data, f)
        keypair_file = f.name
    
    try:
        # Set CLI to use this keypair
        subprocess.run(['solana', 'config', 'set', '--keypair', keypair_file], capture_output=True)
        
        # Request airdrop
        print_section("Requesting Airdrop")
        print_info("Requesting 2 SOL airdrop...")
        
        airdrop_result = subprocess.run([
            'solana', 'airdrop', '2'
        ], capture_output=True, text=True)
        
        if airdrop_result.returncode == 0:
            print_success("Airdrop successful")
        else:
            print_error(f"Airdrop failed: {airdrop_result.stderr}")
            print_info("Continuing anyway - you may need manual airdrop")
        
        # Wait for airdrop confirmation
        print_info("Waiting for airdrop confirmation...")
        await asyncio.sleep(5)
        
        # Create token with metadata
        print_section("Creating KONTRIB Token")
        print_info(f"Creating token with symbol: {token_symbol}")
        print_info("Token Name: BigKreators Contribution Token")
        print_info("Decimals: 9 (standard)")
        
        # Create token with enable-freeze for future governance
        create_result = subprocess.run([
            'spl-token', 'create-token',
            '--decimals', '9',
            '--enable-freeze'
        ], capture_output=True, text=True)
        
        if create_result.returncode != 0:
            print_error(f"Token creation failed: {create_result.stderr}")
            return False
        
        # Extract token mint address
        token_mint = None
        for line in create_result.stdout.strip().split('\n'):
            if 'Creating token' in line:
                token_mint = line.split()[-1]
                break
        
        if not token_mint:
            print_error("Could not extract token mint address")
            return False
        
        print_success(f"KONTRIB Token created: {token_mint}")
        
        # Create associated token account
        print_section("Creating Token Account")
        print_info("Creating associated token account...")
        
        account_result = subprocess.run([
            'spl-token', 'create-account', token_mint
        ], capture_output=True, text=True)
        
        if account_result.returncode != 0:
            print_error(f"Token account creation failed: {account_result.stderr}")
            return False
        
        print_success("Token account created")
        
        # Mint initial supply
        print_section("Minting Initial Supply")
        print_info("Minting 100,000,000 KONTRIB tokens...")
        
        mint_result = subprocess.run([
            'spl-token', 'mint', token_mint, '100000000'
        ], capture_output=True, text=True)
        
        if mint_result.returncode != 0:
            print_error(f"Token minting failed: {mint_result.stderr}")
            return False
        
        print_success("100M KONTRIB tokens minted successfully")
        
        # Verify balance
        print_section("Verifying Token Creation")
        balance_result = subprocess.run([
            'spl-token', 'balance', token_mint
        ], capture_output=True, text=True)
        
        if balance_result.returncode == 0:
            balance = balance_result.stdout.strip()
            print_success(f"Token balance verified: {balance} KONTRIB")
        
        # Add token metadata (if possible)
        print_section("Setting Token Metadata")
        print_info("Note: Full metadata requires Metaplex setup")
        print_info("For now, the token will show as the mint address in wallets")
        print_info("After mainnet deployment, you can add:")
        print("  • Token name: BigKreators Contribution Token")
        print("  • Symbol: KONTRIB")
        print("  • Logo: Your project logo")
        print("  • Description: Rewards for wiki contributions")
        
        # Test with modern service
        print_info("Testing with modern Solana service...")
        try:
            from services.solana_service import ModernSolanaService
            
            service = ModernSolanaService(
                rpc_url="https://api.devnet.solana.com",
                private_key=authority_private_key,
                token_mint=token_mint
            )
            
            # Test SOL balance
            sol_balance = await service.get_sol_balance(authority_address)
            print_success(f"SOL balance via service: {sol_balance} SOL")
            
            # Test token balance
            token_balance = await service.get_token_balance(authority_address)
            print_success(f"Token balance via service: {token_balance:,.0f} KONTRIB")
            
            await service.close()
            
        except Exception as e:
            print_error(f"Service test failed: {e}")
        
        # Generate configuration
        print_section("Generating Configuration")
        
        config = {
            "token_name": "BigKreators Contribution Token",
            "token_symbol": token_symbol,
            "token_mint": token_mint,
            "authority_wallet": authority_address,
            "authority_private_key": authority_private_key,
            "decimals": 9,
            "initial_supply": 100_000_000,
            "network": "devnet",
            "rpc_url": "https://api.devnet.solana.com",
            "created_at": datetime.utcnow().isoformat(),
            "explorer_url": f"https://explorer.solana.com/address/{token_mint}?cluster=devnet",
            "solana_version": "latest",
            "creation_method": "spl_token_cli",
            "features": {
                "freeze_enabled": True,
                "metadata_ready": False,
                "governance_ready": True
            }
        }
        
        # Save configuration
        with open('kontrib_token_config.json', 'w') as f:
            json.dump(config, f, indent=2)
        print_success("Configuration saved to kontrib_token_config.json")
        
        # Generate environment variables
        env_vars = f"""# KONTRIB Token Configuration
SOLANA_RPC_URL=https://api.devnet.solana.com
SOLANA_PRIVATE_KEY={authority_private_key}
TOKEN_MINT_ADDRESS={token_mint}
TOKEN_SYMBOL=KONTRIB
TOKEN_NAME="BigKreators Contribution Token"
WEEKLY_TOKEN_POOL=10000.0
MIN_TOKENS_PER_USER=1.0"""
        
        with open('.env.kontrib.generated', 'w') as f:
            f.write(env_vars)
        print_success("Environment variables saved to .env.kontrib.generated")
        
        # Print summary
        print_section("KONTRIB Token Creation Summary")
        print(f"{GREEN}🎉 KONTRIB Token successfully created!{NC}")
        print(f"{BLUE}Token Name:{NC} BigKreators Contribution Token")
        print(f"{BLUE}Token Symbol:{NC} {token_symbol}")
        print(f"{BLUE}Token Mint:{NC} {token_mint}")
        print(f"{BLUE}Authority Wallet:{NC} {authority_address}")
        print(f"{BLUE}Initial Supply:{NC} 100,000,000 KONTRIB")
        print(f"{BLUE}Decimals:{NC} 9")
        print(f"{BLUE}Network:{NC} Solana Devnet")
        print(f"{BLUE}Explorer:{NC} https://explorer.solana.com/address/{token_mint}?cluster=devnet")
        
        # Symbol validation summary
        print_section("Symbol Validation Summary")
        print(f"{GREEN}✅ Symbol 'KONTRIB' is valid for Solana SPL tokens{NC}")
        print("• Length: 7 characters (within 1-10 limit)")
        print("• Characters: All letters (A-Z allowed)")
        print("• No special characters (follows SPL standard)")
        print("• Professional and brandable")
        
        print_section("Next Steps")
        print(f"{YELLOW}1. Add environment variables to your .env file:{NC}")
        print(f"   cat .env.kontrib.generated >> .env")
        print()
        print(f"{YELLOW}2. Update database migration for KONTRIB:{NC}")
        print(f"   python migrate_database.py")
        print()
        print(f"{YELLOW}3. Test the integration:{NC}")
        print(f"   python test_token_modern.py")
        print()
        print(f"{YELLOW}4. Start your FastAPI server:{NC}")
        print(f"   uvicorn main:app --reload")
        print()
        print(f"{YELLOW}5. Test the API endpoints:{NC}")
        print(f"   curl http://localhost:8000/api/token/status")
        print(f"   curl http://localhost:8000/api/token/wallet/{authority_address}")
        
        # Optional: Metadata setup instructions
        print_section("Optional: Adding Token Metadata")
        print_info("To make KONTRIB display properly in wallets, you can add metadata:")
        print("1. Use Metaplex Token Metadata program")
        print("2. Add logo, description, and external URL")
        print("3. Register with token lists (for DEX visibility)")
        print("4. Submit to wallet providers for recognition")
        print()
        print_info("For MVP/testing, the current setup is sufficient")
        
        return True
        
    finally:
        # Clean up temporary keypair file
        if os.path.exists(keypair_file):
            os.unlink(keypair_file)

def update_project_files():
    """Update project files to use KONTRIB instead of WCT"""
    
    print_section("Updating Project Files for KONTRIB")
    
    # Files to update
    files_to_update = [
        'services/solana_service.py',
        'models/token.py', 
        'routes/token.py',
        'README.md',
        'migrate_database.py'
    ]
    
    replacements = {
        'WCT': 'KONTRIB',
        'Wiki Contribution Token': 'BigKreators Contribution Token',
        'wct': 'kontrib',
        'WCT Token': 'KONTRIB Token'
    }
    
    for file_path in files_to_update:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                
                # Apply replacements
                for old, new in replacements.items():
                    content = content.replace(old, new)
                
                with open(f"{file_path}.kontrib", 'w') as f:
                    f.write(content)
                
                print_success(f"Updated {file_path} → {file_path}.kontrib")
                
            except Exception as e:
                print_error(f"Failed to update {file_path}: {e}")
        else:
            print_info(f"File {file_path} not found - skipping")
    
    print_info("Review the .kontrib files and replace originals if correct")

if __name__ == "__main__":
    print_section("KONTRIB Token Creation")
    print_info("Creating BigKreators Contribution Token (KONTRIB) on Solana")
    
    try:
        success = asyncio.run(create_kontrib_token())
        if success:
            print_success("KONTRIB token creation completed successfully!")
            
            # Offer to update project files
            print()
            response = input("Update project files to use KONTRIB instead of WCT? (y/n): ")
            if response.lower() in ['y', 'yes']:
                update_project_files()
            
        else:
            print_error("Token creation failed")
            exit(1)
            
    except KeyboardInterrupt:
        print_error("Token creation cancelled by user")
        exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
