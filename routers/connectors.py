from typing import List, Optional, Dict

from fastapi import APIRouter, Depends, Request, HTTPException, Query
from hummingbot.client.settings import AllConnectorSettings

from services.accounts_service import AccountsService
from services.market_data_feed_manager import MarketDataFeedManager
from deps import get_accounts_service
from models import AddTokenRequest

router = APIRouter(tags=["Connectors"], prefix="/connectors")


@router.get("/", response_model=List[str])
async def available_connectors():
    """
    Get a list of all available connectors.

    Returns:
        List of connector names supported by the system
    """
    return list(AllConnectorSettings.get_connector_settings().keys())


@router.get("/{connector_name}/config-map", response_model=List[str])
async def get_connector_config_map(connector_name: str, accounts_service: AccountsService = Depends(get_accounts_service)):
    """
    Get configuration fields required for a specific connector.
    
    Args:
        connector_name: Name of the connector to get config map for
        
    Returns:
        List of configuration field names required for the connector
    """
    return accounts_service.get_connector_config_map(connector_name)


@router.get("/{connector_name}/trading-rules")
async def get_trading_rules(
    request: Request, 
    connector_name: str,
    trading_pairs: Optional[List[str]] = Query(default=None, description="Filter by specific trading pairs")
):
    """
    Get trading rules for a connector, optionally filtered by trading pairs.
    
    This endpoint uses the MarketDataFeedManager to access non-trading connector instances,
    which means no authentication or account setup is required.
    
    Args:
        request: FastAPI request object
        connector_name: Name of the connector (e.g., 'binance', 'binance_perpetual')
        trading_pairs: Optional list of trading pairs to filter by (e.g., ['BTC-USDT', 'ETH-USDT'])
        
    Returns:
        Dictionary mapping trading pairs to their trading rules
        
    Raises:
        HTTPException: 404 if connector not found, 500 for other errors
    """
    try:
        market_data_feed_manager: MarketDataFeedManager = request.app.state.market_data_feed_manager
        
        # Get trading rules (filtered by trading pairs if provided)
        rules = await market_data_feed_manager.get_trading_rules(connector_name, trading_pairs)
        
        if "error" in rules:
            raise HTTPException(status_code=404, detail=f"Connector '{connector_name}' not found or error: {rules['error']}")
        
        return rules
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving trading rules: {str(e)}")


@router.get("/{connector_name}/order-types")
async def get_supported_order_types(request: Request, connector_name: str):
    """
    Get order types supported by a specific connector.

    This endpoint uses the MarketDataFeedManager to access non-trading connector instances,
    which means no authentication or account setup is required.

    Args:
        request: FastAPI request object
        connector_name: Name of the connector (e.g., 'binance', 'binance_perpetual')

    Returns:
        List of supported order types (LIMIT, MARKET, LIMIT_MAKER)

    Raises:
        HTTPException: 404 if connector not found, 500 for other errors
    """
    try:
        market_data_feed_manager: MarketDataFeedManager = request.app.state.market_data_feed_manager

        # Access connector through MarketDataProvider's _rate_sources
        connector_instance = market_data_feed_manager.market_data_provider._rate_sources.get(connector_name)

        if not connector_instance:
            raise HTTPException(status_code=404, detail=f"Connector '{connector_name}' not found")

        # Get supported order types
        if hasattr(connector_instance, 'supported_order_types'):
            order_types = [order_type.name for order_type in connector_instance.supported_order_types()]
            return {"connector": connector_name, "supported_order_types": order_types}
        else:
            raise HTTPException(status_code=404, detail=f"Connector '{connector_name}' does not support order types query")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving order types: {str(e)}")
