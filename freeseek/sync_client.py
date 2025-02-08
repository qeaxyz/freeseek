import json
import time
import uuid
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from typing import Dict, Any, Generator, Optional, Callable, Union, List, Tuple
from pydantic import BaseModel, ValidationError
from .auth import AuthManager
from .exceptions import APIError, RateLimitExceededError
from .utils import HelperFunctions, ContextLogger

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
    Synchronous API Client with added circuit breaker, metrics, and batch inference features.
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
        log_middlewares: bool = True,
        retry_stop_attempts: int = 3,
        retry_wait_min: int = 2,
        retry_wait_max: int = 10
    ):
        self.auth = AuthManager(api_key)
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=circuit_failure_threshold,
            recovery_timeout=circuit_recovery_timeout
        )
        self.retry_config = {
            "stop": stop_after_attempt(retry_stop_attempts),
            "wait": wait_exponential(multiplier=backoff_factor, min=retry_wait_min, max=retry_wait_max),
            "retry": retry_if_exception_type(requests.RequestException),
            "reraise": True,
        }
        self._pre_request_middlewares: List[PreRequestMiddleware] = []
        self._post_response_middlewares: List[PostResponseMiddleware] = []
        self.metrics = {"requests": 0, "successes": 0, "failures": 0}
        self.logger = ContextLogger(HelperFunctions.logger)
        self.log_middlewares = log_middlewares

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
            if self.log_middlewares:
                self.logger.debug(f"Context after {middleware.__name__}: {context}")
        return context

    def _apply_post_response_middlewares(self, response: Any) -> Any:
        for middleware in self._post_response_middlewares:
            modified = middleware(response)
            if modified is not None:
                response = modified
            if self.log_middlewares:
                self.logger.debug(f"Response after {middleware.__name__}: {getattr(response, 'status_code', 'N/A')}")
        return response

    @retry(**self.retry_config)
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
            request_id = str(uuid.uuid4())
            with self.log_context(request_id, kwargs.get("json", {}).get("model")):
                self.logger.info(
                    f"Making {request_context['method']} request to {request_context['url']} "
                    f"with headers { {k: 'REDACTED' if k == 'Authorization' else v for k, v in request_context['headers'].items()} } "
                    f"and kwargs {request_context['kwargs']}"
                )
                request_context = self._apply_pre_request_middlewares(request_context)
                response = self.session.request(
                    request_context["method"],
                    request_context["url"],
                    headers=request_context["headers"],
                    timeout=self.timeout,
                    **request_context["kwargs"]
                )
                response.raise_for_status()
                self.logger.info(f"Response received: {response.status_code}")
                response = self._apply_post_response_middlewares(response)
                return response.json()

        self.metrics["requests"] += 1
        try:
            result = self.circuit_breaker.call(do_request)
            self.metrics["successes"] += 1
            return result
        except Exception as e:
            self.metrics["failures"] += 1
            self.logger.error(f"Request failed: {str(e)}")
            raise APIError(
                f"Request failed: {str(e)}",
                status_code=getattr(e.response, "status_code", None),
                response_body=getattr(e.response, "text", None)
            ) from e

    @contextlib.contextmanager
    def log_context(self, request_id: str, model: str):
        """Context manager for setting and clearing logging context."""
        self.logger.set_context("request_id", request_id)
        self.logger.set_context("model", model)
        try:
            yield
        finally:
            self.logger.clear_context()

    def infer(self, model: str, data: dict) -> Dict[str, Any]:
        """
        Perform inference using the specified model and input data.
        """
        try:
            validated_request = InferRequest(model=model, data=data)
        except ValidationError as ve:
            self.logger.error(f"Validation error for infer request: {ve.json()}")
            raise APIError(f"Invalid input for inference: {ve}") from ve
        payload = validated_request.dict()
        return self._request("POST", "infer", json=payload)

    def stream_infer(self, model: str, data: dict) -> Generator[Dict[str, Any], None, None]:
        """
        Perform streaming inference and yield results incrementally.
        """
        try:
            validated_request = InferRequest(model=model, data=data)
        except ValidationError as ve:
            self.logger.error(f"Validation error for stream_infer request: {ve.json()}")
            raise APIError(f"Invalid input for streaming inference: {ve}") from ve
        url = self._full_url("infer")
        headers = self._get_headers()
        payload = validated_request.dict()
        request_id = str(uuid.uuid4())
        with self.log_context(request_id, model):
            self.logger.info(f"Starting streaming infer for URL: {url}")
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
                                self.logger.debug(f"Received chunk: {chunk}")
                                yield chunk
                            except json.JSONDecodeError as je:
                                self.logger.error(f"JSON decode error in streaming response: {str(je)}. Skipping line.")
                                continue
            except requests.HTTPError as e:
                self.logger.error(f"HTTP Error during streaming infer: {str(e)}")
                raise APIError(
                    f"HTTP Error during streaming infer: {str(e)}",
                    status_code=e.response.status_code
                ) from e
            except requests.RequestException as e:
                self.logger.error(f"Streaming request failed: {str(e)}")
                raise APIError(f"Streaming request failed: {str(e)}") from e

    def get_model_info(self, model: str) -> Dict[str, Any]:
        """
        Retrieve information about a specific model.
        """
        return self._request("GET", f"models/{model}")

    def get_model_schema(self, model: str) -> Dict[str, Any]:
        """
        Retrieve the schema for a specific model.
        """
        return self._request("GET", f"models/{model}/schema")

    def list_models(self) -> Dict[str, Any]:
        """
        List all available models.
        """
        return self._request("GET", "models")

    def batch_infer(self, requests_list: List[Tuple[str, dict]], max_workers: int = 5) -> List[Dict[str, Any]]:
        """
        Perform batch inference concurrently.
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
                    self.logger.debug(f"Batch inference succeeded for model {model}")
                    responses.append(result)
                except Exception as exc:
                    self.logger.error(f"Batch inference failed for model {model}: {type(exc).__name__}: {exc}")
                    responses.append({"model": model, "error": {"type": type(exc).__name__, "message": str(exc)}})
        return responses

    def close(self):
        """Close the underlying session."""
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()