import logging
from typing import List, Tuple
from sync_client import FreeseekAPI, InferRequest

# Configure logging for better visibility
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Mock logger for demonstration purposes
class HelperFunctions:
    logger = logging.getLogger("ExampleLogger")

# Example middleware for logging request context
def example_pre_request_middleware(context: dict) -> dict:
    """
    Example pre-request middleware that logs the request method and URL.
    """
    HelperFunctions.logger.info(f"Pre-request middleware processing: {context['method']} {context['url']}")
    return context

# Example middleware for logging response status code
def example_post_response_middleware(response: dict) -> dict:
    """
    Example post-response middleware that logs the response status code.
    """
    HelperFunctions.logger.info(f"Post-response middleware received status code: {response.get('status_code', 'N/A')}")
    return response

# Example usage of the FreeseekAPI client
def main():
    # Initialize the API client
    api_key = "your_api_key_here"
    client = FreeseekAPI(api_key=api_key)

    # Add example middlewares
    client.add_pre_request_middleware(example_pre_request_middleware)
    client.add_post_response_middleware(example_post_response_middleware)

    try:
        # Perform a single inference request
        model_name = "example_model"
        input_data = {"input": "test data"}
        HelperFunctions.logger.info(f"Performing inference for model: {model_name}")
        result = client.infer(model=model_name, data=input_data)
        HelperFunctions.logger.info(f"Inference result: {result}")

        # Perform batch inference
        requests_list: List[Tuple[str, dict]] = [
            ("model_1", {"input": "data_1"}),
            ("model_2", {"input": "data_2"}),
            ("model_3", {"input": "data_3"})
        ]
        HelperFunctions.logger.info("Performing batch inference...")
        batch_results = client.batch_infer(requests_list, max_workers=3)
        HelperFunctions.logger.info(f"Batch inference results: {batch_results}")

    except Exception as e:
        HelperFunctions.logger.error(f"An error occurred: {str(e)}")
    finally:
        # Clean up resources
        client.close()

if __name__ == "__main__":
    main()