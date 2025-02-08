import time
import requests
from typing import Optional
from threading import Lock
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
        self._lock = Lock()  # For thread safety during token refresh

    @property
    def token(self) -> str:
        """
        Get the current authentication token. Refreshes the token if it's expired or nearing expiry.
        """
        with self._lock:  # Ensure thread-safe access to token
            if (not self._token) or (time.time() > self._token_expiry - self.TOKEN_GRACE_PERIOD):
                HelperFunctions.logger.debug("Token expired, missing, or nearing expiry; refreshing token.")
                self.refresh_token()
            return self._token

    def refresh_token(self) -> None:
        """
        Refresh the authentication token using the API key.
        """
        HelperFunctions.logger.info("Attempting to refresh authentication token.")
        try:
            # Retry logic for transient errors
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = requests.post(
                        self.auth_endpoint,
                        json={"api_key": self.api_key},
                        timeout=10
                    )
                    response.raise_for_status()  # Raise HTTP errors
                    break  # Exit retry loop if successful
                except requests.RequestException as e:
                    if attempt == max_retries - 1:  # Last attempt failed
                        raise
                    HelperFunctions.logger.warning(f"Retry {attempt + 1} after failure: {str(e)}")
                    time.sleep(2 ** attempt)  # Exponential backoff

            # Parse token response
            token_data = response.json()
            self._token = token_data["access_token"]
            self._token_expiry = time.time() + token_data["expires_in"]
            HelperFunctions.logger.info("Successfully refreshed auth token.")

        except requests.Timeout as e:
            HelperFunctions.logger.error("Authentication request timed out.")
            raise AuthenticationError("Authentication request timed out.") from e

        except requests.ConnectionError as e:
            HelperFunctions.logger.error("Connection error during authentication.")
            raise AuthenticationError("Connection error during authentication.") from e

        except requests.HTTPError as e:
            HelperFunctions.logger.error(f"HTTP error during authentication: {response.status_code} - {response.text}")
            raise AuthenticationError(f"HTTP error during authentication: {response.status_code}") from e

        except KeyError as e:
            HelperFunctions.logger.error("Invalid token response format.")
            raise AuthenticationError("Invalid token response format.") from e

        except Exception as e:
            HelperFunctions.logger.error(f"Unexpected error during token refresh: {str(e)}")
            raise AuthenticationError("Unexpected error during token refresh.") from e