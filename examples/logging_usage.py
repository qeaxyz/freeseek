from freeseek import FreeseekAPI

client = FreeseekAPI(api_key="your_api_key_here")

# Perform inference with contextual logging
response = client.infer(
    model="deepseek_v3",
    data={"prompt": "Explain quantum computing in 3 sentences:", "temperature": 0.7}
)
print(f"AI Response: {response}")