from pydantic import BaseModel, Field
from typing import Optional, List, Dict


class GatewayWalletCredential(BaseModel):
    """Credentials for connecting a Gateway wallet"""
    chain: str = Field(description="Blockchain chain (e.g., 'solana', 'ethereum')")
    private_key: str = Field(description="Wallet private key")
    network: Optional[str] = Field(default=None, description="Network to use (defaults to chain's default)")


class GatewayWalletInfo(BaseModel):
    """Information about a connected Gateway wallet"""
    chain: str = Field(description="Blockchain chain")
    address: str = Field(description="Wallet address")
    network: str = Field(description="Network the wallet is configured for")


class GatewayBalanceRequest(BaseModel):
    """Request for Gateway wallet balances"""
    account_name: str = Field(description="Account name")
    chain: str = Field(description="Blockchain chain")
    tokens: Optional[List[str]] = Field(default=None, description="List of token symbols to query (optional)")
