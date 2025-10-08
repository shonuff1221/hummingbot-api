from typing import Dict, List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, Query

from models.trading import (
    PortfolioStateFilterRequest,
    PortfolioHistoryFilterRequest,
    PortfolioDistributionFilterRequest,
    AccountsDistributionFilterRequest
)
from services.accounts_service import AccountsService
from deps import get_accounts_service
from models import PaginatedResponse

router = APIRouter(tags=["Portfolio"], prefix="/portfolio")


@router.post("/state", response_model=Dict[str, Dict[str, List[Dict]]])
async def get_portfolio_state(
    filter_request: PortfolioStateFilterRequest,
    accounts_service: AccountsService = Depends(get_accounts_service)
):
    """
    Get the current state of all or filtered accounts portfolio.
    
    Args:
        filter_request: JSON payload with filtering criteria
        
    Returns:
        Dict containing account states with connector balances and token information
    """
    await accounts_service.update_account_state()
    all_states = accounts_service.get_accounts_state()
    
    # Apply account name filter first
    if filter_request.account_names:
        filtered_states = {}
        for account_name in filter_request.account_names:
            if account_name in all_states:
                filtered_states[account_name] = all_states[account_name]
        all_states = filtered_states
    
    # Apply connector filter if specified
    if filter_request.connector_names:
        for account_name, account_data in all_states.items():
            # Filter connectors directly (they are at the top level of account_data)
            filtered_connectors = {}
            for connector_name in filter_request.connector_names:
                if connector_name in account_data:
                    filtered_connectors[connector_name] = account_data[connector_name]
            # Replace account_data with only filtered connectors
            all_states[account_name] = filtered_connectors
    
    return all_states


