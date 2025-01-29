# Freeseek SDK API Reference 📚⚙️

## Overview 🌟

The **Freeseek SDK** provides seamless integration with Freeseek's powerful AI models for inference, model management, and real-time data processing. By leveraging these core classes and methods, developers can interact with Freeseek's sophisticated AI capabilities in a simple and efficient manner.

## Core Classes 🚀

### `FreeseekClient` – The Gateway to AI Interaction 🌐

The **FreeseekClient** is the central class to interact with Freeseek's API. It allows users to request model inferences, manage settings, and handle authentication. This class is designed to be both intuitive and flexible, allowing for smooth integration into your applications.

#### Key Methods:

| Method                             | Description                                                                                         |
| ---------------------------------- | --------------------------------------------------------------------------------------------------- |
| `infer(model, prompt, **kwargs)` | Obtain a single inference response from the model. 📩                                               |
| `infer_batch(model, prompts)`    | Process and receive responses for multiple prompts at once. Efficient batch processing. 📦          |
| `stream_infer(model, prompt)`    | Stream real-time responses for dynamic use cases (e.g., chatbot, real-time analysis). 🌊            |
| `get_model_info(model)`          | Retrieve detailed specifications, capabilities, and limitations of the model. ℹ️                  |
| `refresh_token()`                | Renew your authentication token for continued API access. 🔄                                        |
| `update_config(new_settings)`    | Modify runtime configuration and fine-tune settings (e.g., change temperature, model options). ⚙️ |

#### Parameters for `infer()`:

```python
# infer() Parameters
model (BaseModel): A model instance (required, e.g., DeepseekV3, DeepseekR1)
prompt (str): Input text for inference (required)
temperature (float): Adjusts response creativity, between 0.1-1.0 🌡️
max_tokens (int): Limits the number of tokens (words/characters) in the response 🔢
stream (bool): Whether to enable real-time streaming of the response (default: False) 🌊
top_p (float): Controls nucleus sampling for diverse response generation (optional) 🎯
frequency_penalty (float): Adjusts likelihood of repeating phrases (optional) 🔄
presence_penalty (float): Encourages introduction of new topics (optional) 💬
```

### `DeepseekV3` / `DeepseekR1` Models 🧠

Freeseek offers advanced models like `DeepseekV3` and `DeepseekR1` that power inference tasks. These models come with fine-tuned settings, allowing for both general and creative text generation. Choose the one that fits your needs based on functionality and preferences.

```python
from freeseek import DeepseekV3, DeepseekR1

# Example Model Setup with DeepseekV3
model = DeepseekV3(
    creative_mode=True,  # 🎨 Enable creative generation for more diverse responses
    safe_filter=False    # ⚠️ Disable content filtering for unrestricted output
)
```

---

## Response Objects 📦

When you call any inference method, you will receive a **response object** that contains key information about the generated output.

```python
{
    "text": str,          # The generated content (output from the model) 📝
    "latency": float,     # Time taken for inference in milliseconds (efficiency indicator) ⏱️
    "tokens_used": int,   # Total tokens used during the inference (useful for pricing & quota) 🔢
    "model_version": str  # Identifier of the model version used for inference (ensures versioning) 🏷️
}
```

#### Example Response:

```json
{
    "text": "Here is the generated text based on your input prompt...",
    "latency": 125.4,
    "tokens_used": 100,
    "model_version": "v3.2.0"
}
```

---

## Error Handling ⚠️

Freeseek’s API uses HTTP status codes to inform you of the request outcome. Here's a breakdown of the common errors you might encounter, along with solutions for each:

| Code | Meaning                                   | Solution                                                                                                |
| ---- | ----------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| 401  | Unauthorized: Invalid API Key 🔑          | Verify your API credentials or refresh your authentication token. Ensure correct access permissions.    |
| 429  | Too Many Requests: Rate Limit Exceeded 🚧 | Implement a backoff strategy (e.g., exponential backoff) or wait before retrying the request.           |
| 503  | Service Unavailable 🛠️                  | The service is temporarily unavailable. Retry after a short delay (usually 30 seconds).                 |
| 400  | Bad Request: Invalid Input Parameters 🚫  | Check if the input prompt or parameters follow the correct format. Ensure model settings are valid.     |
| 500  | Internal Server Error 🔧                  | A server error occurred. Try the request again after a brief wait, or contact support for further help. |

---

## Authentication & Tokens 🔑

To access Freeseek's API, you need to authenticate using an **API key**. Make sure that you store your API key securely, as it grants access to model inferences and other services.

### Token Refresh

Tokens can expire or need to be refreshed. You can use the `refresh_token()` method to automatically renew your authentication token.

```python
client.refresh_token()  # Refresh token for continued access
```

---

## Rate Limits & Quotas 📉

Freeseek enforces rate limits to maintain service stability and fairness across users. Be mindful of the following when planning your API usage:

- **Standard Plan**: 1000 requests per hour
- **Premium Plan**: 5000 requests per hour
- **Requests are counted per model** (e.g., `DeepseekV3` or `DeepseekR1`)

### Handling Rate Limits:

If you exceed the limit, you will receive a `429` status code. Implement rate limiting with retries to avoid this issue.

---

## Advanced Features ✨

### **Streaming Inference** 🌊

For real-time applications such as chatbots, customer support, or live text generation, you can use the `stream_infer()` method. This streams the model's output in real-time as it is generated.

```python
response_stream = client.stream_infer(model, "What's the weather like?")
for chunk in response_stream:
    print(chunk["text"])  # Display each chunk of generated content as it's streamed
```

### **Batch Inference** 📦

If you need to process multiple prompts simultaneously, the `infer_batch()` method allows you to send multiple inputs and get responses in bulk, minimizing overhead and improving efficiency.

```python
prompts = ["What is AI?", "How do I use Freeseek?"]
responses = client.infer_batch(model, prompts)
for response in responses:
    print(response["text"])  # Process multiple responses at once
```

---

## Configuration & Settings ⚙️

Fine-tune the behavior of the model with various configuration options:

```python
client.update_config({
    "temperature": 0.8,  # Increase creativity for more diverse responses
    "max_tokens": 150,   # Limit response length
    "safe_filter": True, # Enable content filtering for safety
    "top_p": 0.95       # Adjust nucleus sampling for response diversity
})
```

---

## Conclusion 🎯

The **Freeseek SDK** is a powerful toolkit for developers to leverage Freeseek’s cutting-edge AI models for a wide range of use cases. Whether you're building intelligent chatbots, text generation systems, or conducting batch processing, the SDK makes it easy to integrate Freeseek's capabilities into your projects. With options for streaming, batching, and flexible model parameters, you can optimize the performance and results for your specific needs.

Happy coding! 🚀
