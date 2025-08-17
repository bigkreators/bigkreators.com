"""
Modern Solana service for token operations using Solana 0.36.7
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
from solders.address_lookup_table_account import AddressLookupTableAccount
from solders.system_program import transfer, TransferParams
from solders.instruction import Instruction

logger = logging.getLogger(__name__)

class ModernSolanaService:
    def __init__(self, rpc_url: str, private_key: str, token_mint: str = None):
        """
        Initialize modern Solana service
        
        Args:
            rpc_url: Solana RPC endpoint
            private_key: Base58 encoded private key for authority wallet
            token_mint: Token mint address (optional for initial setup)
        """
        self.client = AsyncClient(rpc_url)
        self.authority = Keypair.from_base58_string(private_key)
        self.token_mint = Pubkey.from_string(token_mint) if token_mint else None
        self.token_decimals = 9
        
    async def get_sol_balance(self, wallet_address: str) -> float:
        """Get SOL balance for a wallet"""
        try:
            wallet_pubkey = Pubkey.from_string(wallet_address)
            response = await self.client.get_balance(wallet_pubkey, commitment=Confirmed)
            return response.value / 1_000_000_000  # Convert lamports to SOL
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
            
            # Get token accounts by owner
            response = await self.client.get_token_accounts_by_owner(
                wallet_pubkey,
                {"mint": self.token_mint},
                commitment=Confirmed
            )
            
            if not response.value:
                return 0.0
            
            # Get balance of first token account
            token_account = response.value[0].pubkey
            balance_response = await self.client.get_token_account_balance(
                token_account, 
                commitment=Confirmed
            )
            
            if balance_response.value:
                raw_amount = int(balance_response.value.amount)
                return raw_amount / (10 ** self.token_decimals)
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Error getting token balance: {e}")
            return 0.0
    
    async def send_sol(self, recipient_address: str, amount: float) -> Optional[str]:
        """
        Send SOL to a recipient
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
            blockhash_response = await self.client.get_latest_blockhash(commitment=Finalized)
            recent_blockhash = blockhash_response.value.blockhash
            
            # Create message
            message = MessageV0.try_compile(
                payer=self.authority.pubkey(),
                instructions=[transfer_ix],
                address_lookup_table_accounts=[],
                recent_blockhash=recent_blockhash
            )
            
            # Create and sign transaction
            transaction = VersionedTransaction(message, [self.authority])
            
            # Send transaction
            response = await self.client.send_transaction(
                transaction,
                opts=TxOpts(
                    skip_preflight=False, 
                    preflight_commitment=Confirmed,
                    max_retries=3
                )
            )
            
            logger.info(f"SOL transfer successful: {response.value}")
            return str(response.value)
            
        except Exception as e:
            logger.error(f"Error sending SOL: {e}")
            return None
    
    async def create_spl_token(self, decimals: int = 9) -> Optional[Dict[str, Any]]:
        """
        Create a new SPL token using modern Solana libraries
        """
        try:
            # This is a simplified version - in practice you'd use spl-token library
            # For now, we'll return the structure for CLI creation
            return {
                "authority": str(self.authority.pubkey()),
                "decimals": decimals,
                "success": False,
                "message": "Use create_token_cli.py for token creation"
            }
            
        except Exception as e:
            logger.error(f"Error creating token: {e}")
            return None
    
    async def get_transaction_history(self, wallet_address: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get transaction history for a wallet
        """
        try:
            wallet_pubkey = Pubkey.from_string(wallet_address)
            
            # Get signatures for address
            response = await self.client.get_signatures_for_address(
                wallet_pubkey, 
                limit=limit,
                commitment=Confirmed
            )
            
            transactions = []
            for sig_info in response.value:
                transactions.append({
                    'signature': str(sig_info.signature),
                    'slot': sig_info.slot,
                    'block_time': sig_info.block_time,
                    'success': not sig_info.err,
                    'confirmation_status': 'confirmed'
                })
            
            return transactions
            
        except Exception as e:
            logger.error(f"Error getting transaction history: {e}")
            return []
    
    async def get_account_info(self, address: str) -> Optional[Dict[str, Any]]:
        """Get account information"""
        try:
            pubkey = Pubkey.from_string(address)
            response = await self.client.get_account_info(pubkey, commitment=Confirmed)
            
            if response.value:
                return {
                    "address": address,
                    "lamports": response.value.lamports,
                    "owner": str(response.value.owner),
                    "executable": response.value.executable,
                    "rent_epoch": response.value.rent_epoch
                }
            return None
            
        except Exception as e:
            logger.error(f"Error getting account info: {e}")
            return None
    
    async def airdrop_sol(self, amount: float = 1.0) -> Optional[str]:
        """Request SOL airdrop (devnet only)"""
        try:
            lamports = int(amount * 1_000_000_000)
            response = await self.client.request_airdrop(
                self.authority.pubkey(), 
                lamports
            )
            
            logger.info(f"Airdrop requested: {response.value}")
            return str(response.value)
            
        except Exception as e:
            logger.error(f"Error requesting airdrop: {e}")
            return None
    
    async def close(self):
        """Close the async client"""
        await self.client.close()
