import asyncio
import httpx
import json
import uuid
import contextlib
from typing import Dict, Any, AsyncGenerator, List, Tuple
from .base_client import BaseClient
from .models import InferRequest
from .exceptions import APIError, RateLimitExceededError
from .utils import HelperFunctions, ContextLogger
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

class AsyncFreeseekAPI(BaseClient):
    """
    Asynchronous API Client with added circuit breaker, metrics, and batch inference features.
    """
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.freeseek.com/v1",
        timeout: int = 30,
        max_retries: int = 3,
        backoff_factor: int = 1,
        circuit_failure_threshold: int = 3,
        circuit_recovery_timeout: int = 30,
        retry_stop_attempts: int = 3,
        retry_wait_min: int = 2,
        retry_wait_max: int = 10,
        log_middlewares: bool = True
    ):
        """
        Initialize the asynchronous API client.
        """
        super().__init__(api_key, base_url, timeout)
        self.client = httpx.AsyncClient(timeout=self.timeout)
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.circuit_breaker = self._initialize_circuit_breaker(
            failure_threshold=circuit_failure_threshold,
            recovery_timeout=circuit_recovery_timeout
        )
        self.retry_config = {
            "stop": stop_after_attempt(retry_stop_attempts),
            "wait": wait_exponential(multiplier=backoff_factor, min=retry_wait_min, max=retry_wait_max),
            "retry": retry_if_exception_type(httpx.RequestError),
            "reraise": True,
        }
        self.logger = ContextLogger(HelperFunctions.logger)
        self.log_middlewares = log_middlewares

    def _initialize_circuit_breaker(self, failure_threshold: int, recovery_timeout: int):
        """
        Initialize the circuit breaker for handling repeated failures.
        """
        from .circuit_breaker import CircuitBreaker
        return CircuitBreaker(failure_threshold=failure_threshold, recovery_timeout=recovery_timeout)

    async def _apply_pre_request_middlewares(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply pre-request middlewares asynchronously.
        """
        for middleware in self._pre_request_middlewares:
            if asyncio.iscoroutinefunction(middleware):
                modified = await middleware(context)
            else:
                modified = middleware(context)
            if modified is not None:
                context = modified
            if self.log_middlewares:
                self.logger.debug(f"Async context after {middleware.__name__}: {context}")
        return context

    async def _apply_post_response_middlewares(self, response: httpx.Response) -> httpx.Response:
        """
        Apply post-response middlewares asynchronously.
        """
        for middleware in self._post_response_middlewares:
            if asyncio.iscoroutinefunction(middleware):
                modified = await middleware(response)
            else:
                modified = middleware(response)
            if modified is not None:
                response = modified
            if self.log_middlewares:
                self.logger.debug(f"Async response after {middleware.__name__}: {getattr(response, 'status_code', 'N/A')}")
        return response

    @retry(**self.retry_config)
    async def _async_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        Make an asynchronous HTTP request with retries, middleware, and circuit breaker.
        """
        async def do_request():
            url = self._full_url(endpoint)
            headers = self._get_headers()
            request_context = {
                "method": method,
                "url": url,
                "headers": headers,
                "kwargs": kwargs,
            }
            # Generate a unique request ID and set contextual metadata
            request_id = str(uuid.uuid4())
            async with self.log_context(request_id, kwargs.get("json", {}).get("model")):
                self.logger.info(f"Making async {request_context['method']} request to {request_context['url']}")
                request_context = await self._apply_pre_request_middlewares(request_context)
                try:
                    response = await self.client.request(
                        request_context["method"],
                        request_context["url"],
                        headers=request_context["headers"],
                        **request_context["kwargs"]
                    )
                    response.raise_for_status()
                    self.logger.info(f"Async response received: {response.status_code}")
                    response = await self._apply_post_response_middlewares(response)
                    return response.json()
                except Exception as e:
                    self.logger.error(f"Async request failed: {str(e)}")
                    raise APIError(
                        f"Async request failed: {str(e)}",
                        status_code=getattr(response, "status_code", None),
                        response_body=getattr(response, "text", None)
                    ) from e

        self.metrics["requests"] += 1
        try:
            result = await self.circuit_breaker.call(do_request)
            self.metrics["successes"] += 1
            self.logger.info(f"Circuit breaker state: {self.circuit_breaker.state}")
            return result
        except Exception as e:
            self.metrics["failures"] += 1
            self.logger.error(f"Circuit breaker state: {self.circuit_breaker.state}")
            raise

    @contextlib.asynccontextmanager
    async def log_context(self, request_id: str, model: str):
        """
        Context manager for setting and clearing logging context.
        """
        self.logger.set_context("request_id", request_id)
        self.logger.set_context("model", model)
        try:
            yield
        finally:
            self.logger.clear_context()

    async def infer(self, model: str, data: dict) -> Dict[str, Any]:
        """
        Perform inference using the specified model and input data.
        """
        try:
            validated_request = InferRequest(model=model, data=data)
        except ValidationError as ve:
            self.logger.error(f"Validation error for async infer: {ve.json()}")
            raise APIError(f"Invalid input for async inference: {ve}") from ve
        payload = validated_request.dict()
        return await self._async_request("POST", "infer", json=payload)

    async def stream_infer(self, model: str, data: dict) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Perform streaming inference and yield results incrementally.
        """
        try:
            validated_request = InferRequest(model=model, data=data)
        except ValidationError as ve:
            self.logger.error(f"Validation error for async stream_infer: {ve.json()}")
            raise APIError(f"Invalid input for async streaming inference: {ve}") from ve
        url = self._full_url("infer")
        headers = self._get_headers()
        payload = validated_request.dict()
        request_id = str(uuid.uuid4())
        async with self.log_context(request_id, model):
            self.logger.info(f"Starting async streaming infer for URL: {url}")
            request_context = {
                "method": "POST",
                "url": url,
                "headers": headers,
                "kwargs": {"json": payload},
            }
            request_context = await self._apply_pre_request_middlewares(request_context)
            try:
                async with self.client.stream(
                    request_context["method"],
                    request_context["url"],
                    headers=request_context["headers"],
                    **request_context["kwargs"]
                ) as response:
                    response.raise_for_status()
                    response = await self._apply_post_response_middlewares(response)
                    async for line in response.aiter_lines():
                        if line:
                            try:
                                chunk = json.loads(line)
                                self.logger.debug(f"Received async chunk: {chunk}")
                                yield chunk
                            except json.JSONDecodeError as je:
                                self.logger.error(f"Async JSON decode error: {str(je)}. Skipping line.")
                                continue
            except (httpx.HTTPStatusError, httpx.RequestError) as e:
                self.logger.error(f"Async streaming request error: {str(e)}")
                raise APIError(f"Async streaming request failed: {str(e)}") from e

    async def get_model_info(self, model: str) -> Dict[str, Any]:
        """
        Retrieve information about a specific model.
        """
        return await self._async_request("GET", f"models/{model}")

    async def get_model_schema(self, model: str) -> Dict[str, Any]:
        """
        Retrieve the schema for a specific model.
        """
        return await self._async_request("GET", f"models/{model}/schema")

    async def list_models(self) -> Dict[str, Any]:
        """
        List all available models.
        """
        return await self._async_request("GET", "models")

    async def async_batch_infer(self, requests_list: List[Tuple[str, dict]]) -> List[Dict[str, Any]]:
        """
        Perform batch inference concurrently using asyncio tasks.
        """
        tasks = [self.infer(model, data) for model, data in requests_list]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        responses = []
        for (model, data), result in zip(requests_list, results):
            if isinstance(result, Exception):
                self.logger.error(f"Async batch inference failed for model {model}: {type(result).__name__}: {result}")
                responses.append({"model": model, "error": {"type": type(result).__name__, "message": str(result)}})
            else:
                responses.append(result)
        return responses

    async def aclose(self):
        """
        Close the underlying async client session.
        """
        await self.client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.aclose()