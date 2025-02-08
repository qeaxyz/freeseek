import uuid
from typing import List, Callable, Dict, Any, Optional

# Type aliases for middleware functions.
PreRequestMiddleware = Callable[[Dict[str, Any]], Optional[Dict[str, Any]]]
PostResponseMiddleware = Callable[[Any], Optional[Any]]

class MiddlewareHandler:
    """
    Handles pre-request and post-response middlewares.
    """
    def __init__(self):
        self.pre_request_middlewares: List[PreRequestMiddleware] = []
        self.post_response_middlewares: List[PostResponseMiddleware] = []

    def add_pre_request_middleware(self, middleware: PreRequestMiddleware) -> None:
        """
        Register a middleware to modify the request context before sending.
        """
        self.pre_request_middlewares.append(middleware)

    def add_post_response_middleware(self, middleware: PostResponseMiddleware) -> None:
        """
        Register a middleware to process the response after receiving.
        """
        self.post_response_middlewares.append(middleware)

    def process_pre_request(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the request context through all registered pre-request middlewares.
        """
        for middleware in self.pre_request_middlewares:
            try:
                modified = middleware(context)
                if modified is not None:
                    context = modified
            except Exception as e:
                HelperFunctions.logger.error(f"Pre-request middleware {middleware.__name__} failed: {str(e)}")
                raise APIError(f"Pre-request middleware failed: {str(e)}") from e
        return context

    def process_post_response(self, response: Any) -> Any:
        """
        Process the response through all registered post-response middlewares.
        """
        for middleware in self.post_response_middlewares:
            try:
                modified = middleware(response)
                if modified is not None:
                    response = modified
            except Exception as e:
                HelperFunctions.logger.error(f"Post-response middleware {middleware.__name__} failed: {str(e)}")
                raise APIError(f"Post-response middleware failed: {str(e)}") from e
        return response

    def close(self):
        """
        Clean up resources (if needed).
        """
        HelperFunctions.logger.info("MiddlewareHandler closed.")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class ContextLoggingMiddleware:
    """
    Middleware to attach contextual metadata to logs.
    """
    def __init__(self, logger):
        self.logger = logger

    def __call__(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Attach contextual metadata to logs.
        """
        request_id = str(uuid.uuid4())
        self.logger.info(
            f"Processing request with ID {request_id}",
            extra={"request_id": request_id, "model": context.get("model")}
        )
        return context