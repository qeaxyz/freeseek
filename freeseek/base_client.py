# base_client.py
import time
from typing import Dict, Any, List, Callable, Optional
from .exceptions import APIError
from .utils import HelperFunctions

PreRequestMiddleware = Callable[[Dict[str, Any]], Optional[Dict[str, Any]]]
PostResponseMiddleware = Callable[[Any], Optional[Any]]

class BaseClient:
    def __init__(self, api_key: str, base_url: str, timeout: int):
        self.auth = AuthManager(api_key)
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._pre_request_middlewares: List[PreRequestMiddleware] = []
        self._post_response_middlewares: List[PostResponseMiddleware] = []
        self.metrics = {"requests": 0, "successes": 0, "failures": 0}
        self.optimizer = AdaptiveQueryOptimizer()

    def infer(self, model, data):
        optimized_model, optimized_data = self.optimizer.process_request(model, data)
        return self._send_request(optimized_model, optimized_data)

    def _full_url(self, endpoint: str) -> str:
        return f"{self.base_url}/{endpoint.lstrip('/')}"

    def _get_headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.auth.token}"}

    def add_pre_request_middleware(self, middleware: PreRequestMiddleware) -> None:
        self._pre_request_middlewares.append(middleware)

    def add_post_response_middleware(self, middleware: PostResponseMiddleware) -> None:
        self._post_response_middlewares.append(middleware)

    def _apply_pre_request_middlewares(self, context: Dict[str, Any]) -> Dict[str, Any]:
        for middleware in self._pre_request_middlewares:
            modified = middleware(context)
            if modified is not None:
                context = modified
        return context

    def _apply_post_response_middlewares(self, response: Any) -> Any:
        for middleware in self._post_response_middlewares:
            modified = middleware(response)
            if modified is not None:
                response = modified
        return response