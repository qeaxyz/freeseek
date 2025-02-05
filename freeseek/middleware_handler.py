from typing import List, Callable, Dict, Any

PreRequestMiddleware = Callable[[Dict[str, Any]], Optional[Dict[str, Any]]]
PostResponseMiddleware = Callable[[Any], Optional[Any]]

class MiddlewareHandler:
    def __init__(self):
        self.pre_request_middlewares: List[PreRequestMiddleware] = []
        self.post_response_middlewares: List[PostResponseMiddleware] = []

    def add_pre_request_middleware(self, middleware: PreRequestMiddleware) -> None:
        self.pre_request_middlewares.append(middleware)

    def add_post_response_middleware(self, middleware: PostResponseMiddleware) -> None:
        self.post_response_middlewares.append(middleware)

    def process_pre_request(self, context: Dict[str, Any]) -> Dict[str, Any]:
        for middleware in self.pre_request_middlewares:
            modified = middleware(context)
            if modified is not None:
                context = modified
        return context

    def process_post_response(self, response: Any) -> Any:
        for middleware in self.post_response_middlewares:
            modified = middleware(response)
            if modified is not None:
                response = modified
        return response

class ContextLoggingMiddleware:
    def __call__(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Middleware to attach contextual metadata to logs.
        """
        request_id = str(uuid.uuid4())
        HelperFunctions.logger.info(
            f"Processing request with ID {request_id}",
            extra={"request_id": request_id, "model": context.get("model")}
        )
        return context