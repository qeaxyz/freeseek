class FreeseekError(Exception):
    """Base exception for all Freeseek exceptions"""
    pass

class APIError(FreeseekError):
    """Exception raised for API-related errors"""
    def __init__(self, message, status_code: int = None):
        super().__init__(message)
        self.status_code = status_code

class AuthenticationError(FreeseekError):
    """Exception raised for authentication failures"""
    pass

class ModelValidationError(FreeseekError):
    """Exception raised for invalid model inputs"""
    pass