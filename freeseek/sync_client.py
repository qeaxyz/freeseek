import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from typing import Dict, Any, List, Tuple
from .base_client import BaseClient
from .models import InferRequest
from .exceptions import APIError, RateLimitExceededError
from .utils import HelperFunctions

class FreeseekAPI(BaseClient):
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
        circuit_recovery_timeout: int = 30
    ):
        """
        Initialize the synchronous API client.
        """
        super().__init__(api_key, base_url, timeout)
        self.session = requests.Session()
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.circuit_breaker = self._initialize_circuit_breaker(
            failure_threshold=circuit_failure_threshold,
            recovery_timeout=circuit_recovery_timeout
        )

    def _initialize_circuit_breaker(self, failure_threshold: int, recovery_timeout: int):
        """
        Initialize the circuit breaker for handling repeated failures.
        """
        from .circuit_breaker import CircuitBreaker
        return CircuitBreaker(failure_threshold=failure_threshold, recovery_timeout=recovery_timeout)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(requests.RequestException),
        reraise=True
    )
    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        Make a synchronous HTTP request with retries, middleware, and circuit breaker.
        """
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
                f"Making {request_context['method']} request to {request_context['url']} "
                f"with headers { {k: 'REDACTED' if k == 'Authorization' else v for k, v in request_context['headers'].items()} } "
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
        """
        Perform inference using the specified model and input data.
        """
        try:
            validated_request = InferRequest(model=model, data=data)
        except ValidationError as ve:
            HelperFunctions.logger.error(f"Validation error for infer request: {ve.json()}")
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
        Perform batch inference concurrently using multiple threads.
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed

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