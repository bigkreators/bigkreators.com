"""
Solana service compatible with solana==0.36.7
Fixed to work without proxy parameter
"""
import asyncio
import json
from typing import List, Optional, Dict, Any
from decimal import Decimal
import logging
import base58

from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Confirmed, Finalized
from solana.rpc.types import TxOpts
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.transaction import VersionedTransaction
from solders.message import MessageV0
from solders.system_program import transfer, TransferParams
from solders.instruction import Instruction

logger = logging.getLogger(__name__)

class ModernSolanaService:
    def __init__(self, rpc_url: str, private_key: str, token_mint: str = None):
        """
        Initialize modern Solana service for v0.36.7
        
        Args:
            rpc_url: Solana RPC endpoint
            private_key: Base58 encoded private key for authority wallet
            token_mint: Token mint address (optional for initial setup)
        """
        # Initialize AsyncClient without proxy parameter (not supported in 0.36.7)
        self.client = AsyncClient(rpc_url)
        self.authority = Keypair.from_base58_string(private_key)
        self.token_mint = Pubkey.from_string(token_mint) if token_mint else None
        self.token_decimals = 9
        
    async def get_sol_balance(self, wallet_address: str) -> float:
        """Get SOL balance for a wallet"""
        try:
            wallet_pubkey = Pubkey.from_string(wallet_address)
            response = await self.client.get_balance(wallet_pubkey, commitment=Confirmed)
            
            # In v0.36.7, response has a 'value' attribute
            if hasattr(response, 'value'):
                return response.value / 1_000_000_000  # Convert lamports to SOL
            return 0.0
        except Exception as e:
            logger.error(f"Error getting SOL balance: {e}")
            return 0.0
    
    async def get_token_balance(self, wallet_address: str) -> float:
        """
        Get token balance for a wallet address
        """
        if not self.token_mint:
            logger.warning("Token mint not set")
            return 0.0
        
        try:
            wallet_pubkey = Pubkey.from_string(wallet_address)
            
            # Get token accounts for this wallet
            from solana.rpc.types import TokenAccountOpts
            
            opts = TokenAccountOpts(mint=self.token_mint)
            response = await self.client.get_token_accounts_by_owner(
                wallet_pubkey,
                opts,
                commitment=Confirmed
            )
            
            if hasattr(response, 'value') and response.value:
                # Parse the account data to get balance
                for account in response.value:
                    try:
                        # The account data contains the token balance
                        account_data = account.account.data
                        if account_data:
                            # Token account data structure:
                            # First 64 bytes contain mint and owner
                            # Next 8 bytes contain the amount
                            import struct
                            amount_bytes = account_data[64:72]
                            amount = struct.unpack('<Q', amount_bytes)[0]
                            return amount / (10 ** self.token_decimals)
                    except Exception as e:
                        logger.warning(f"Error parsing token account data: {e}")
                        continue
            
            return 0.0
            
        except Exception as e:
            logger.warning(f"Error getting token balance: {e}")
            return 0.0
    
    async def get_transaction_history(self, wallet_address: str, limit: int = 10) -> List[Dict]:
        """Get recent transactions for a wallet"""
        try:
            wallet_pubkey = Pubkey.from_string(wallet_address)
            
            # Get signatures for address
            response = await self.client.get_signatures_for_address(
                wallet_pubkey,
                limit=limit,
                commitment=Confirmed
            )
            
            transactions = []
            if hasattr(response, 'value'):
                for sig_info in response.value:
                    tx = {
                        "signature": str(sig_info.signature),
                        "slot": sig_info.slot,
                        "timestamp": sig_info.block_time,
                        "status": "success" if not sig_info.err else "failed",
                        "err": sig_info.err
                    }
                    transactions.append(tx)
            
            return transactions
            
        except Exception as e:
            logger.error(f"Error getting transaction history: {e}")
            return []
    
    async def send_sol(self, recipient_address: str, amount: float) -> Optional[str]:
        """
        Send SOL to another wallet
        
        Args:
            recipient_address: Recipient's wallet address
            amount: Amount of SOL to send
            
        Returns:
            Transaction signature if successful, None otherwise
        """
        try:
            recipient_pubkey = Pubkey.from_string(recipient_address)
            lamports = int(amount * 1_000_000_000)
            
            # Create transfer instruction
            transfer_ix = transfer(
                TransferParams(
                    from_pubkey=self.authority.pubkey(),
                    to_pubkey=recipient_pubkey,
                    lamports=lamports
                )
            )
            
            # Get recent blockhash
            recent_blockhash_resp = await self.client.get_latest_blockhash(commitment=Confirmed)
            recent_blockhash = recent_blockhash_resp.value.blockhash
            
            # Create message
            message = MessageV0.try_compile(
                payer=self.authority.pubkey(),
                instructions=[transfer_ix],
                address_lookup_table_accounts=[],
                recent_blockhash=recent_blockhash
            )
            
            # Create and sign transaction
            tx = VersionedTransaction(message, [self.authority])
            
            # Send transaction
            opts = TxOpts(preflight_commitment=Confirmed)
            result = await self.client.send_transaction(tx, opts=opts)
            
            if hasattr(result, 'value'):
                return str(result.value)
            
            return None
            
        except Exception as e:
            logger.error(f"Error sending SOL: {e}")
            return None
    
    async def close(self):
        """Close the RPC client connection"""
        try:
            await self.client.close()
        except Exception as e:
            logger.debug(f"Error closing client: {e}")
            pass

# Also create a simplified version as fallback
class SimplifiedSolanaService:
    """Simplified service that also works with 0.36.7"""
    def __init__(self, rpc_url: str, private_key: str, token_mint: str = None):
        self.client = AsyncClient(rpc_url)
        self.authority = Keypair.from_base58_string(private_key)
        self.token_mint = Pubkey.from_string(token_mint) if token_mint else None
        self.token_decimals = 9
    
    async def get_sol_balance(self, wallet_address: str) -> float:
        try:
            wallet_pubkey = Pubkey.from_string(wallet_address)
            response = await self.client.get_balance(wallet_pubkey, commitment=Confirmed)
            return response.value / 1_000_000_000 if hasattr(response, 'value') else 0.0
        except Exception as e:
            logger.error(f"Error getting SOL balance: {e}")
            return 0.0
    
    async def get_token_balance(self, wallet_address: str) -> float:
        # Simplified - returns 0 for now
        return 0.0
    
    async def get_transaction_history(self, wallet_address: str, limit: int = 10) -> List[Dict]:
        try:
            wallet_pubkey = Pubkey.from_string(wallet_address)
            response = await self.client.get_signatures_for_address(wallet_pubkey, limit=limit)
            
            transactions = []
            if hasattr(response, 'value'):
                for sig_info in response.value:
                    transactions.append({
                        "signature": str(sig_info.signature),
                        "slot": sig_info.slot,
                        "timestamp": sig_info.block_time,
                        "status": "success" if not sig_info.err else "failed"
                    })
            return transactions
        except Exception as e:
            logger.error(f"Error getting transaction history: {e}")
            return []
    
    async def send_sol(self, recipient_address: str, amount: float) -> Optional[str]:
        # Not implemented in simplified version
        return None
    
    async def close(self):
        try:
            await self.client.close()
        except:
            pass
