import unittest
from freeseek.auth import AuthManager
from unittest.mock import patch

class TestAuthManager(unittest.TestCase):

    def setUp(self):
        self.api_key = "mock_api_key"
        self.auth_manager = AuthManager(api_key=self.api_key)

    @patch('time.time', return_value=1000)
    @patch('freeseek.auth.AuthManager.refresh_token')
    def test_token_refresh_on_expiry(self, mock_refresh_token, mock_time):
        """Test that the token is refreshed when it has expired."""
        self.auth_manager.token = "old_token"
        self.auth_manager.token_expiry = 999  # Simulate expired token
        
        token = self.auth_manager.get_token()
        
        self.assertEqual(token, "new_token_based_on_api_key")
        mock_refresh_token.assert_called_once()

    @patch('time.time', return_value=1000)
    def test_no_refresh_needed(self, mock_time):
        """Test that the token is not refreshed when it is still valid."""
        self.auth_manager.token = "valid_token"
        self.auth_manager.token_expiry = 2000  # Token is still valid
        
        token = self.auth_manager.get_token()
        
        self.assertEqual(token, "valid_token")

if __name__ == '__main__':
    unittest.main()