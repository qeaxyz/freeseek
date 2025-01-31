import logging
import json
from typing import Any, Dict, Optional

class HelperFunctions:
    @staticmethod
    def setup_logging(level: int = logging.INFO, log_format: str = '%(asctime)s - %(levelname)s - %(message)s') -> None:
        logging.basicConfig(level=level, format=log_format)
        logging.info("Logging setup complete.")

    @staticmethod
    def parse_json(response: Any) -> Optional[Dict[str, Any]]:
        try:
            return response.json()
        except json.JSONDecodeError as e:
            logging.error(f"Failed to decode JSON response: {str(e)}")
        except AttributeError as e:
            logging.error(f"Invalid response object: {str(e)}")
        return None

    @staticmethod
    def handle_error(error: Exception) -> Dict[str, str]:
        logging.error(f"An error occurred: {str(error)}")
        return {"error": str(error)}
