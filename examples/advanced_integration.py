from freeseek import FreeseekAPI, ModelHandler, HelperFunctions

HelperFunctions.setup_logging()

api = FreeseekAPI(api_key="your_api_key_here")
model_handler = ModelHandler(api)

def handle_batch_inference(model_handler, batch_data):
    try:
        batch_responses = []
        for data in batch_data:
            response = model_handler.infer_model("v3", data)
            batch_responses.append(response)
        print("Batch Inference Responses:", batch_responses)
    except Exception as e:
        HelperFunctions.handle_error(e)

def handle_streaming_inference(model_handler, num_streams):
    try:
        for i in range(1, num_streams + 1):
            streaming_data = {"input": f"stream_data_{i}"}
            response = model_handler.infer_model("v3", streaming_data)
            print(f"Streaming Response {i}: {response}")
    except Exception as e:
        HelperFunctions.handle_error(e)

def handle_invalid_data_inference(model_handler, invalid_data):
    try:
        response = model_handler.infer_model("v3", invalid_data)
        print("Invalid Data Inference Response:", response)
    except Exception as e:
        print("Error during request:", e)
        HelperFunctions.handle_error(e)

batch_data = [
    {"input": "data_point_1"},
    {"input": "data_point_2"},
    {"input": "data_point_3"}
]

handle_batch_inference(model_handler, batch_data)
handle_streaming_inference(model_handler, 5)
handle_invalid_data_inference(model_handler, {"input": "invalid_data_point"})
