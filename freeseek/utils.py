import logging
import json
from typing import Optional, Dict, Any
from functools import wraps
import time
from cryptography.fernet import Fernet

# Custom Exception (Assuming it's defined in a separate file)
class APIError(Exception):
    pass

class Encryptor:
    def __init__(self, key: bytes):
        self.cipher_suite = Fernet(key)

    def encrypt(self, data: str) -> bytes:
        return self.cipher_suite.encrypt(data.encode())

    def decrypt(self, encrypted_data: bytes) -> str:
        return self.cipher_suite.decrypt(encrypted_data).decode()

class HelperFunctions:
    logger = logging.getLogger("freeseek")

    @staticmethod
    def setup_logging(level: int = logging.INFO, log_file: Optional[str] = None):
        handlers = [logging.StreamHandler()]
        if log_file:
            handlers.append(logging.FileHandler(log_file))
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=handlers
        )
        HelperFunctions.logger.info("Logging configured")

    @staticmethod
    def handle_api_error(func):
        """Decorator for handling API errors."""
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except APIError as e:
                HelperFunctions.logger.error(f"API Error: {str(e)}")
                raise
            except Exception as e:
                HelperFunctions.logger.error(f"Unexpected error: {str(e)}")
                raise APIError("Internal error occurred") from e
        return wrapper

    @staticmethod
    def validate_json(payload: str) -> bool:
        """Validate JSON string format."""
        try:
            json.loads(payload)
            return True
        except json.JSONDecodeError:
            return False

class RateLimitHandler:
    def __init__(self):
        self.rate_limit_remaining = float('inf')
        self.rate_limit_reset_time = 0

    def update_rate_limits(self, headers: Dict[str, str]):
        """Update rate limit information from response headers."""
        try:
            self.rate_limit_remaining = int(headers.get('X-RateLimit-Remaining', float('inf')))
            self.rate_limit_reset_time = int(headers.get('X-RateLimit-Reset', 0))
            logging.debug(f"Updated rate limits: Remaining={self.rate_limit_remaining}, Reset={self.rate_limit_reset_time}")
        except ValueError:
            logging.warning("Failed to parse rate limit headers")

    def should_wait(self) -> bool:
        """Check if we should wait before making another request."""
        current_time = time.time()
        if self.rate_limit_remaining <= 1 and current_time < self.rate_limit_reset_time:
            return True
        return False

    def wait_until_reset(self):
        """Wait until the rate limit resets."""
        current_time = time.time()
        sleep_time = max(0, self.rate_limit_reset_time - current_time)
        logging.info(f"Rate limit exceeded. Sleeping for {sleep_time} seconds.")
        time.sleep(sleep_time)

class ContextLogger:
    """
    Logger with dynamic contextual metadata support.
    """
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.context: Dict[str, Any] = {}

    def set_context(self, key: str, value: Any):
        """
        Add or update contextual metadata.
        """
        self.context[key] = value

    def clear_context(self):
        """
        Clear all contextual metadata.
        """
        self.context.clear()

    def log(self, level: int, message: str, extra: Optional[Dict[str, Any]] = None):
        """
        Log a message with contextual metadata.
        """
        combined_extra = {**self.context, **(extra or {})}
        self.logger.log(level, message, extra=combined_extra)

    def debug(self, message: str, extra: Optional[Dict[str, Any]] = None):
        self.log(logging.DEBUG, message, extra)

    def info(self, message: str, extra: Optional[Dict[str, Any]] = None):
        self.log(logging.INFO, message, extra)

    def warning(self, message: str, extra: Optional[Dict[str, Any]] = None):
        self.log(logging.WARNING, message, extra)

    def error(self, message: str, extra: Optional[Dict[str, Any]] = None):
        self.log(logging.ERROR, message, extra)

    def critical(self, message: str, extra: Optional[Dict[str, Any]] = None):
        self.log(logging.CRITICAL, message, extra)