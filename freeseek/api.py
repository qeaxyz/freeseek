import requests
from .auth import AuthManager

class FreeseekAPI:
    def __init__(self, api_key: str):
        """
        Initialize the FreeseekAPI with an API key.
        
        :param api_key: The API key for authentication.
        """
        self.auth_manager = AuthManager(api_key)
        self.base_url = "https://api.freeseek.com/v1"

    def infer(self, model: str, data: dict) -> dict:
        """
        Perform inference using the specified model and data.
        
        :param model: The model to use for inference.
        :param data: The data to infer on.
        :return: The inference result as a dictionary.
        """
        endpoint = f"{self.base_url}/infer"
        headers = {"Authorization": f"Bearer {self.auth_manager.get_token()}"}
        try:
            response = requests.post(endpoint, json={"model": model, "data": data}, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"error": str(e)}

    def get_model_info(self, model: str) -> dict:
        """
        Get information about a specific model.
        
        :param model: The model to get information about.
        :return: The model information as a dictionary.
        """
        endpoint = f"{self.base_url}/models/{model}"
        headers = {"Authorization": f"Bearer {self.auth_manager.get_token()}"}
        try:
            response = requests.get(endpoint, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"error": str(e)}
