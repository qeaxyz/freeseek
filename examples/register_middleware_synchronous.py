from freeseek.api import FreeseekAPI

# Define a pre-request middleware to add a custom header.
def add_custom_header(context):
    context["headers"]["X-Custom-Header"] = "my-custom-value"
    return context

# Define a post-response middleware to log the content length.
def log_content_length(response):
    content_length = response.headers.get("Content-Length", "unknown")
    print(f"Response Content-Length: {content_length}")
    return response

# Initialize the API client.
api_client = FreeseekAPI(api_key="YOUR_API_KEY")

# Register middleware.
api_client.add_pre_request_middleware(add_custom_header)
api_client.add_post_response_middleware(log_content_length)

# Make an inference request.
result = api_client.infer("example-model", {"input": "Hello, world!"})
print(result)
