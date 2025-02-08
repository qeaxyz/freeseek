from typing import Dict, Any, Optional

class FreeseekError(Exception):
    """Base exception for all Freeseek exceptions."""
    pass

class APIError(FreeseekError):
    """Exception raised for API-related errors."""
    def __init__(self, message: str, status_code: Optional[int] = None, extra_info: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.status_code = status_code
        self.extra_info = extra_info or {}

    def __repr__(self):
        return f"APIError(status_code={self.status_code}, message={self.args[0]}, extra_info={self.extra_info})"

class AuthenticationError(FreeseekError):
    """Exception raised for authentication failures."""
    def __init__(self, message: str = "Authentication failed", reason: Optional[str] = None):
        super().__init__(message)
        self.reason = reason

    def __str__(self):
        return f"{self.args[0]} - Reason: {self.reason}" if self.reason else self.args[0]

class ModelValidationError(FreeseekError):
    """Exception raised for invalid model inputs."""
    def __init__(self, message: str = "Model validation failed", errors: Optional[Dict[str, str]] = None):
        super().__init__(message)
        self.errors = errors or {}

    def __str__(self):
        return f"{self.args[0]} - Errors: {self.errors}" if self.errors else self.args[0]

class RateLimitExceededError(APIError):
    """Exception raised when rate limits are exceeded."""
    def __init__(self, message: str = "Rate limit exceeded", status_code: int = 429, extra_info: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code, extra_info)

class MiddlewareError(FreeseekError):
    """Exception raised for middleware errors."""
    pass
