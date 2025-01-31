import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from typing import Dict, Any
from .auth import AuthManager
from .exceptions import APIError

class FreeseekAPI:
    def __init__(self, api_key: str, base_url: str = "https://api.freeseek.com/v1"):
        self.auth = AuthManager(api_key)
        self.base_url = base_url
        self.session = requests.Session()
        self.timeout = 30  # seconds

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(requests.RequestException),
        reraise=True
    )
    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = {"Authorization": f"Bearer {self.auth.token}"}
        
        try:
            response = self.session.request(
                method,
                url,
                headers=headers,
                timeout=self.timeout,
                **kwargs
            )
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as e:
            raise APIError(f"HTTP Error: {str(e)}", status_code=e.response.status_code) from e
        except requests.RequestException as e:
            raise APIError(f"Request failed: {str(e)}") from e

    def infer(self, model: str, data: dict) -> Dict[str, Any]:
        return self._request("POST", "infer", json={"model": model, "data": data})

    def get_model_info(self, model: str) -> Dict[str, Any]:
        return self._request("GET", f"models/{model}")

    def get_model_schema(self, model: str) -> Dict[str, Any]:
        return self._request("GET", f"models/{model}/schema")

    def list_models(self) -> Dict[str, Any]:
        return self._request("GET", "models")