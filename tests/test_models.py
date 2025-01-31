import unittest
from unittest.mock import patch
from freeseek.models import ModelHandler
from freeseek.api import FreeseekAPI

class TestModelHandler(unittest.TestCase):
    """Unit tests for the ModelHandler class."""

    @patch.object(FreeseekAPI, 'infer', return_value={"status": "success", "result": "mock_result"})
    def test_infer_model(self, mock_infer):
        """Test the infer_model method of ModelHandler."""
        api_instance = FreeseekAPI(api_key="mock_api_key")
        model_handler = ModelHandler(api_instance)
        
        input_data = {"input": "test_data"}
        result = model_handler.infer_model("v3", input_data)
        
        self.assertEqual(result, {"status": "success", "result": "mock_result"})
        mock_infer.assert_called_once_with("v3", input_data)

    @patch.object(FreeseekAPI, 'get_model_info', return_value={"model_name": "v3", "status": "available"})
    def test_get_model_info(self, mock_get_model_info):
        """Test the get_model_info method of ModelHandler."""
        api_instance = FreeseekAPI(api_key="mock_api_key")
        model_handler = ModelHandler(api_instance)
        
        result = model_handler.get_model_info("v3")
        
        self.assertEqual(result, {"model_name": "v3", "status": "available"})
        mock_get_model_info.assert_called_once_with("v3")

if __name__ == '__main__':
    unittest.main()