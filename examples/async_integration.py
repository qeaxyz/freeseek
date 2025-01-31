import asyncio
from freeseek import AsyncFreeseekAPI, ModelHandler

async def main():
    api = AsyncFreeseekAPI(api_key="your_api_key")
    model_handler = ModelHandler(api)
    
    # Concurrent batch processing
    tasks = [
        model_handler.infer_model("v3", {"input": f"data_{i}"})
        for i in range(10)
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            print(f"Task {i} failed: {str(result)}")
        else:
            print(f"Task {i} result: {result}")

if __name__ == "__main__":
    asyncio.run(main())