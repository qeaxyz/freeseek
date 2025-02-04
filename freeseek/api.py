import json
import time
import requests
import httpx
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from typing import Dict, Any, Generator, Optional, AsyncGenerator, Callable, Union, List, Tuple
from pydantic import BaseModel, ValidationError

from .auth import AuthManager
from .exceptions import APIError, RateLimitExceededError
from .utils import HelperFunctions

# Type aliases for middleware functions.
PreRequestMiddleware = Callable[[Dict[str, Any]], Union[Dict[str, Any], None]]
PostResponseMiddleware = Callable[[Any], Union[Any, None]]


# Pydantic model for inference requests.
class InferRequest(BaseModel):
    model: str
    data: dict


# =============================================================================
# Circuit Breaker Implementation
# =============================================================================
class CircuitBreaker:
    def __init__(self, failure_threshold: int = 3, recovery_timeout: int = 30):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout  # in seconds
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = "CLOSED"  # Other states: "OPEN", "HALF_OPEN"

    def _open(self):
        self.state = "OPEN"
        self.last_failure_time = time.time()
        HelperFunctions.logger.warning("Circuit breaker opened.")

    def _close(self):
        self.state = "CLOSED"
        self.failure_count = 0
        self.last_failure_time = None
        HelperFunctions.logger.info("Circuit breaker closed.")

    def call(self, func: Callable, *args, **kwargs):
        if self.state == "OPEN":
            if self.last_failure_time and (time.time() - self.last_failure_time) > self.recovery_timeout:
                self.state = "HALF_OPEN"
            else:
                raise APIError("Circuit breaker is open. Request aborted.")
        try:
            result = func(*args, **kwargs)
        except Exception as e:
            self.failure_count += 1
            if self.failure_count >= self.failure_threshold:
                self._open()
            raise e
        else:
            # On success reset failure count if we were half-open.
            if self.state == "HALF_OPEN":
                self._close()
            return result


