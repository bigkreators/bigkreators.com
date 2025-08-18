#!/usr/bin/env python3
"""
KONTRIB Token Creation Script - Simplified Version
Creates the KONTRIB token on Solana with proper token extraction
"""

import asyncio
import subprocess
import json
import base58
import tempfile
import os
import time
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
    """Validate token symbol"""
    print_section("Token Symbol Validation")
    print_success("Using symbol: 'KONTRIB' (7 chars, clean, professional)")
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
            all_good = False
    
    return all_good

async def create_kontrib_token():
    """Create KONTRIB token using simplified approach"""
    
    print_section("KONTRIB Token Creation - Simplified")
    print_info("Creating K̡̓ontrib Token on Solana Devnet")
    
    # Validate token symbol
    token_symbol = validate_token_symbol()
    
    # Check prerequisites
    if not check_prerequisites():
        print_error("Prerequisites not met. Please install required tools.")
        return False
    
    # Configure Solana CLI
    print_section("Configuring Solana CLI")
    print_info("Setting network to devnet...")
    subprocess.run(['solana', 'config', 'set', '--url', 'devnet'], capture_output=True)
    
    # Create authority keypair
    print_section("Creating Authority Keypair")
    authority_keypair = Keypair()
    authority_address = str(authority_keypair.pubkey())
    authority_private_key = base58.b58encode(bytes(authority_keypair)).decode('ascii')
    
    print_success(f"Authority wallet: {authority_address}")
    
    # Save keypair to file for CLI
    keypair_file = "kontrib-authority.json"
    with open(keypair_file, 'w') as f:
        keypair_bytes = bytes(authority_keypair)
        keypair_data = list(keypair_bytes)
        json.dump(keypair_data, f)
    
    print_info(f"Keypair saved to: {keypair_file}")
    
    try:
        # Set CLI to use this keypair
        subprocess.run(['solana', 'config', 'set', '--keypair', keypair_file], capture_output=True)
        
        # Request airdrop
        print_section("Requesting Airdrop")
        print_info("Requesting 2 SOL airdrop...")
        
        airdrop_result = subprocess.run([
            'solana', 'airdrop', '2', authority_address
        ], capture_output=True, text=True)
        
        if airdrop_result.returncode == 0:
            print_success("Airdrop successful")
        else:
            print_error(f"Airdrop failed: {airdrop_result.stderr}")
            print_info("Continuing anyway - you may need manual airdrop")
        
        # Wait for confirmation
        print_info("Waiting for airdrop confirmation...")
        time.sleep(5)
        
        # Create token - simplified command
        print_section("Creating KONTRIB Token")
        print_info(f"Creating token with symbol: {token_symbol}")
        print_info("Token Name: K̡̓ontrib")
        print_info("Decimals: 9 (standard)")
        
        # Use simpler token creation without extra flags first
        create_result = subprocess.run([
            'spl-token', 'create-token',
            '--decimals', '9'
        ], capture_output=True, text=True)
        
        if create_result.returncode != 0:
            print_error(f"Token creation failed: {create_result.stderr}")
            return False
        
        # Parse the output to get the actual token address
        print_info("Parsing token creation output...")
        print(f"Raw output: {create_result.stdout}")
        
        # The token address is usually after "Creating token " in the output
        token_mint = None
        lines = create_result.stdout.strip().split('\n')
        for line in lines:
            if 'Creating token ' in line:
                # Extract the address after "Creating token "
                parts = line.split('Creating token ')
                if len(parts) > 1:
                    token_mint = parts[1].strip()
                    break
        
        # Sometimes it's just on its own line as an address
        if not token_mint:
            for line in lines:
                line = line.strip()
                # Check if it looks like a base58 address (43-44 chars)
                if len(line) >= 43 and len(line) <= 44 and ' ' not in line:
                    # Make sure it's not the token program ID
                    if line != "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA":
                        token_mint = line
                        break
        
        if not token_mint:
            print_error("Could not extract token mint address from output")
            print_info("Please check the output above and manually copy the token address")
            return False
        
        print_success(f"KONTRIB Token created: {token_mint}")
        
        # Now mint the supply directly without creating a separate account
        print_section("Minting Initial Supply")
        print_info("Minting 100,000,000 KONTRIB tokens...")
        
        # Mint with --fund-recipient to auto-create account
        mint_result = subprocess.run([
            'spl-token', 'mint', token_mint, '100000000', '--fund-recipient'
        ], capture_output=True, text=True)
        
        if mint_result.returncode != 0:
            # Try without --fund-recipient flag
            print_info("Retrying mint without --fund-recipient...")
            mint_result = subprocess.run([
                'spl-token', 'mint', token_mint, '100000000'
            ], capture_output=True, text=True)
            
            if mint_result.returncode != 0:
                print_error(f"Token minting failed: {mint_result.stderr}")
                print_info(f"Token was created at: {token_mint}")
                print_info("You can try minting manually with:")
                print(f"  spl-token mint {token_mint} 100000000")
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
        
        # Generate configuration
        print_section("Generating Configuration")
        
        config = {
            "token_name": "K̡̓ontrib",
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
            "keypair_file": keypair_file
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
TOKEN_NAME="K̡̓ontrib"
WEEKLY_TOKEN_POOL=10000.0
MIN_TOKENS_PER_USER=1.0"""
        
        with open('.env.kontrib.generated', 'w') as f:
            f.write(env_vars)
        print_success("Environment variables saved to .env.kontrib.generated")
        
        # Print summary
        print_section("KONTRIB Token Creation Summary")
        print(f"{GREEN}🎉 KONTRIB Token successfully created!{NC}")
        print(f"{BLUE}Token Name:{NC} K̡̓ontrib")
        print(f"{BLUE}Token Symbol:{NC} {token_symbol}")
        print(f"{BLUE}Token Mint:{NC} {token_mint}")
        print(f"{BLUE}Authority Wallet:{NC} {authority_address}")
        print(f"{BLUE}Initial Supply:{NC} 100,000,000 KONTRIB")
        print(f"{BLUE}Decimals:{NC} 9")
        print(f"{BLUE}Network:{NC} Solana Devnet")
        print(f"{BLUE}Keypair File:{NC} {keypair_file}")
        print(f"{BLUE}Explorer:{NC} https://explorer.solana.com/address/{token_mint}?cluster=devnet")
        
        print_section("Next Steps")
        print(f"{YELLOW}1. Add environment variables to your .env file:{NC}")
        print(f"   cat .env.kontrib.generated >> .env")
        print()
        print(f"{YELLOW}2. Keep your keypair file safe:{NC}")
        print(f"   {keypair_file} contains your private key")
        print()
        print(f"{YELLOW}3. View your token on Solana Explorer:{NC}")
        print(f"   https://explorer.solana.com/address/{token_mint}?cluster=devnet")
        print()
        print(f"{YELLOW}4. Add metadata (logo, etc.):{NC}")
        print(f"   Upload logo to: static/images/kontrib/logo-512.png")
        print(f"   Create metadata.json with token info")
        
        return True
        
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return False

if __name__ == "__main__":
    print_section("KONTRIB Token Creation")
    print_info("Creating K̡̓ontrib Token (KONTRIB) on Solana")
    
    try:
        success = asyncio.run(create_kontrib_token())
        if success:
            print_success("\n✨ KONTRIB token creation completed successfully! ✨")
        else:
            print_error("\nToken creation failed. Check the errors above.")
    except KeyboardInterrupt:
        print()
        print_info("Operation cancelled by user")
    except Exception as e:
        print_error(f"Unexpected error: {e}")