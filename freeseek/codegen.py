def generate_boilerplate(language: str) -> str:
    if language == 'python':
        return """
from freeseek.api import FreeseekAPI

api_client = FreeseekAPI(api_key="YOUR_API_KEY")
result = api_client.infer("example-model", {"input": "Hello, world!"})
print(result)
"""
    else:
        return "Unsupported language"