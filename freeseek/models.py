from functools import lru_cache
from typing import Dict, Any, List
from pydantic import BaseModel, ValidationError
from .exceptions import APIError, ModelValidationError
from .utils import HelperFunctions

class InferRequest(BaseModel):
    model: str
    data: Dict[str, Any]

class ModelHandler:
    def __init__(self, api):
        self.api = api
        self.schema_cache: Dict[str, Dict[str, Any]] = {}

    def _fetch_model_schema(self, model: str) -> Dict[str, Any]:
        """Fetch and cache the schema for a given model."""
        if model not in self.schema_cache:
            try:
                schema = self.api.get_model_schema(model)
                self.schema_cache[model] = schema.get("input_schema", {})
            except APIError as e:
                HelperFunctions.logger.warning(f"Failed to fetch schema for {model}: {str(e)}")
                raise APIError(f"Could not fetch schema for {model}") from e
        return self.schema_cache[model]

    def _validate_input(self, model: str, data: Dict[str, Any]) -> None:
        """Validate input data against model schema."""
        schema = self._fetch_model_schema(model)
        required_fields = set(schema.get("required", []))

        missing_fields = required_fields - data.keys()
        if missing_fields:
            raise ModelValidationError(f"Missing required fields: {', '.join(missing_fields)}")

    def infer_model(self, model: str, data: Dict[str, Any], validate: bool = True) -> Dict[str, Any]:
        """Perform model inference with optional validation."""
        if validate:
            self._validate_input(model, data)
        return self.api.infer(model, data)

    @lru_cache(maxsize=32)
    def get_model_info(self, model: str) -> Dict[str, Any]:
        """Retrieve model metadata with caching."""
        return self.api.get_model_info(model)

    def list_available_models(self) -> List[str]:
        """Return a list of available models."""
        return self.api.list_models()
