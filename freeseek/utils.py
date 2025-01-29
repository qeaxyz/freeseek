import logging
import json

class HelperFunctions:
    @staticmethod
    def setup_logging():
        logging.basicConfig(level=logging.INFO)
        logging.info("Logging setup complete.")

    @staticmethod
    def parse_json(response):
        try:
            return response.json()
        except json.JSONDecodeError:
            logging.error("Failed to decode JSON response.")
            return None

    @staticmethod
    def handle_error(error: Exception):
        logging.error(f"An error occurred: {str(error)}")
        return {"error": str(error)}
