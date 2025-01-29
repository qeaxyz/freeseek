import requests
from .auth import AuthManager

class FreeseekAPI:
    def __init__(self, api_key: str):
        self.auth_manager = AuthManager(api_key)
        self.base_url = "https://api.freeseek.com/v1"

    def infer(self, model: str, data: dict):
        endpoint = f"{self.base_url}/infer"
        headers = {"Authorization": f"Bearer {self.auth_manager.get_token()}"}
        response = requests.post(endpoint, json={"model": model, "data": data}, headers=headers)
        return response.json()

    def get_model_info(self, model: str):
        endpoint = f"{self.base_url}/models/{model}"
        headers = {"Authorization": f"Bearer {self.auth_manager.get_token()}"}
        response = requests.get(endpoint, headers=headers)
        return response.json()
