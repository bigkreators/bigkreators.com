"""
Test script for modern token integration (Solana 0.36.7)
"""
import asyncio
import os
from dotenv import load_dotenv

async def test_modern_integration():
    """Test the modern token integration"""
    
    print("🧪 Testing Modern Token Integration (Solana 0.36.7)")
    print("=" * 55)
    
    # Load environment variables
    load_dotenv()
    
    # Check environment variables
    rpc_url = os.getenv("SOLANA_RPC_URL")
    private_key = os.getenv("SOLANA_PRIVATE_KEY")
    token_mint = os.getenv("TOKEN_MINT_ADDRESS")
    
    print(f"RPC URL: {rpc_url or 'Not set'}")
    print(f"Private Key: {'Set' if private_key else 'Not set'}")
    print(f"Token Mint: {token_mint or 'Not set'}")
    print()
    
    if not all([rpc_url, private_key]):
        print("❌ Missing required environment variables")
        print("Run create_token_modern.py first, then add variables to .env")
        return False
    
    print("✅ Environment variables found")
    
    # Test modern Solana service
    try:
        from services.solana_service import ModernSolanaService
        
        service = ModernSolanaService(rpc_url, private_key, token_mint)
        print("✅ Modern Solana service initialized")
        
        # Test authority wallet info
        authority_address = str(service.authority.pubkey())
        print(f"✅ Authority wallet: {authority_address}")
        
        # Test SOL balance
        sol_balance = await service.get_sol_balance(authority_address)
        print(f"✅ SOL balance: {sol_balance} SOL")
        
        # Test token balance (if token mint is set)
        if token_mint:
            token_balance = await service.get_token_balance(authority_address)
            print(f"✅ Token balance: {token_balance} KONTRIB")
        else:
            print("ℹ️  Token mint not set - skipping token balance test")
        
        # Test account info
        account_info = await service.get_account_info(authority_address)
        if account_info:
            print(f"✅ Account info: {account_info['lamports']} lamports")
        
        # Test transaction history
        history = await service.get_transaction_history(authority_address, limit=3)
        print(f"✅ Transaction history: {len(history)} recent transactions")
        
        await service.close()
        print("✅ Service closed successfully")
        
        print("\n" + "="*55)
        print("🎉 All modern integration tests passed!")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you've run the setup script and installed dependencies")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_modern_integration())
    if not success:
        exit(1)