@router.post("/history", response_model=PaginatedResponse)
async def get_portfolio_history(
    filter_request: PortfolioHistoryFilterRequest,
    accounts_service: AccountsService = Depends(get_accounts_service)
):
    """
    Get the historical state of all or filtered accounts portfolio with pagination.
    
    Args:
        filter_request: JSON payload with filtering criteria
        
    Returns:
        Paginated response with historical portfolio data
    """
    try:
        # Convert integer timestamps to datetime objects
        start_time_dt = datetime.fromtimestamp(filter_request.start_time / 1000) if filter_request.start_time else None
        end_time_dt = datetime.fromtimestamp(filter_request.end_time / 1000) if filter_request.end_time else None
        
        if not filter_request.account_names:
            # Get history for all accounts
            data, next_cursor, has_more = await accounts_service.load_account_state_history(
                limit=filter_request.limit,
                cursor=filter_request.cursor,
                start_time=start_time_dt,
                end_time=end_time_dt
            )
        else:
            # Get history for specific accounts - need to aggregate
            all_data = []
            for account_name in filter_request.account_names:
                acc_data, _, _ = await accounts_service.get_account_state_history(
                    account_name=account_name,
                    limit=filter_request.limit,
                    cursor=filter_request.cursor,
                    start_time=start_time_dt,
                    end_time=end_time_dt
                )
                all_data.extend(acc_data)
            
            # Sort by timestamp and apply pagination
            all_data.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            
            # Apply limit
            data = all_data[:filter_request.limit]
            has_more = len(all_data) > filter_request.limit
            next_cursor = data[-1]["timestamp"] if data and has_more else None
        
        # Apply connector filter to the data if specified
        if filter_request.connector_names:
            for item in data:
                for account_name, account_data in item.items():
                    if isinstance(account_data, dict) and "connectors" in account_data:
                        filtered_connectors = {}
                        for connector_name in filter_request.connector_names:
                            if connector_name in account_data["connectors"]:
                                filtered_connectors[connector_name] = account_data["connectors"][connector_name]
                        account_data["connectors"] = filtered_connectors
        
        return PaginatedResponse(
            data=data,
            pagination={
                "limit": filter_request.limit,
                "has_more": has_more,
                "next_cursor": next_cursor,
                "current_cursor": filter_request.cursor,
                "filters": {
                    "account_names": filter_request.account_names,
                    "connector_names": filter_request.connector_names,
                    "start_time": filter_request.start_time,
                    "end_time": filter_request.end_time
                }
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/distribution")
async def get_portfolio_distribution(
    filter_request: PortfolioDistributionFilterRequest,
    accounts_service: AccountsService = Depends(get_accounts_service)
):
    """
    Get portfolio distribution by tokens with percentages across all or filtered accounts.
    
    Args:
        filter_request: JSON payload with filtering criteria
        
    Returns:
        Dictionary with token distribution including percentages, values, and breakdown by accounts/connectors
    """
    if not filter_request.account_names:
        # Get distribution for all accounts
        distribution = accounts_service.get_portfolio_distribution()
    elif len(filter_request.account_names) == 1:
        # Single account - use existing method
        distribution = accounts_service.get_portfolio_distribution(filter_request.account_names[0])
    else:
        # Multiple accounts - need to aggregate
        aggregated_distribution = {
            "tokens": {},
            "total_value": 0,
            "token_count": 0,
            "accounts": {}
        }
        
        for account_name in filter_request.account_names:
            account_dist = accounts_service.get_portfolio_distribution(account_name)
            
            # Skip if account doesn't exist or has error
            if account_dist.get("error") or account_dist.get("token_count", 0) == 0:
                continue
            
            # Aggregate token data
            for token, token_data in account_dist.get("tokens", {}).items():
                if token not in aggregated_distribution["tokens"]:
                    aggregated_distribution["tokens"][token] = {
                        "token": token,
                        "value": 0,
                        "percentage": 0,
                        "accounts": {}
                    }
                
                aggregated_distribution["tokens"][token]["value"] += token_data.get("value", 0)
                
                # Copy account-specific data
                for acc_name, acc_data in token_data.get("accounts", {}).items():
                    aggregated_distribution["tokens"][token]["accounts"][acc_name] = acc_data
            
            aggregated_distribution["total_value"] += account_dist.get("total_value", 0)
            aggregated_distribution["accounts"][account_name] = account_dist.get("accounts", {}).get(account_name, {})
        
        # Recalculate percentages
        total_value = aggregated_distribution["total_value"]
        if total_value > 0:
            for token_data in aggregated_distribution["tokens"].values():
                token_data["percentage"] = (token_data["value"] / total_value) * 100
        
        aggregated_distribution["token_count"] = len(aggregated_distribution["tokens"])
        
        distribution = aggregated_distribution
    
    # Apply connector filter if specified
    if filter_request.connector_names:
        filtered_distribution = []
        filtered_total_value = 0
        
        for token_data in distribution.get("distribution", []):
            filtered_token = {
                "token": token_data["token"],
                "total_value": 0,
                "total_units": 0,
                "percentage": 0,
                "accounts": {}
            }
            
            # Filter each account's connectors
            for account_name, account_data in token_data.get("accounts", {}).items():
                if "connectors" in account_data:
                    filtered_connectors = {}
                    account_value = 0
                    account_units = 0
                    
                    # Only include specified connectors
                    for connector_name in filter_request.connector_names:
                        if connector_name in account_data["connectors"]:
                            filtered_connectors[connector_name] = account_data["connectors"][connector_name]
                            account_value += account_data["connectors"][connector_name].get("value", 0)
                            account_units += account_data["connectors"][connector_name].get("units", 0)
                    
                    # Only include account if it has matching connectors
                    if filtered_connectors:
                        filtered_token["accounts"][account_name] = {
                            "value": round(account_value, 6),
                            "units": account_units,
                            "percentage": 0,  # Will be recalculated later
                            "connectors": filtered_connectors
                        }
                        
                        filtered_token["total_value"] += account_value
                        filtered_token["total_units"] += account_units
            
            # Only include token if it has values after filtering
            if filtered_token["total_value"] > 0:
                filtered_distribution.append(filtered_token)
                filtered_total_value += filtered_token["total_value"]
        
        # Recalculate percentages after filtering
        if filtered_total_value > 0:
            for token_data in filtered_distribution:
                token_data["percentage"] = round((token_data["total_value"] / filtered_total_value) * 100, 4)
                # Update account percentages
                for account_data in token_data["accounts"].values():
                    account_data["percentage"] = round((account_data["value"] / filtered_total_value) * 100, 4)
        
        # Sort by value (descending)
        filtered_distribution.sort(key=lambda x: x["total_value"], reverse=True)
        
        # Update the distribution
        distribution = {
            "total_portfolio_value": round(filtered_total_value, 6),
            "token_count": len(filtered_distribution),
            "distribution": filtered_distribution,
            "account_filter": distribution.get("account_filter", "filtered")
        }
    
    return distribution


@router.post("/accounts-distribution")
async def get_accounts_distribution(
    filter_request: AccountsDistributionFilterRequest,
    accounts_service: AccountsService = Depends(get_accounts_service)
):
    """
    Get portfolio distribution by accounts with percentages.
    
    Args:
        filter_request: JSON payload with filtering criteria
        
    Returns:
        Dictionary with account distribution including percentages, values, and breakdown by connectors
    """
    all_distribution = accounts_service.get_account_distribution()
    
    # If no filter, return all accounts
    if not filter_request.account_names:
        return all_distribution
    
    # Filter the distribution by requested accounts
    filtered_distribution = {
        "accounts": {},
        "total_value": 0,
        "account_count": 0
    }
    
    for account_name in filter_request.account_names:
        if account_name in all_distribution.get("accounts", {}):
            filtered_distribution["accounts"][account_name] = all_distribution["accounts"][account_name]
            filtered_distribution["total_value"] += all_distribution["accounts"][account_name].get("total_value", 0)
    
    # Apply connector filter if specified
    if filter_request.connector_names:
        for account_name, account_data in filtered_distribution["accounts"].items():
            if "connectors" in account_data:
                filtered_connectors = {}
                for connector_name in filter_request.connector_names:
                    if connector_name in account_data["connectors"]:
                        filtered_connectors[connector_name] = account_data["connectors"][connector_name]
                account_data["connectors"] = filtered_connectors
                
                # Recalculate account total after connector filtering
                new_total = sum(
                    conn_data.get("total_balance_in_usd", 0) 
                    for conn_data in filtered_connectors.values()
                )
                account_data["total_value"] = new_total
        
        # Recalculate total_value after connector filtering
        filtered_distribution["total_value"] = sum(
            acc_data.get("total_value", 0) 
            for acc_data in filtered_distribution["accounts"].values()
        )

    # Recalculate percentages
    total_value = filtered_distribution["total_value"]
    if total_value > 0:
        for account_data in filtered_distribution["accounts"].values():
            account_data["percentage"] = (account_data.get("total_value", 0) / total_value) * 100
    
    filtered_distribution["account_count"] = len(filtered_distribution["accounts"])

    return filtered_distribution


@router.get("/gateway/{chain}/balance")
async def get_gateway_wallet_balance(
    chain: str,
    address: Optional[str] = Query(default=None, description="Wallet address (uses default wallet if not specified)"),
    tokens: Optional[List[str]] = Query(default=None, description="List of token symbols to query"),
    accounts_service: AccountsService = Depends(get_accounts_service)
):
    """
    Get Gateway wallet balances with pricing from rate sources.

    This endpoint queries a Gateway wallet and returns token balances
    with current market prices fetched from the rate source provider. Prices are
    cached and updated in the background by the market data feed manager.

    Args:
        chain: Blockchain chain (e.g., 'solana', 'ethereum')
        address: Optional wallet address (uses chain's default wallet if not specified)
        tokens: Optional list of token symbols (if None, returns top 20 tokens)

    Returns:
        Dictionary with chain, address, and list of token balances with units, prices, and values

    Raises:
        HTTPException: 503 if Gateway unavailable, 400 if chain/network not found or no wallet available

    Note:
        - Prices are fetched from rate sources using "gateway" connector for AMM pairs
        - Gateway wallet balances are also automatically included in portfolio state
          under master_account as gateway_{chain} connectors
    """
    try:
        # Get default wallet address if not provided
        if not address:
            address = await accounts_service.gateway_client.get_default_wallet_address(chain)
            if not address:
                raise HTTPException(status_code=400, detail=f"No wallet found for chain '{chain}'")

        balances = await accounts_service.get_gateway_balances(chain, address, tokens)
        return {"chain": chain, "address": address, "balances": balances}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))