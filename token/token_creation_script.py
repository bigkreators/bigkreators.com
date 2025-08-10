#!/usr/bin/env python3
"""
BigKreators KONTRIB Token Creation Script
Creates the Wiki Contribution Token on Solana devnet
"""

import asyncio
import base58
import json
import os
from datetime import datetime
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Confirmed
from spl.token.async_client import AsyncToken
from spl.token.constants import TOKEN_PROGRAM_ID
from spl.token.instructions import get_associated_token_address

# Colors for output
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
RED = '\033[0;31m'
BLUE = '\033[0;34m'
NC = '\033[0m'  # No Color

def print_section(title):
    """Print a section header"""
    print(f"\n{YELLOW}{'='*50}{NC}")
    print(f"{YELLOW}{title}{NC}")
    print(f"{YELLOW}{'='*50}{NC}\n")

def print_success(message):
    """Print success message"""
    print(f"{GREEN}✅ {message}{NC}")

def print_error(message):
    """Print error message"""
    print(f"{RED}❌ {message}{NC}")

def print_info(message):
    """Print info message"""
    print(f"{BLUE}ℹ️  {message}{NC}")

async def check_wallet_balance(client, wallet_pubkey):
    """Check SOL balance of a wallet"""
    try:
        balance = await client.get_balance(wallet_pubkey)
        sol_balance = balance.value / 1_000_000_000  # Convert lamports to SOL
        return sol_balance
    except Exception as e:
        print_error(f"Error checking balance: {e}")
        return 0

async def request_airdrop_if_needed(client, wallet_keypair, min_balance=1.0):
    """Request airdrop if wallet balance is too low"""
    balance = await check_wallet_balance(client, wallet_keypair.pubkey())
    
    if balance < min_balance:
        print_info(f"Wallet balance: {balance:.4f} SOL (need at least {min_balance} SOL)")
        print_info("Requesting airdrop...")
        
        try:
            airdrop_response = await client.request_airdrop(
                wallet_keypair.pubkey(), 
                int(2 * 1_000_000_000)  # 2 SOL
            )
            print_success(f"Airdrop requested: {airdrop_response.value}")
            
            # Wait for confirmation
            print_info("Waiting for airdrop confirmation...")
            await asyncio.sleep(10)
            
            new_balance = await check_wallet_balance(client, wallet_keypair.pubkey())
            print_success(f"New balance: {new_balance:.4f} SOL")
            
        except Exception as e:
            print_error(f"Airdrop failed: {e}")
            print_info("You may need to wait and try again, or use a faucet manually")
            return False
    else:
        print_success(f"Wallet balance: {balance:.4f} SOL")
    
    return True

