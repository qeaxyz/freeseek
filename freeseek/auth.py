import time
import secrets

class AuthManager:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.token: str = ""
        self.token_expiry: float = 0.0

    def get_token(self) -> str:
        if not self.token or time.time() > self.token_expiry:
            self.refresh_token()
        return self.token

    def refresh_token(self) -> None:
        try:
            # Simulate token generation based on the API key
            self.token = secrets.token_hex(16)  # Generates a secure token
            self.token_expiry = time.time() + 3600  # Token valid for 1 hour
        except Exception as e:
            print(f"Failed to refresh token: {e}")
            self.token = ""
            self.token_expiry = 0.0
