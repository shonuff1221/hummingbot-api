from pydantic import BaseModel, Field
from typing import Optional


class GatewayConfig(BaseModel):
    """Configuration for Gateway container deployment"""
    passphrase: str = Field(description="Gateway passphrase for configuration encryption")
    image: str = Field(default="hummingbot/gateway:latest", description="Docker image for Gateway")
    port: int = Field(default=15888, description="Port for Gateway API")
    dev_mode: bool = Field(default=True, description="Enable development mode")


class GatewayStatus(BaseModel):
    """Status information for Gateway instance"""
    running: bool = Field(description="Whether Gateway container is running")
    container_id: Optional[str] = Field(default=None, description="Container ID if running")
    image: Optional[str] = Field(default=None, description="Image used for the container")
    created_at: Optional[str] = Field(default=None, description="Container creation timestamp")
    port: Optional[int] = Field(default=None, description="Port Gateway is running on")


class AddPoolRequest(BaseModel):
    """Request to add a liquidity pool"""
    connector: str = Field(description="DEX connector name (e.g., 'raydium', 'meteora')")
    type: str = Field(description="Pool type (e.g., 'amm', 'clmm')")
    network: str = Field(description="Network name (e.g., 'mainnet-beta')")
    base: str = Field(description="Base token symbol")
    quote: str = Field(description="Quote token symbol")
    address: str = Field(description="Pool contract address")
