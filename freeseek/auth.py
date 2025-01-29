import time

class AuthManager:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.token = None
        self.token_expiry = None

    def get_token(self):
        if not self.token or time.time() > self.token_expiry:
            self.refresh_token()
        return self.token

    def refresh_token(self):
        self.token = "new_token_based_on_api_key"
        self.token_expiry = time.time() + 3600
