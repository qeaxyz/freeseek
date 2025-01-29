from freeseek import FreeseekAPI, ModelHandler, HelperFunctions

HelperFunctions.setup_logging()
api = FreeseekAPI(api_key="your_api_key_here")
model_handler = ModelHandler(api)
data = {"input": "test_data"}

try:
    response = model_handler.infer_model("v3", data)
    print("Inference Response:", response)
except Exception as e:
    HelperFunctions.handle_error(e)
