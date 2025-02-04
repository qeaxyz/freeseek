import time
import requests
from typing import Optional
from .exceptions import AuthenticationError
from .utils import HelperFunctions

class AuthManager:
    # Preemptively refresh token if it is within this many seconds of expiring.
    TOKEN_GRACE_PERIOD = 300  # 5 minutes

    def __init__(self, api_key: str, auth_endpoint: str = "https://api.freeseek.com/auth"):
        self.api_key = api_key
        self.auth_endpoint = auth_endpoint
        self._token: Optional[str] = None
        self._token_expiry: float = 0.0

    @property
    def token(self) -> str:
        if (not self._token) or (time.time() > self._token_expiry - self.TOKEN_GRACE_PERIOD):
            HelperFunctions.logger.debug("Token expired, missing, or nearing expiry; refreshing token.")
            self.refresh_token()
        return self._token

    def refresh_token(self) -> None:
        """Refresh authentication token using API key."""
        try:
            response = requests.post(
                self.auth_endpoint,
                json={"api_key": self.api_key},
                timeout=10
            )
            response.raise_for_status()
            token_data = response.json()
            self._token = token_data["access_token"]
            self._token_expiry = time.time() + token_data["expires_in"]
            HelperFunctions.logger.info("Successfully refreshed auth token.")
        except requests.RequestException as e:
            HelperFunctions.logger.error(f"Authentication request failed: {str(e)}")
            raise AuthenticationError(f"Authentication failed: {str(e)}") from e
        except KeyError as e:
            HelperFunctions.logger.error("Invalid token response format")
            raise AuthenticationError("Invalid token response format") from e
