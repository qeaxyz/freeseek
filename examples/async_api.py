import aiohttp
from typing import Dict, Any
from .auth import AuthManager
from .exceptions import APIError

class AsyncFreeseekAPI:
    def __init__(self, api_key: str, base_url: str = "https://api.freeseek.com/v1"):
        self.auth = AuthManager(api_key)
        self.base_url = base_url
        self.session = aiohttp.ClientSession()
        self.timeout = aiohttp.ClientTimeout(total=30)

    async def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = {"Authorization": f"Bearer {await self.auth.get_token_async()}"}
        
        try:
            async with self.session.request(
                method,
                url,
                headers=headers,
                timeout=self.timeout,
                **kwargs
            ) as response:
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientError as e:
            raise APIError(f"Request failed: {str(e)}") from e

    async def infer(self, model: str, data: dict) -> Dict[str, Any]:
        return await self._request("POST", "infer", json={"model": model, "data": data})

    async def close(self):
        await self.session.close()