async def create_kontrib_token():
    """Create the KONTRIB token on Solana devnet"""
    
    print_section("BigKreators KONTRIB Token Creation")
    print_info("This script will create the Wiki Contribution Token on Solana devnet")
    print_info("Token specs: 100M supply, 9 decimals, symbol: KONTRIB")
    
    # Connect to devnet
    print_info("Connecting to Solana devnet...")
    client = AsyncClient("https://api.devnet.solana.com")
    
    try:
        # Create authority keypair
        authority_keypair = Keypair()
        print_success(f"Authority wallet created: {authority_keypair.pubkey()}")
        
        # Check balance and request airdrop if needed
        airdrop_success = await request_airdrop_if_needed(client, authority_keypair)
        if not airdrop_success:
            print_error("Failed to get sufficient SOL for token creation")
            return None
        
        # Create token mint
        print_section("Creating Token Mint")
        mint_keypair = Keypair()
        
        print_info("Creating token mint...")
        
        # Create the token
        token = AsyncToken(
            conn=client,
            pubkey=mint_keypair.pubkey(),
            program_id=TOKEN_PROGRAM_ID,
            payer=authority_keypair
        )
        
        # Create mint account
        await token.create_mint(
            mint=mint_keypair,
            mint_authority=authority_keypair.pubkey(),
            decimals=9,
            freeze_authority=authority_keypair.pubkey()
        )
        
        token_mint = mint_keypair.pubkey()
        print_success(f"Token mint created: {token_mint}")
        
        # Create associated token account for authority
        print_section("Creating Token Account")
        print_info("Creating associated token account for authority...")
        
        authority_token_account = await token.create_associated_token_account(
            owner=authority_keypair.pubkey(),
            mint=token_mint
        )
        print_success(f"Authority token account: {authority_token_account}")
        
        # Mint initial supply
        print_section("Minting Initial Supply")
        initial_supply = 100_000_000 * (10 ** 9)  # 100M tokens with 9 decimals
        
        print_info(f"Minting {initial_supply // (10**9):,} KONTRIB tokens...")
        
        await token.mint_to(
            dest=authority_token_account,
            mint_authority=authority_keypair,
            amount=initial_supply
        )
        
        print_success(f"Minted {initial_supply // (10**9):,} KONTRIB tokens to authority")
        
        # Verify token creation
        print_section("Verifying Token Creation")
        
        # Check token account balance
        balance_response = await client.get_token_account_balance(authority_token_account)
        if balance_response.value:
            token_balance = int(balance_response.value.amount) / (10 ** 9)
            print_success(f"Token balance verified: {token_balance:,.0f} KONTRIB")
        
        # Get mint info
        mint_info = await client.get_account_info(token_mint)
        if mint_info.value:
            print_success("Token mint account verified")
        
        # Generate configuration
        print_section("Token Configuration")
        
        token_config = {
            "token_name": "Wiki Contribution Token",
            "token_symbol": "KONTRIB",
            "token_mint": str(token_mint),
            "authority_wallet": str(authority_keypair.pubkey()),
            "authority_private_key": base58.b58encode(authority_keypair.secret()).decode(),
            "authority_token_account": str(authority_token_account),
            "decimals": 9,
            "initial_supply": initial_supply // (10**9),
            "network": "devnet",
            "rpc_url": "https://api.devnet.solana.com",
            "created_at": datetime.utcnow().isoformat(),
            "explorer_url": f"https://explorer.solana.com/address/{token_mint}?cluster=devnet"
        }
        
        # Save configuration to file
        with open('kontrib_token_config.json', 'w') as f:
            json.dump(token_config, f, indent=2)
        
        print_success("Token configuration saved to kontrib_token_config.json")
        
        # Generate .env variables
        env_vars = f"""
# BigKreators KONTRIB Token Configuration
SOLANA_RPC_URL=https://api.devnet.solana.com
SOLANA_PRIVATE_KEY={base58.b58encode(authority_keypair.secret()).decode()}
TOKEN_MINT_ADDRESS={token_mint}
WEEKLY_TOKEN_POOL=10000.0
MIN_TOKENS_PER_USER=1.0
"""
        
        with open('.env.kontrib.generated', 'w') as f:
            f.write(env_vars.strip())
        
        print_success("Environment variables saved to .env.kontrib.generated")
        
        # Print summary
        print_section("Token Creation Summary")
        print(f"{GREEN}🎉 KONTRIB Token successfully created!{NC}")
        print(f"{BLUE}Token Mint:{NC} {token_mint}")
        print(f"{BLUE}Authority Wallet:{NC} {authority_keypair.pubkey()}")
        print(f"{BLUE}Initial Supply:{NC} {initial_supply // (10**9):,} KONTRIB")
        print(f"{BLUE}Explorer:{NC} https://explorer.solana.com/address/{token_mint}?cluster=devnet")
        
        print_section("Next Steps")
        print(f"{YELLOW}1. Add the following to your .env file:{NC}")
        print(f"   SOLANA_PRIVATE_KEY={base58.b58encode(authority_keypair.secret()).decode()}")
        print(f"   TOKEN_MINT_ADDRESS={token_mint}")
        print(f"   SOLANA_RPC_URL=https://api.devnet.solana.com")
        print()
        print(f"{YELLOW}2. Test the token integration:{NC}")
        print(f"   python test_token_integration.py")
        print()
        print(f"{YELLOW}3. Start your FastAPI server and test the endpoints:{NC}")
        print(f"   uvicorn main:app --reload")
        print(f"   curl http://localhost:8000/api/token/balance/{authority_keypair.pubkey()}")
        
        return token_config
        
    except Exception as e:
        print_error(f"Token creation failed: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    finally:
        await client.close()

async def main():
    """Main function"""
    try:
        config = await create_kontrib_token()
        if config:
            print_success("Token creation completed successfully!")
            return True
        else:
            print_error("Token creation failed")
            return False
    except KeyboardInterrupt:
        print_error("Token creation cancelled by user")
        return False
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
