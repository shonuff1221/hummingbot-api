import logging
from typing import Dict, List, Optional
import aiohttp
from decimal import Decimal

logger = logging.getLogger(__name__)


class GatewayClient:
    """
    Simplified Gateway HTTP client for API integration.
    Provides essential functionality for wallet management and balance queries.
    """

    def __init__(self, base_url: str = "http://localhost:15888"):
        self.base_url = base_url
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self):
        """Close the aiohttp session"""
        if self._session and not self._session.closed:
            await self._session.close()

    async def _request(self, method: str, path: str, params: Dict = None, json: Dict = None) -> Dict:
        """Make HTTP request to Gateway"""
        session = await self._get_session()
        url = f"{self.base_url}/{path}"

        try:
            if method == "GET":
                async with session.get(url, params=params) as response:
                    return await response.json()
            elif method == "POST":
                async with session.post(url, json=json) as response:
                    return await response.json()
            elif method == "DELETE":
                async with session.delete(url, json=json) as response:
                    return await response.json()
        except Exception as e:
            logger.error(f"Gateway request failed: {method} {url} - {e}")
            raise

    async def ping(self) -> bool:
        """Check if Gateway is online"""
        try:
            response = await self._request("GET", "")
            return response.get("status") == "ok"
        except Exception:
            return False

    async def get_wallets(self) -> List[Dict]:
        """Get all connected wallets"""
        return await self._request("GET", "wallet")

    async def get_default_wallet_address(self, chain: str) -> Optional[str]:
        """Get default wallet address for a chain"""
        try:
            wallets = await self.get_wallets()
            for wallet in wallets:
                if wallet.get("chain") == chain:
                    addresses = wallet.get("walletAddresses", [])
                    return addresses[0] if addresses else None
            return None
        except Exception as e:
            logger.error(f"Error getting default wallet for chain {chain}: {e}")
            return None

    async def add_wallet(self, chain: str, private_key: str, set_default: bool = True) -> Dict:
        """Add a wallet to Gateway"""
        return await self._request("POST", "wallet/add", json={
            "chain": chain,
            "privateKey": private_key,
            "setDefault": set_default
        })

    async def remove_wallet(self, chain: str, address: str) -> Dict:
        """Remove a wallet from Gateway"""
        return await self._request("DELETE", "wallet/remove", json={
            "chain": chain,
            "address": address
        })

    async def get_balances(self, chain: str, network: str, address: str, tokens: List[str]) -> Dict:
        """Get token balances for a wallet"""
        return await self._request("POST", f"chains/{chain}/balances", json={
            "network": network,
            "address": address,
            "tokens": tokens
        })

    async def get_chains(self) -> Dict:
        """Get available chains"""
        return await self._request("GET", "config/chains")

    async def get_default_network(self, chain: str) -> Optional[str]:
        """Get default network for a chain"""
        try:
            config = await self._request("GET", "config", params={"namespace": chain})
            return config.get("defaultNetwork")
        except Exception:
            return None

    async def get_tokens(self, chain: str, network: str) -> Dict:
        """Get available tokens for a chain/network"""
        return await self._request("GET", "tokens", params={
            "chain": chain,
            "network": network
        })

    async def add_token(self, chain: str, network: str, address: str, symbol: str, name: str, decimals: int) -> Dict:
        """Add a custom token to Gateway's token list"""
        return await self._request("POST", "tokens", json={
            "chain": chain,
            "network": network,
            "token": {
                "address": address,
                "symbol": symbol,
                "name": name,
                "decimals": decimals
            }
        })

    async def get_config(self, namespace: str) -> Dict:
        """Get configuration for a specific namespace (connector or chain-network)"""
        return await self._request("GET", "config", params={"namespace": namespace})

    async def update_config(self, namespace: str, path: str, value: any) -> Dict:
        """Update a configuration value for a namespace"""
        return await self._request("POST", "config/update", json={
            "namespace": namespace,
            "path": path,
            "value": value
        })

    async def get_pools(self, connector: str, network: str) -> List[Dict]:
        """Get pools for a connector and network"""
        return await self._request("GET", "pools", params={
            "connector": connector,
            "network": network
        })

    async def add_pool(self, connector: str, pool_type: str, network: str, base_symbol: str, quote_symbol: str, address: str) -> Dict:
        """Add a new pool"""
        return await self._request("POST", "pools", json={
            "connector": connector,
            "type": pool_type,
            "network": network,
            "baseSymbol": base_symbol,
            "quoteSymbol": quote_symbol,
            "address": address
        })

    async def pool_info(self, connector: str, network: str, pool_address: str) -> Dict:
        """Get detailed information about a specific pool"""
        return await self._request("POST", "clmm/liquidity/pool", json={
            "connector": connector,
            "network": network,
            "poolAddress": pool_address
        })

    # ============================================
    # Swap Operations
    # ============================================

    async def quote_swap(
        self,
        connector: str,
        network: str,
        base_asset: str,
        quote_asset: str,
        amount: float,
        side: str,
        slippage_pct: Optional[float] = None,
        pool_address: Optional[str] = None
    ) -> Dict:
        """Get a quote for a swap"""
        payload = {
            "network": network,
            "baseToken": base_asset,
            "quoteToken": quote_asset,
            "amount": str(amount),
            "side": side.upper()
        }
        if slippage_pct is not None:
            payload["slippagePct"] = slippage_pct
        if pool_address:
            payload["poolAddress"] = pool_address

        return await self._request("GET", f"connectors/{connector}/router/quote-swap", params=payload)

    async def execute_swap(
        self,
        connector: str,
        network: str,
        wallet_address: str,
        base_asset: str,
        quote_asset: str,
        amount: float,
        side: str,
        slippage_pct: Optional[float] = None
    ) -> Dict:
        """Execute a swap"""
        payload = {
            "network": network,
            "address": wallet_address,
            "baseToken": base_asset,
            "quoteToken": quote_asset,
            "amount": str(amount),
            "side": side.upper()
        }
        if slippage_pct is not None:
            payload["slippagePct"] = slippage_pct

        return await self._request("POST", f"connectors/{connector}/router/execute-swap", json=payload)

    async def execute_quote(
        self,
        connector: str,
        network: str,
        wallet_address: str,
        quote_id: str
    ) -> Dict:
        """Execute a previously obtained quote"""
        return await self._request("POST", f"connectors/{connector}/router/execute-quote", json={
            "network": network,
            "address": wallet_address,
            "quoteId": quote_id
        })

    # ============================================
    # Liquidity Operations - CLMM (Concentrated Liquidity)
    # ============================================

    async def clmm_open_position(
        self,
        connector: str,
        network: str,
        wallet_address: str,
        pool_address: str,
        lower_price: float,
        upper_price: float,
        base_token_amount: Optional[float] = None,
        quote_token_amount: Optional[float] = None,
        slippage_pct: Optional[float] = None
    ) -> Dict:
        """Open a NEW CLMM position with initial liquidity"""
        payload = {
            "connector": connector,
            "network": network,
            "address": wallet_address,
            "poolAddress": pool_address,
            "lowerPrice": lower_price,
            "upperPrice": upper_price
        }
        if base_token_amount is not None:
            payload["baseTokenAmount"] = str(base_token_amount)
        if quote_token_amount is not None:
            payload["quoteTokenAmount"] = str(quote_token_amount)
        if slippage_pct is not None:
            payload["slippagePct"] = slippage_pct

        return await self._request("POST", "clmm/liquidity/open", json=payload)

    async def clmm_add_liquidity(
        self,
        connector: str,
        network: str,
        wallet_address: str,
        position_address: str,
        base_token_amount: Optional[float] = None,
        quote_token_amount: Optional[float] = None,
        slippage_pct: Optional[float] = None
    ) -> Dict:
        """Add more liquidity to an existing CLMM position"""
        payload = {
            "connector": connector,
            "network": network,
            "address": wallet_address,
            "positionAddress": position_address
        }
        if base_token_amount is not None:
            payload["baseTokenAmount"] = str(base_token_amount)
        if quote_token_amount is not None:
            payload["quoteTokenAmount"] = str(quote_token_amount)
        if slippage_pct is not None:
            payload["slippagePct"] = slippage_pct

        return await self._request("POST", "clmm/liquidity/add", json=payload)

    async def clmm_close_position(
        self,
        connector: str,
        network: str,
        wallet_address: str,
        position_address: str
    ) -> Dict:
        """Close a CLMM position completely"""
        return await self._request("POST", "clmm/liquidity/close", json={
            "connector": connector,
            "network": network,
            "address": wallet_address,
            "positionAddress": position_address
        })

    async def clmm_remove_liquidity(
        self,
        connector: str,
        network: str,
        wallet_address: str,
        position_address: str,
        percentage: float
    ) -> Dict:
        """Remove liquidity from a CLMM position (partial)"""
        return await self._request("POST", "clmm/liquidity/remove", json={
            "connector": connector,
            "network": network,
            "address": wallet_address,
            "positionAddress": position_address,
            "percentage": percentage
        })

    async def clmm_position_info(
        self,
        connector: str,
        network: str,
        wallet_address: str,
        position_address: str
    ) -> Dict:
        """Get CLMM position information"""
        return await self._request("POST", "clmm/liquidity/position", json={
            "connector": connector,
            "network": network,
            "address": wallet_address,
            "positionAddress": position_address
        })

    async def clmm_positions_owned(
        self,
        connector: str,
        network: str,
        wallet_address: str,
        pool_address: Optional[str] = None
    ) -> Dict:
        """Get all CLMM positions owned by wallet"""
        payload = {
            "connector": connector,
            "network": network,
            "address": wallet_address
        }
        if pool_address:
            payload["poolAddress"] = pool_address

        return await self._request("POST", "clmm/liquidity/positions", json=payload)

    async def clmm_collect_fees(
        self,
        connector: str,
        network: str,
        wallet_address: str,
        position_address: str
    ) -> Dict:
        """Collect accumulated fees from a CLMM position"""
        return await self._request("POST", "clmm/liquidity/collect-fees", json={
            "connector": connector,
            "network": network,
            "address": wallet_address,
            "positionAddress": position_address
        })

