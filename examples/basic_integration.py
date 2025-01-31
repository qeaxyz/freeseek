import os
from freeseek import FreeseekAPI, ModelHandler, HelperFunctions

# Setup logging
HelperFunctions.setup_logging()

# Retrieve API key from environment variables
api_key = os.getenv("FREESEEK_API_KEY")
if not api_key:
    raise ValueError("API key not found. Please set the FREESEEK_API_KEY environment variable.")

# Initialize API and ModelHandler
api = FreeseekAPI(api_key=api_key)
model_handler = ModelHandler(api)

# Prepare data for inference
data = {"input": "test_data"}

try:
    # Perform model inference
    response = model_handler.infer_model("v3", data)
    print("Inference Response:", response)
except Exception as e:
    # Handle errors
    HelperFunctions.handle_error(e)
    print(f"An error occurred during model inference: {e}")
