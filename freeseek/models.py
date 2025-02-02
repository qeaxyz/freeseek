from functools import lru_cache
from typing import Dict, Any
from pydantic import BaseModel, ValidationError
from .exceptions import APIError, ModelValidationError
from .utils import HelperFunctions


class InferRequest(BaseModel):
    model: str
    data: dict


class ModelHandler:
    def __init__(self, api):
        self.api = api
        self.schema_cache = {}

    def _validate_input(self, model: str, data: dict) -> None:
        """Validate input data against model schema."""
        if model not in self.schema_cache:
            try:
                schema = self.api.get_model_schema(model)
                self.schema_cache[model] = schema.get("input_schema", {})
            except APIError as e:
                HelperFunctions.logger.warning(f"Failed to fetch schema for {model}: {str(e)}")
                return

        required_fields = self.schema_cache[model].get("required", [])
        for field in required_fields:
            if field not in data:
                raise ModelValidationError(f"Missing required field: {field}")

    def infer_model(self, model: str, data: dict, validate: bool = True) -> Dict[str, Any]:
        """Perform model inference with optional validation."""
        if validate:
            self._validate_input(model, data)
        return self.api.infer(model, data)

    @lru_cache(maxsize=32)
    def get_model_info(self, model: str) -> Dict[str, Any]:
        return self.api.get_model_info(model)

    def list_available_models(self) -> Dict[str, Any]:
        return self.api.list_models()