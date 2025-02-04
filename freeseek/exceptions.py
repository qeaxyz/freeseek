# exceptions.py
class FreeseekError(Exception):
    """Base exception for all Freeseek exceptions."""
    pass

class APIError(FreeseekError):
    """Exception raised for API-related errors."""
    def __init__(self, message: str, status_code: int = None, extra_info: Dict[str, Any] = None):
        super().__init__(message)
        self.status_code = status_code
        self.extra_info = extra_info

class AuthenticationError(FreeseekError):
    """Exception raised for authentication failures."""
    pass

class ModelValidationError(FreeseekError):
    """Exception raised for invalid model inputs."""
    pass

class RateLimitExceededError(APIError):
    """Exception raised when rate limits are exceeded."""
    pass

class MiddlewareError(FreeseekError):
    """Exception raised for middleware errors."""
    pass