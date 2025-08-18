"""
Token-related models for the BigKreators token system
"""
from models.base import DBModel, DateTimeModelMixin
from typing import Optional
from pydantic import Field, BaseModel
from datetime import datetime

class Contribution(DBModel, DateTimeModelMixin):
    """Model for tracking user contributions"""
    user_id: str = Field(..., description="User who made the contribution")
    article_id: str = Field(..., description="Article that was contributed to")
    type: str = Field(..., description="Type of contribution")
    base_points: int = Field(..., description="Base points for this contribution type")
    quality_multiplier: float = Field(1.0, description="Quality multiplier (0.5-3.0)")
    reputation_multiplier: float = Field(1.0, description="User reputation multiplier")
    demand_multiplier: float = Field(1.0, description="Content demand multiplier")
    total_points: int = Field(..., description="Total points after all multipliers")
    description: Optional[str] = Field(None, description="Description of contribution")

class TokenReward(DBModel, DateTimeModelMixin):
    """Model for individual token rewards"""
    user_id: str = Field(..., description="User receiving reward")
    week_start: datetime = Field(..., description="Start of reward week")
    week_end: datetime = Field(..., description="End of reward week")
    total_points: int = Field(..., description="Total points earned this week")
    token_amount: float = Field(..., description="Tokens awarded")
    transaction_signature: Optional[str] = Field(None, description="Blockchain transaction signature")
    status: str = Field("pending", description="Reward status")

class ContributionCreate(BaseModel):
    """Model for creating new contributions"""
    article_id: str = Field(..., description="Article ID")
    type: str = Field(..., description="Contribution type")
    description: Optional[str] = Field(None, description="Description")

class WalletInfo(BaseModel):
    """Model for wallet information"""
    address: str = Field(..., description="Wallet address")
    sol_balance: float = Field(0.0, description="SOL balance")
    token_balance: float = Field(0.0, description="Token balance")
    account_exists: bool = Field(True, description="Whether account exists")

class TokenSystemStatus(BaseModel):
    """Model for token system status"""
    status: str = Field(..., description="System status")
    network: str = Field(..., description="Solana network")
    authority_wallet: str = Field(..., description="Authority wallet address")
    authority_sol_balance: float = Field(0.0, description="Authority SOL balance")
    token_mint: Optional[str] = Field(None, description="Token mint address")
    rpc_url: str = Field(..., description="RPC URL")