# =============================================================================
# Synchronous API Client with Additional Features
# =============================================================================
class FreeseekAPI:
    """
    Synchronous API Client with added circuit breaker, metrics, and a new batch inference feature.
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.freeseek.com/v1",
        timeout: int = 30,
        max_retries: int = 3,
        backoff_factor: int = 1,
        circuit_failure_threshold: int = 3,
        circuit_recovery_timeout: int = 30
    ):
        self.auth = AuthManager(api_key)
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor

        # Circuit breaker for handling repeated failures.
        self.circuit_breaker = CircuitBreaker(failure_threshold=circuit_failure_threshold,
                                               recovery_timeout=circuit_recovery_timeout)

        # Initialize middleware lists.
        self._pre_request_middlewares: List[PreRequestMiddleware] = []
        self._post_response_middlewares: List[PostResponseMiddleware] = []

        # Simple metrics
        self.metrics = {"requests": 0, "successes": 0, "failures": 0}

    def add_pre_request_middleware(self, middleware: PreRequestMiddleware) -> None:
        """Register middleware to modify the request context before sending."""
        self._pre_request_middlewares.append(middleware)

    def add_post_response_middleware(self, middleware: PostResponseMiddleware) -> None:
        """Register middleware to process the response after receiving."""
        self._post_response_middlewares.append(middleware)

    def _full_url(self, endpoint: str) -> str:
        return f"{self.base_url}/{endpoint.lstrip('/')}"

    def _get_headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.auth.token}"}

    def _apply_pre_request_middlewares(self, context: Dict[str, Any]) -> Dict[str, Any]:
        for middleware in self._pre_request_middlewares:
            modified = middleware(context)
            if modified is not None:
                context = modified
            HelperFunctions.logger.debug(f"Context after {middleware.__name__}: {context}")
        return context

    def _apply_post_response_middlewares(self, response: Any) -> Any:
        for middleware in self._post_response_middlewares:
            modified = middleware(response)
            if modified is not None:
                response = modified
            HelperFunctions.logger.debug(f"Response after {middleware.__name__}: {getattr(response, 'status_code', 'N/A')}")
        return response

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(requests.RequestException),
        reraise=True
    )
    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        def do_request():
            url = self._full_url(endpoint)
            headers = self._get_headers()

            request_context = {
                "method": method,
                "url": url,
                "headers": headers,
                "kwargs": kwargs,
            }
            HelperFunctions.logger.debug(f"Initial request context: {request_context}")

            request_context = self._apply_pre_request_middlewares(request_context)

            HelperFunctions.logger.debug(
                f"Making {request_context['method']} request to {request_context['url']} with headers "
                f"{ {k: 'REDACTED' if k=='Authorization' else v for k, v in request_context['headers'].items()} } "
                f"and kwargs {request_context['kwargs']}"
            )
            response = self.session.request(
                request_context["method"],
                request_context["url"],
                headers=request_context["headers"],
                timeout=self.timeout,
                **request_context["kwargs"]
            )
            response.raise_for_status()
            HelperFunctions.logger.debug(f"Response received: {response.status_code}")

            response = self._apply_post_response_middlewares(response)
            return response.json()

        self.metrics["requests"] += 1
        try:
            result = self.circuit_breaker.call(do_request)
            self.metrics["successes"] += 1
            return result
        except Exception as e:
            self.metrics["failures"] += 1
            HelperFunctions.logger.error(f"Request failed: {str(e)}")
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

        request_context = {
            "method": "POST",
            "url": url,
            "headers": headers,
            "kwargs": {"json": payload, "timeout": self.timeout, "stream": True},
        }
        request_context = self._apply_pre_request_middlewares(request_context)

        try:
            with self.session.post(
                request_context["url"],
                headers=request_context["headers"],
                **request_context["kwargs"]
            ) as response:
                response.raise_for_status()
                response = self._apply_post_response_middlewares(response)
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

    def batch_infer(self, requests_list: List[Tuple[str, dict]], max_workers: int = 5) -> List[Dict[str, Any]]:
        """
        New Feature: Perform batch inference concurrently.
        
        :param requests_list: List of tuples, where each tuple is (model, data)
        :param max_workers: Maximum number of threads to use.
        :return: List of responses.
        """
        responses: List[Dict[str, Any]] = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_req = {
                executor.submit(self.infer, model, data): (model, data)
                for model, data in requests_list
            }
            for future in as_completed(future_to_req):
                model, _ = future_to_req[future]
                try:
                    result = future.result()
                    HelperFunctions.logger.debug(f"Batch inference succeeded for model {model}")
                    responses.append(result)
                except Exception as exc:
                    HelperFunctions.logger.error(f"Batch inference failed for model {model}: {exc}")
                    responses.append({"model": model, "error": str(exc)})
        return responses


# =============================================================================
# Asynchronous API Client with Additional Features
# =============================================================================
class AsyncFreeseekAPI:
    """
    Asynchronous API Client with added circuit breaker (synchronously wrapped),
    asynchronous batch inference, and metrics.
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.freeseek.com/v1",
        timeout: int = 30,
        max_retries: int = 3,
        backoff_factor: int = 1,
        circuit_failure_threshold: int = 3,
        circuit_recovery_timeout: int = 30
    ):
        self.auth = AuthManager(api_key)
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.client = httpx.AsyncClient(timeout=self.timeout)

        # For simplicity, we share the same circuit breaker for async requests.
        self.circuit_breaker = CircuitBreaker(failure_threshold=circuit_failure_threshold,
                                               recovery_timeout=circuit_recovery_timeout)

        self._pre_request_middlewares: List[PreRequestMiddleware] = []
        self._post_response_middlewares: List[PostResponseMiddleware] = []

        self.metrics = {"requests": 0, "successes": 0, "failures": 0}

    def add_pre_request_middleware(self, middleware: PreRequestMiddleware) -> None:
        self._pre_request_middlewares.append(middleware)

    def add_post_response_middleware(self, middleware: PostResponseMiddleware) -> None:
        self._post_response_middlewares.append(middleware)

    def _full_url(self, endpoint: str) -> str:
        return f"{self.base_url}/{endpoint.lstrip('/')}"

    def _get_headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.auth.token}"}

    async def _apply_pre_request_middlewares(self, context: Dict[str, Any]) -> Dict[str, Any]:
        for middleware in self._pre_request_middlewares:
            if asyncio.iscoroutinefunction(middleware):
                modified = await middleware(context)
            else:
                modified = middleware(context)
            if modified is not None:
                context = modified
            HelperFunctions.logger.debug(f"Async context after {middleware.__name__}: {context}")
        return context

    async def _apply_post_response_middlewares(self, response: Any) -> Any:
        for middleware in self._post_response_middlewares:
            if asyncio.iscoroutinefunction(middleware):
                modified = await middleware(response)
            else:
                modified = middleware(response)
            if modified is not None:
                response = modified
            HelperFunctions.logger.debug(f"Async response after {middleware.__name__}: {getattr(response, 'status_code', 'N/A')}")
        return response

    async def _async_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        async def do_request():
            url = self._full_url(endpoint)
            headers = self._get_headers()
            request_context = {
                "method": method,
                "url": url,
                "headers": headers,
                "kwargs": kwargs,
            }
            HelperFunctions.logger.debug(f"Initial async request context: {request_context}")

            request_context = await self._apply_pre_request_middlewares(request_context)

            HelperFunctions.logger.debug(
                f"Making async {request_context['method']} request to {request_context['url']} with headers "
                f"{ {k: 'REDACTED' if k=='Authorization' else v for k, v in request_context['headers'].items()} } and kwargs {request_context['kwargs']}"
            )
            response = await self.client.request(
                request_context["method"],
                request_context["url"],
                headers=request_context["headers"],
                **request_context["kwargs"]
            )
            response.raise_for_status()
            HelperFunctions.logger.debug(f"Async response received: {response.status_code}")

            response = await self._apply_post_response_middlewares(response)
            return response.json()

        self.metrics["requests"] += 1
        try:
            # Note: wrapping the async call in a synchronous circuit breaker call is not ideal;
            # for a production system, consider an async circuit breaker.
            result = self.circuit_breaker.call(lambda: asyncio.run(do_request()))
            self.metrics["successes"] += 1
            return result
        except Exception as e:
            self.metrics["failures"] += 1
            HelperFunctions.logger.error(f"Async request failed: {str(e)}")
            raise APIError(f"Async request failed: {str(e)}") from e

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

        request_context = {
            "method": "POST",
            "url": url,
            "headers": headers,
            "kwargs": {"json": payload},
        }
        request_context = await self._apply_pre_request_middlewares(request_context)

        try:
            async with self.client.stream("POST", request_context["url"],
                                          headers=request_context["headers"],
                                          json=payload) as response:
                response.raise_for_status()
                response = await self._apply_post_response_middlewares(response)
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

    async def async_batch_infer(self, requests_list: List[Tuple[str, dict]]) -> List[Dict[str, Any]]:
        """
        New Feature: Asynchronously perform batch inferences concurrently.
        
        :param requests_list: List of (model, data) tuples.
        :return: List of inference results.
        """
        tasks = []
        for model, data in requests_list:
            tasks.append(self.infer(model, data))
        results = await asyncio.gather(*tasks, return_exceptions=True)
        responses = []
        for (model, result) in zip([r[0] for r in requests_list], results):
            if isinstance(result, Exception):
                HelperFunctions.logger.error(f"Async batch inference failed for model {model}: {result}")
                responses.append({"model": model, "error": str(result)})
            else:
                responses.append(result)
        return responses

    async def aclose(self):
        """Close the underlying async client session."""
        await self.client.aclose()
