import asyncio
from freeseek.api import AsyncFreeseekAPI

async def main():
    # Define async middleware functions.
    async def async_add_custom_header(context):
        context["headers"]["X-Async-Custom"] = "async-value"
        return context

    def async_log_content_length(response):
        print(f"Async Response Content-Length: {response.headers.get('Content-Length', 'unknown')}")
        return response

    # Initialize the async API client.
    api_client = AsyncFreeseekAPI(api_key="YOUR_API_KEY")
    api_client.add_pre_request_middleware(async_add_custom_header)
    api_client.add_post_response_middleware(async_log_content_length)

    # Make an asynchronous inference request.
    result = await api_client.infer("example-model", {"input": "Hello, async world!"})
    print(result)
    await api_client.aclose()

asyncio.run(main())
