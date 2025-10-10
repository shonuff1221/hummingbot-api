"""
Models for DEX (Decentralized Exchange) trading operations.
Supports swaps and liquidity provision on AMM and CLMM protocols.
"""
from typing import Optional, List
from pydantic import BaseModel, Field
from decimal import Decimal


# ============================================
# Swap Models
# ============================================

class SwapQuoteRequest(BaseModel):
    """Request for swap price quote"""
    connector: str = Field(description="DEX connector (e.g., 'raydium', 'meteora')")
    network: Optional[str] = Field(default=None, description="Network (e.g., 'mainnet-beta'). If not provided, uses default network for chain")
    trading_pair: str = Field(description="Trading pair in BASE-QUOTE format (e.g., 'SOL-USDC')")
    side: str = Field(description="Trade side: 'BUY' or 'SELL'")
    amount: Decimal = Field(description="Amount to swap (in base token for SELL, quote token for BUY)")
    slippage_pct: Optional[Decimal] = Field(default=None, description="Maximum slippage percentage (e.g., 1.0 for 1%)")
    pool_address: Optional[str] = Field(default=None, description="Specific pool address (optional)")


class SwapQuoteResponse(BaseModel):
    """Response with swap quote details"""
    base: str = Field(description="Base token symbol")
    quote: str = Field(description="Quote token symbol")
    price: Decimal = Field(description="Quoted price")
    amount: Decimal = Field(description="Input amount")
    expected_amount: Optional[Decimal] = Field(default=None, description="Expected output amount")
    slippage_pct: Optional[Decimal] = Field(default=None, description="Applied slippage percentage")
    gas_estimate: Optional[Decimal] = Field(default=None, description="Estimated gas cost")


class SwapExecuteRequest(BaseModel):
    """Request to execute a swap"""
    connector: str = Field(description="DEX connector (e.g., 'raydium', 'meteora')")
    network: Optional[str] = Field(default=None, description="Network (e.g., 'mainnet-beta'). If not provided, uses default network for chain")
    chain: str = Field(description="Chain (e.g., 'solana', 'ethereum')")
    trading_pair: str = Field(description="Trading pair (e.g., 'SOL-USDC')")
    side: str = Field(description="Trade side: 'BUY' or 'SELL'")
    amount: Decimal = Field(description="Amount to swap")
    slippage_pct: Optional[Decimal] = Field(default=None, description="Maximum slippage percentage")
    quote_id: Optional[str] = Field(default=None, description="Quote ID to execute (if using quote)")


class SwapExecuteResponse(BaseModel):
    """Response after executing swap"""
    transaction_hash: str = Field(description="Transaction hash")
    trading_pair: str = Field(description="Trading pair")
    side: str = Field(description="Trade side")
    amount: Decimal = Field(description="Amount swapped")
    status: str = Field(default="submitted", description="Transaction status")


# ============================================
# Liquidity Models
# ============================================

class OpenPositionRequest(BaseModel):
    """Request to open a new CLMM position with initial liquidity"""
    connector: str = Field(description="DEX connector (e.g., 'meteora_clmm')")
    network: Optional[str] = Field(default=None, description="Network (e.g., 'mainnet-beta'). If not provided, uses default network for chain")
    chain: str = Field(description="Chain (e.g., 'solana', 'ethereum')")
    trading_pair: str = Field(description="Trading pair (e.g., 'SOL-USDC')")

    # Position range - either absolute prices or center + widths
    lower_price: Optional[Decimal] = Field(default=None, description="Lower price for position range")
    upper_price: Optional[Decimal] = Field(default=None, description="Upper price for position range")
    price: Optional[Decimal] = Field(default=None, description="Center price (alternative to absolute prices)")
    lower_width_pct: Optional[Decimal] = Field(default=None, description="Lower range width % from center")
    upper_width_pct: Optional[Decimal] = Field(default=None, description="Upper range width % from center")

    # Initial liquidity
    base_token_amount: Optional[Decimal] = Field(default=None, description="Amount of base token to add")
    quote_token_amount: Optional[Decimal] = Field(default=None, description="Amount of quote token to add")
    slippage_pct: Optional[Decimal] = Field(default=None, description="Maximum slippage percentage")


