from typing import List, Callable, Dict, Any

class MiddlewarePipeline:
    def __init__(self):
        self.pre_request_middlewares: List[Callable] = []
        self.post_response_middlewares: List[Callable] = []

    def add_pre_request_middleware(self, middleware: Callable):
        self.pre_request_middlewares.append(middleware)

    def add_post_response_middleware(self, middleware: Callable):
        self.post_response_middlewares.append(middleware)

    def process_pre_request(self, context: Dict[str, Any]) -> Dict[str, Any]:
        for middleware in self.pre_request_middlewares:
            context = middleware(context)
        return context

    def process_post_response(self, response: Any) -> Any:
        for middleware in self.post_response_middlewares:
            response = middleware(response)
        return response