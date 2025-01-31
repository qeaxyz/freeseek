import time
import requests
from typing import Optional
from .exceptions import AuthenticationError

class AuthManager:
    def __init__(self, api_key: str, auth_endpoint: str = "https://api.freeseek.com/auth"):
        self.api_key = api_key
        self.auth_endpoint = auth_endpoint
        self._token: Optional[str] = None
        self._token_expiry: float = 0.0

    @property
    def token(self) -> str:
        if time.time() > self._token_expiry:
            self.refresh_token()
        return self._token

    def refresh_token(self) -> None:
        """Refresh authentication token using API key"""
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
        except requests.RequestException as e:
            raise AuthenticationError(f"Authentication failed: {str(e)}") from e
        except KeyError as e:
            raise AuthenticationError("Invalid token response format") from e