class OpenPositionResponse(BaseModel):
    """Response after opening a new position"""
    transaction_hash: str = Field(description="Transaction hash")
    position_address: str = Field(description="Address of the newly created position")
    trading_pair: str = Field(description="Trading pair")
    pool_address: str = Field(description="Pool address")
    lower_price: Decimal = Field(description="Lower price bound")
    upper_price: Decimal = Field(description="Upper price bound")
    status: str = Field(default="submitted", description="Transaction status")


class AddLiquidityToPositionRequest(BaseModel):
    """Request to add MORE liquidity to an EXISTING CLMM position"""
    connector: str = Field(description="DEX connector (e.g., 'meteora_clmm')")
    network: Optional[str] = Field(default=None, description="Network (e.g., 'mainnet-beta'). If not provided, uses default network for chain")
    chain: str = Field(description="Chain (e.g., 'solana', 'ethereum')")
    position_address: str = Field(description="Existing position address to add liquidity to")
    base_token_amount: Optional[Decimal] = Field(default=None, description="Amount of base token to add")
    quote_token_amount: Optional[Decimal] = Field(default=None, description="Amount of quote token to add")
    slippage_pct: Optional[Decimal] = Field(default=None, description="Maximum slippage percentage")


class AddLiquidityAMMRequest(BaseModel):
    """Request to add liquidity to an AMM pool (no position concept)"""
    connector: str = Field(description="DEX connector (e.g., 'raydium')")
    network: Optional[str] = Field(default=None, description="Network (e.g., 'mainnet-beta'). If not provided, uses default network for chain")
    chain: str = Field(description="Chain (e.g., 'solana', 'ethereum')")
    trading_pair: str = Field(description="Trading pair (e.g., 'SOL-USDC')")
    base_token_amount: Decimal = Field(description="Amount of base token to add")
    quote_token_amount: Decimal = Field(description="Amount of quote token to add")
    slippage_pct: Optional[Decimal] = Field(default=None, description="Maximum slippage percentage")


class RemoveLiquidityFromPositionRequest(BaseModel):
    """Request to remove SOME liquidity from a CLMM position (partial removal)"""
    connector: str = Field(description="DEX connector (e.g., 'meteora_clmm')")
    network: Optional[str] = Field(default=None, description="Network (e.g., 'mainnet-beta'). If not provided, uses default network for chain")
    chain: str = Field(description="Chain (e.g., 'solana', 'ethereum')")
    position_address: str = Field(description="Position address to remove liquidity from")
    percentage: Decimal = Field(description="Percentage of liquidity to remove (0-100)")


class ClosePositionRequest(BaseModel):
    """Request to CLOSE a CLMM position completely (removes all liquidity and closes position)"""
    connector: str = Field(description="DEX connector (e.g., 'meteora_clmm')")
    network: Optional[str] = Field(default=None, description="Network (e.g., 'mainnet-beta'). If not provided, uses default network for chain")
    chain: str = Field(description="Chain (e.g., 'solana', 'ethereum')")
    position_address: str = Field(description="Position address to close")


class RemoveLiquidityAMMRequest(BaseModel):
    """Request to remove liquidity from an AMM pool"""
    connector: str = Field(description="DEX connector (e.g., 'raydium')")
    network: Optional[str] = Field(default=None, description="Network (e.g., 'mainnet-beta'). If not provided, uses default network for chain")
    chain: str = Field(description="Chain (e.g., 'solana', 'ethereum')")
    trading_pair: str = Field(description="Trading pair (e.g., 'SOL-USDC')")
    percentage: Decimal = Field(description="Percentage of liquidity to remove (0-100)")


