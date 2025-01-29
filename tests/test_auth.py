import unittest
from freeseek.auth import AuthManager
from unittest.mock import patch

class TestAuthManager(unittest.TestCase):

    @patch('time.time', return_value=1000)
    @patch('freeseek.auth.AuthManager.refresh_token')
    def test_token_refresh_on_expiry(self, mock_refresh_token, mock_time):
        auth_manager = AuthManager(api_key="mock_api_key")
        auth_manager.token = "old_token"
        auth_manager.token_expiry = 999  # Simulate expired token
        
        token = auth_manager.get_token()
        
        self.assertEqual(token, "new_token_based_on_api_key")
        mock_refresh_token.assert_called_once()

    @patch('time.time', return_value=1000)
    def test_no_refresh_needed(self, mock_time):
        auth_manager = AuthManager(api_key="mock_api_key")
        auth_manager.token = "valid_token"
        auth_manager.token_expiry = 2000  # Token is still valid
        
        token = auth_manager.get_token()
        
        self.assertEqual(token, "valid_token")

if __name__ == '__main__':
    unittest.main()