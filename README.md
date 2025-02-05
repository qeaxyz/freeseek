# Freeseek SDK 🚀✨

**Seamlessly Integrate Deepseek's AI Models into Your Python Apps!**

---

## Table of Contents

- [Features](#features-star)
- [Installation](#installation-wrench)
- [Quickstart](#quickstart-rocket)
- [Configuration](#configuration-gear)
- [Examples](#examples-page_facing_up)
- [Documentation](#documentation-books)
- [Contributing](#contributing-handshake)
- [License](#license-scroll)
- [Support](#support-speech_balloon)

---

## Features ⭐

- **Seamless Authentication**: Secure token-based authentication with automatic token refresh.
- **World-Class GPU Infrastructure**: Leverage blazing-fast GPUs for real-time inference.
- **Multi-Environment Support**: Easily configure the SDK for development, staging, or production environments.
- **Advanced Features**:
  - **Real-time Streaming**: Process streaming responses incrementally for large outputs.
  - **Batch Query Processing**: Perform concurrent batch inferences for multiple requests.
  - **Circuit Breaker**: Prevent cascading failures during API outages or high latency.
  - **Retry Mechanism**: Automatic retries with exponential backoff for transient errors.
  - **Rate Limiting**: Dynamically adapt to API rate limits using headers like `X-RateLimit-Remaining`.
  - **Middleware Support**: Pre-request and post-response middleware for custom processing.
  - **Metrics Tracking**: Monitor request success/failure rates for better observability.
  - **Asynchronous Support**: Use both synchronous and asynchronous clients for flexibility.
  - **Model Validation**: Validate input data against model schemas before sending requests.
  - **Dynamic Model Endpoints**: Automatically resolve model-specific endpoints from configuration.
- **Built-in Utilities**: Logging, error handling, JSON parsing, and encryption utilities.

---

## Installation 🔧

```bash
# Install from PyPI
pip install freeseek

# Or clone and install locally
git clone https://github.com/yourusername/freeseek-sdk.git
cd freeseek-sdk
pip install -r requirements.txt
```

---

## Quickstart 🚀

### Synchronous Client

```python
from freeseek import FreeseekAPI

# Initialize the client
client = FreeseekAPI(api_key="your_api_key_here")

# Perform inference
response = client.infer(
    model="deepseek_v3",
    data={"prompt": "Explain quantum computing in 3 sentences:", "temperature": 0.7}
)
print(f"AI Response: {response}")
```

### Asynchronous Client

```python
import asyncio
from freeseek import AsyncFreeseekAPI

async def main():
    # Initialize the async client
    client = AsyncFreeseekAPI(api_key="your_api_key_here")

    # Perform inference
    response = await client.infer(
        model="deepseek_v3",
        data={"prompt": "Explain quantum computing in 3 sentences:", "temperature": 0.7}
    )
    print(f"AI Response: {response}")

# Run the async function
asyncio.run(main())
```

---

## Configuration ⚙️

Customize the SDK using `default_config.json` or runtime parameters:

```python
from freeseek import FreeseekAPI

# Configure the client
client = FreeseekAPI(
    api_key="your_api_key_here",
    base_url="https://api.freeseek.com/v1",
    timeout=30,
    max_retries=5,
    circuit_failure_threshold=3,
    circuit_recovery_timeout=30
)
```

Alternatively, use environment variables for configuration:

```bash
export FREESEEK_API_KEY="your_api_key_here"
export FREESEEK_BASE_URL="https://api.freeseek.com/v1"
export FREESEEK_TIMEOUT=30
```

---

## Examples 📄

Check out our full examples in the `/examples` directory:

- `basic_integration.py`: Simple API interactions.
- `advanced_integration.py`: Streaming, batch processing, and error handling.
- `async_integration.py`: Asynchronous API usage with concurrency.
- `middleware_example.py`: Custom pre-request and post-response middleware.

---

## Documentation 📚

| Resource                            | Description                       |
| ----------------------------------- | --------------------------------- |
| [API Reference](docs/api_reference.md) | Complete method & parameter guide |
| [Usage Guide](docs/usage_guide.md)     | Setup tutorials & best practices  |
| [Model Cards](docs/models.md)          | Deepseek V3/R1 specifications     |
| [Middleware Guide](docs/middleware.md) | Middleware implementation details |

---

## License 📜

Distributed under the MIT License. See `LICENSE` for more information.

---

## Support 💬

Need help? Join our community on [Discord](https://discord.gg/example) or open an issue on GitHub.

---

**Happy Coding!** 🎉👩💻👨💻
