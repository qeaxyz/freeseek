import unittest
from unittest.mock import patch, MagicMock
from freeseek.models import ModelHandler
from freeseek.api import FreeseekAPI

class TestModelHandler(unittest.TestCase):

    @patch.object(FreeseekAPI, 'infer', return_value={"status": "success", "result": "mock_result"})
    def test_infer_model(self, mock_infer):
        api = FreeseekAPI(api_key="mock_api_key")
        model_handler = ModelHandler(api)
        
        data = {"input": "test_data"}
        result = model_handler.infer_model("v3", data)
        
        self.assertEqual(result, {"status": "success", "result": "mock_result"})
        mock_infer.assert_called_once_with("v3", data)

    @patch.object(FreeseekAPI, 'get_model_info', return_value={"model_name": "v3", "status": "available"})
    def test_get_model_info(self, mock_get_model_info):
        api = FreeseekAPI(api_key="mock_api_key")
        model_handler = ModelHandler(api)
        
        result = model_handler.get_model_info("v3")
        
        self.assertEqual(result, {"model_name": "v3", "status": "available"})
        mock_get_model_info.assert_called_once_with("v3")

if __name__ == '__main__':
    unittest.main()