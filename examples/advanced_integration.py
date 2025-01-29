from freeseek import FreeseekAPI, ModelHandler, HelperFunctions

HelperFunctions.setup_logging()

api = FreeseekAPI(api_key="your_api_key_here")

model_handler = ModelHandler(api)

batch_data = [
    {"input": "data_point_1"},
    {"input": "data_point_2"},
    {"input": "data_point_3"}
]

try:
    batch_responses = []
    for data in batch_data:
        response = model_handler.infer_model("v3", data)
        batch_responses.append(response)

    print("Batch Inference Responses:", batch_responses)
except Exception as e:
    HelperFunctions.handle_error(e)

try:
    for i in range(1, 6):  # Simulating streaming data
        streaming_data = {"input": f"stream_data_{i}"}
        response = model_handler.infer_model("v3", streaming_data)
        print(f"Streaming Response {i}: {response}")
except Exception as e:
    HelperFunctions.handle_error(e)

try:
    invalid_data = {"input": "invalid_data_point"}
    response = model_handler.infer_model("v3", invalid_data)
    print("Invalid Data Inference Response:", response)
except Exception as e:
    print("Error during request:", e)
    HelperFunctions.handle_error(e)
