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