class LiquidityPositionInfo(BaseModel):
    """Information about a liquidity position"""
    type: str = Field(description="Position type: 'amm' or 'clmm'")
    address: Optional[str] = Field(default=None, description="Position address (CLMM only)")
    pool_address: str = Field(description="Pool address")
    trading_pair: str = Field(description="Trading pair")
    base_token: str = Field(description="Base token symbol")
    quote_token: str = Field(description="Quote token symbol")
    base_token_amount: Decimal = Field(description="Base token amount in position")
    quote_token_amount: Decimal = Field(description="Quote token amount in position")
    price: Decimal = Field(description="Current price")

    # AMM-specific
    lp_token_amount: Optional[Decimal] = Field(default=None, description="LP token amount (AMM)")

    # CLMM-specific
    lower_price: Optional[Decimal] = Field(default=None, description="Lower price (CLMM)")
    upper_price: Optional[Decimal] = Field(default=None, description="Upper price (CLMM)")
    base_fee_amount: Optional[Decimal] = Field(default=None, description="Base token fees (CLMM)")
    quote_fee_amount: Optional[Decimal] = Field(default=None, description="Quote token fees (CLMM)")
    lower_bin_id: Optional[int] = Field(default=None, description="Lower bin ID (CLMM)")
    upper_bin_id: Optional[int] = Field(default=None, description="Upper bin ID (CLMM)")


class PoolInfo(BaseModel):
    """Information about a liquidity pool"""
    type: str = Field(description="Pool type: 'amm' or 'clmm'")
    address: str = Field(description="Pool address")
    trading_pair: str = Field(description="Trading pair")
    base_token: str = Field(description="Base token symbol")
    quote_token: str = Field(description="Quote token symbol")
    price: Decimal = Field(description="Current pool price")
    base_token_amount: Decimal = Field(description="Base token liquidity in pool")
    quote_token_amount: Decimal = Field(description="Quote token liquidity in pool")
    fee_pct: Decimal = Field(description="Pool fee percentage")

    # CLMM-specific
    bin_step: Optional[int] = Field(default=None, description="Bin step (CLMM)")
    active_bin_id: Optional[int] = Field(default=None, description="Active bin ID (CLMM)")


class GetPositionsRequest(BaseModel):
    """Request to get user's liquidity positions"""
    connector: str = Field(description="DEX connector (e.g., 'raydium', 'meteora')")
    network: Optional[str] = Field(default=None, description="Network (e.g., 'mainnet-beta'). If not provided, uses default network for chain")
    chain: str = Field(description="Chain (e.g., 'solana', 'ethereum')")
    pool_address: Optional[str] = Field(default=None, description="Filter by pool address (required for AMM)")


class GetPoolInfoRequest(BaseModel):
    """Request to get pool information"""
    connector: str = Field(description="DEX connector (e.g., 'raydium', 'meteora')")
    network: Optional[str] = Field(default=None, description="Network (e.g., 'mainnet-beta'). If not provided, uses default network for chain")
    trading_pair: str = Field(description="Trading pair (e.g., 'SOL-USDC')")


class CollectFeesRequest(BaseModel):
    """Request to collect fees from a CLMM position"""
    connector: str = Field(description="DEX connector (e.g., 'meteora')")
    network: Optional[str] = Field(default=None, description="Network (e.g., 'mainnet-beta'). If not provided, uses default network for chain")
    chain: str = Field(description="Chain (e.g., 'solana', 'ethereum')")
    position_address: str = Field(description="Position address to collect fees from")


class CollectFeesResponse(BaseModel):
    """Response after collecting fees"""
    transaction_hash: str = Field(description="Transaction hash")
    position_address: str = Field(description="Position address")
    base_fee_collected: Optional[Decimal] = Field(default=None, description="Base token fees collected")
    quote_fee_collected: Optional[Decimal] = Field(default=None, description="Quote token fees collected")
    status: str = Field(default="submitted", description="Transaction status")
