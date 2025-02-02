import json
import requests
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from typing import Dict, Any, Generator, Optional, AsyncGenerator
from pydantic import BaseModel, ValidationError
from .auth import AuthManager
from .exceptions import APIError, RateLimitExceededError
from .utils import HelperFunctions


# Pydantic Models for Requests
class InferRequest(BaseModel):
    model: str
    data: dict


# Synchronous API Client
class FreeseekAPI:
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.freeseek.com/v1",
        timeout: int = 30,
        max_retries: int = 3,
        backoff_factor: int = 1
    ):
        self.auth = AuthManager(api_key)
        self.base_url = base_url
        self.session = requests.Session()
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor

    def _full_url(self, endpoint: str) -> str:
        return f"{self.base_url}/{endpoint.lstrip('/')}"

    def _get_headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.auth.token}"}

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(requests.RequestException),
        reraise=True
    )
    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        url = self._full_url(endpoint)
        headers = self._get_headers()
        HelperFunctions.logger.debug(f"Making {method} request to {url} with headers { {k: 'REDACTED' if k=='Authorization' else v for k,v in headers.items()} } and kwargs {kwargs}")
        try:
            response = self.session.request(method, url, headers=headers, timeout=self.timeout, **kwargs)
            response.raise_for_status()
            HelperFunctions.logger.debug(f"Response received: {response.status_code}")
            return response.json()
        except requests.HTTPError as e:
            HelperFunctions.logger.error(f"HTTP Error during {method} {url}: {str(e)}")
            raise APIError(f"HTTP Error: {str(e)}", status_code=e.response.status_code) from e
        except requests.RequestException as e:
            HelperFunctions.logger.error(f"Request failed for {method} {url}: {str(e)}")
            raise APIError(f"Request failed: {str(e)}") from e

    def infer(self, model: str, data: dict) -> Dict[str, Any]:
        try:
            validated_request = InferRequest(model=model, data=data)
        except ValidationError as ve:
            HelperFunctions.logger.error(f"Validation error for infer request: {ve.json()}")
            raise APIError(f"Invalid input for inference: {ve}") from ve
        payload = validated_request.dict()
        return self._request("POST", "infer", json=payload)

    def stream_infer(self, model: str, data: dict) -> Generator[Dict[str, Any], None, None]:
        try:
            validated_request = InferRequest(model=model, data=data)
        except ValidationError as ve:
            HelperFunctions.logger.error(f"Validation error for stream_infer request: {ve.json()}")
            raise APIError(f"Invalid input for streaming inference: {ve}") from ve
        url = self._full_url("infer")
        headers = self._get_headers()
        payload = validated_request.dict()
        HelperFunctions.logger.debug(f"Starting streaming infer for URL: {url}")
        try:
            with self.session.post(url, headers=headers, json=payload, timeout=self.timeout, stream=True) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if line:
                        try:
                            chunk = json.loads(line.decode('utf-8'))
                            HelperFunctions.logger.debug(f"Received chunk: {chunk}")
                            yield chunk
                        except json.JSONDecodeError as je:
                            HelperFunctions.logger.error(f"JSON decode error in streaming response: {str(je)}")
        except requests.HTTPError as e:
            HelperFunctions.logger.error(f"HTTP Error during streaming infer: {str(e)}")
            raise APIError(f"HTTP Error during streaming infer: {str(e)}", status_code=e.response.status_code) from e
        except requests.RequestException as e:
            HelperFunctions.logger.error(f"Streaming request failed: {str(e)}")
            raise APIError(f"Streaming request failed: {str(e)}") from e

    def get_model_info(self, model: str) -> Dict[str, Any]:
        return self._request("GET", f"models/{model}")

    def get_model_schema(self, model: str) -> Dict[str, Any]:
        return self._request("GET", f"models/{model}/schema")

    def list_models(self) -> Dict[str, Any]:
        return self._request("GET", "models")


# Asynchronous API Client
class AsyncFreeseekAPI:
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.freeseek.com/v1",
        timeout: int = 30,
        max_retries: int = 3,
        backoff_factor: int = 1
    ):
        self.auth = AuthManager(api_key)
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.client = httpx.AsyncClient(timeout=self.timeout)

    def _full_url(self, endpoint: str) -> str:
        return f"{self.base_url}/{endpoint.lstrip('/')}"

    def _get_headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.auth.token}"}

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.RequestError)),
        reraise=True
    )
    async def _async_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        url = self._full_url(endpoint)
        headers = self._get_headers()
        HelperFunctions.logger.debug(f"Async {method} request to {url} with headers { {k: 'REDACTED' if k=='Authorization' else v for k,v in headers.items()} } and kwargs {kwargs}")
        try:
            response = await self.client.request(method, url, headers=headers, **kwargs)
            response.raise_for_status()
            HelperFunctions.logger.debug(f"Async response received: {response.status_code}")
            return response.json()
        except httpx.HTTPStatusError as e:
            HelperFunctions.logger.error(f"HTTP Error during {method} {url}: {str(e)}")
            raise APIError(f"HTTP Error: {str(e)}", status_code=e.response.status_code) from e
        except httpx.RequestException as e:
            HelperFunctions.logger.error(f"Request failed for {method} {url}: {str(e)}")
            raise APIError(f"Request failed: {str(e)}") from e

    async def infer(self, model: str, data: dict) -> Dict[str, Any]:
        try:
            validated_request = InferRequest(model=model, data=data)
        except ValidationError as ve:
            HelperFunctions.logger.error(f"Validation error for async infer: {ve.json()}")
            raise APIError(f"Invalid input for async inference: {ve}") from ve
        payload = validated_request.dict()
        return await self._async_request("POST", "infer", json=payload)

    async def stream_infer(self, model: str, data: dict) -> AsyncGenerator[Dict[str, Any], None]:
        try:
            validated_request = InferRequest(model=model, data=data)
        except ValidationError as ve:
            HelperFunctions.logger.error(f"Validation error for async stream_infer: {ve.json()}")
            raise APIError(f"Invalid input for async streaming inference: {ve}") from ve
        url = self._full_url("infer")
        headers = self._get_headers()
        payload = validated_request.dict()
        HelperFunctions.logger.debug(f"Starting async streaming infer for URL: {url}")
        try:
            async with self.client.stream("POST", url, headers=headers, json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line:
                        try:
                            chunk = json.loads(line)
                            HelperFunctions.logger.debug(f"Received async chunk: {chunk}")
                            yield chunk
                        except json.JSONDecodeError as je:
                            HelperFunctions.logger.error(f"Async JSON decode error: {str(je)}")
        except (httpx.HTTPStatusError, httpx.RequestError) as e:
            HelperFunctions.logger.error(f"Async streaming request error: {str(e)}")
            raise APIError(f"Async streaming request failed: {str(e)}") from e

    async def get_model_info(self, model: str) -> Dict[str, Any]:
        return await self._async_request("GET", f"models/{model}")

    async def get_model_schema(self, model: str) -> Dict[str, Any]:
        return await self._async_request("GET", f"models/{model}/schema")

    async def list_models(self) -> Dict[str, Any]:
        return await self._async_request("GET", "models")

    async def aclose(self):
        """Close the underlying async client session."""
        await self.client.aclose()