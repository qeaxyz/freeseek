# 🗺️ Freeseek SDK Usage Guide 👩‍💻

## 🚀 1. Environment Setup 🛠️

### 📦 Requirements

- Python 3.8 or newer 🐍
- A valid Freeseek API key 🔑
- Internet connection 🌐
- Virtual environment (recommended)

```bash
# Step 1: Create a virtual environment to isolate dependencies
python -m venv freeseek-env

# Step 2: Activate the virtual environment
source freeseek-env/bin/activate  # For Unix/MacOS
freeseek-env\Scripts\activate     # For Windows

# Step 3: Install the Freeseek SDK package
pip install freeseek
```

---

## 🐣 2. Basic Implementation Example

### 🌐 Initialize Client and Make Your First Request

Once you’ve installed the SDK and set up your environment, you can start using the `FreeseekClient` to interact with Freeseek’s services.

```python
from freeseek import FreeseekClient, DeepseekR1

# Initialize the Freeseek client
client = FreeseekClient(
    api_key="your_key_here",  # Replace with your API key 🔑
    endpoint="production"     # Use 'staging' for testing purposes 🌍
)

# Send a simple query to the model
response = client.infer(
    model=DeepseekR1(),        # Select the model (DeepseekR1, DeepseekV2, etc.)
    prompt="Write a Python function to reverse a string:",  # Your input prompt
    temperature=0.5            # Controls randomness of the output (0.0 to 1.0)
)

# Print the output solution
print(f"💡 Solution:\n{response.text}")
```

---

## 🚀 3. Advanced Features

### 🔄 Real-time Streaming

Freeseek SDK supports real-time streaming of responses for faster and more interactive results. Ideal for applications requiring immediate feedback, like chatbots or dynamic content generation.

```python
# Example of real-time streaming
for chunk in client.stream_infer(
    model=DeepseekV3(),             # Specify the model for streaming
    prompt="Explain neural networks in rap lyrics:"  # Your prompt
):
    print(chunk.text, end="", flush=True)  # Output the response as it's being generated 🎤
```

### 📈 Batch Processing

For efficiency, you can process multiple queries at once. This method is perfect when you have a large set of prompts to send to the model and want to optimize for time.

```python
# Batch process multiple prompts
responses = client.infer_batch(
    model=DeepseekR1(),
    prompts=[
        "TL;DR summary: {long_text}",
        "Generate 5 marketing slogans: {product_desc}"
    ]
)

# Loop through and print responses
for idx, response in enumerate(responses):
    print(f"Response {idx+1}: {response.text}")
```

---

## 🏆 4. Best Practices

### 🔑 Token Management

Freeseek employs tokens to authenticate and track API usage. Managing tokens efficiently is key to ensuring smooth interaction.

- **Cache authentication tokens**: Tokens expire every 55 minutes, so caching them reduces the need for frequent re-authentication.
- **Proactive token refresh**: Refresh tokens before they expire to avoid interruptions.

```python
# Refresh the API token before expiration
client.refresh_token()
```

### 🔄 Error Handling & Resilience

Ensure your application gracefully handles errors, especially in case of rate limits or transient network issues.

#### Example: Exponential Backoff on 429 (Rate Limit Exceeded)

```python
import time

retry_count = 0
while retry_count < 5:  # Retry 5 times at most
    try:
        response = client.infer(model=DeepseekR1(), prompt="What is AI?")
        break  # Exit loop if request succeeds
    except FreeseekError as e:
        if e.code == 429:  # Handle rate limit
            retry_count += 1
            wait_time = 2 ** retry_count  # Exponential backoff
            print(f"Rate limit exceeded. Retrying in {wait_time} seconds...")
            time.sleep(wait_time)
        else:
            raise  # Re-raise any other errors
```

### ⚡ Performance Optimization

For high-performance applications, it's crucial to follow these tips to minimize delays and maximize throughput:

- **Batch small requests**: Send batches of 5-10 prompts at once. This is more efficient than sending individual requests, especially in high-volume environments.
- **Limit max tokens**: Avoid requesting unnecessary token lengths. Setting a reasonable `max_tokens` value reduces unnecessary computation.
- **Monitor token usage**: Keep track of `response.tokens_used` to stay within budget limits and optimize costs.

```python
# Example of setting max tokens and checking usage
response = client.infer(
    model=DeepseekR1(),
    prompt="Explain the significance of deep learning",
    max_tokens=100  # Limit output length
)
print(f"Tokens used: {response.tokens_used}")
```

---

## 🔧 5. Troubleshooting

| Issue                          | Fix                                                                                                                                  |
| ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------ |
| 🌐**Connection Timeout** | Check firewall settings and ensure the endpoint URL (`api.freseek.com`) is not blocked.                                            |
| ❌**Model Not Found**    | Verify model name casing and ensure you’re using the correct model. (e.g.,`DeepseekR1()` vs. `deepseekr1()`)                    |
| 📄**JSON Parse Error**   | Ensure that the prompt contains valid UTF-8 characters. Non-UTF-8 or invalid characters will cause errors when parsing the response. |
| ⏳**Slow Response**      | Ensure you're not hitting rate limits; check your API usage. Use streaming for faster responses in dynamic scenarios.                |
| 🔑**Invalid API Key**    | Double-check that your API key is correctly entered and not expired. Refresh your key if necessary.                                  |

---

## 🌟 6. Frequently Asked Questions (FAQ)

### 💡 **What models does Freeseek support?**

Freeseek offers a variety of models optimized for different tasks. Some common ones include:

- **DeepseekR1**: A versatile model for a wide range of tasks.
- **DeepseekV2**: Enhanced version for more complex tasks.
- **DeepseekV3**: For cutting-edge NLP features (e.g., real-time generation, summarization).

### 🔄 **How do I switch to a different model?**

Simply pass the desired model class to the `model` parameter in your `client.infer()` or `client.stream_infer()` call, like so:

```python
response = client.infer(model=DeepseekV3(), prompt="Summarize the latest AI research.")
```

This guide provides a comprehensive overview of using the Freeseek SDK, including setup, basic implementations, advanced features, best practices, and troubleshooting tips. By following these guidelines, you’ll be able to build and scale AI-powered applications with ease. Enjoy coding! 🎉
