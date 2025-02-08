def generate_boilerplate(language: str, api_key: str = "YOUR_API_KEY") -> str:
    boilerplates = {
        "python": f'''\
from freeseek.api import FreeseekAPI

api_client = FreeseekAPI(api_key="{api_key}")
result = api_client.infer("example-model", {{"input": "Hello, world!"}})
print(result)
'''
    }

    return boilerplates.get(language.lower(), "Unsupported language")
