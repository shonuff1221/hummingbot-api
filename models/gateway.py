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


class GatewayAction(BaseModel):
    """Actions that can be performed on Gateway"""
    action: str = Field(description="Action to perform: start, stop, restart, remove")
