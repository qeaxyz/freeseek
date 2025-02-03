import logging
import json
from typing import Optional, Dict, Any
from functools import wraps
from .exceptions import APIError
from cryptography.fernet import Fernet

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
        """Configure logging with optional file output."""
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