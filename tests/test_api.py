import unittest
from unittest.mock import patch, MagicMock
from freeseek.api import FreeseekAPI
from freeseek.auth import AuthManager

class TestFreeseekAPI(unittest.TestCase):

    @patch.object(AuthManager, 'get_token', return_value='mock_token')
    @patch('requests.post')
    def test_infer(self, mock_post, mock_get_token):
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "success", "result": "mock_result"}
        mock_post.return_value = mock_response
        
        api = FreeseekAPI(api_key="mock_api_key")
        data = {"input": "test_data"}
        result = api.infer("v3", data)
        
        self.assertEqual(result, {"status": "success", "result": "mock_result"})
        mock_post.assert_called_once_with(
            "https://api.freeseek.com/v1/infer", 
            json={"model": "v3", "data": data}, 
            headers={"Authorization": "Bearer mock_token"}
        )

    @patch.object(AuthManager, 'get_token', return_value='mock_token')
    @patch('requests.get')
    def test_get_model_info(self, mock_get, mock_get_token):
        mock_response = MagicMock()
        mock_response.json.return_value = {"model_name": "v3", "status": "available"}
        mock_get.return_value = mock_response
        
        api = FreeseekAPI(api_key="mock_api_key")
        result = api.get_model_info("v3")
        
        self.assertEqual(result, {"model_name": "v3", "status": "available"})
        mock_get.assert_called_once_with(
            "https://api.freeseek.com/v1/models/v3", 
            headers={"Authorization": "Bearer mock_token"}
        )

if __name__ == '__main__':
    unittest.main()