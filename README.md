# API to Poke LLM

## Quick setup

### 1. Initialize everything
```bash
make init
```
This will:
- Install dependencies
- Prompt you to enter your API key (saved to `.api-key`)
- Download cloudflared
- Prepare the model

### 2. Start the API
```bash
make serve
```
This will start the FastAPI app and Cloudflare tunnel. You should see something similar to the following:

```bash
🚀 Starting Poke-LLM...
Setting up environment...
Starting FastAPI...
Starting tunnel...
Waiting for tunnel URL...
INFO:     Started server process [86577]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)

🎉 Poke-LLM is running!
=======================
📱 Local API: http://127.0.0.1:8000
🌐 Public URL: https://participate-spiritual-supplied-bought.trycloudflare.com

🧪 Test: python test.py
🛑 Stop: kill 86577 86585
```

## Using the API

Once running, you can use the public URL to make requests:

### cURL
```bash
curl -X POST "https://your-tunnel-url.trycloudflare.com/generate" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $(cat .api-key)" \
  -d '{"prompt": "Hello, how are you?", "max_new_tokens": 50}'
```

### Python
```python
import requests

# Load API key from file
with open('.api-key', 'r') as f:
    api_key = f.read().strip()

url = "https://your-tunnel-url.trycloudflare.com/generate"
headers = {"Content-Type": "application/json", "X-API-Key": api_key}
data = {"prompt": "Hello, how are you?", "max_new_tokens": 50}

response = requests.post(url, json=data, headers=headers)
print(response.json())
```

**Replace `your-tunnel-url` with the actual URL shown when you run the script!**

## Available Commands

- `make init` - Install dependencies, download cloudflared, and prepare the model
- `make serve` - Start FastAPI app and Cloudflare tunnel
- `make change-model` - Change the language model (interactive menu)
- `make clean` - Clean up generated files (venv, logs, etc.)
- `make help` - Show all available commands

## Changing the Model

You can easily switch between different language models:

```bash
make change-model
```

This will show you a menu with popular models:
- **TinyLlama** (default) - Small, fast, good for testing
- **GPT-2** - Very small, very fast
- **DistilGPT-2** - Smaller GPT-2 variant
- **DialoGPT** - Optimized for conversations
- **GPT-Neo** - Alternative to GPT-2
- **Custom** - Enter any Hugging Face model ID

After changing the model, run `make init` to download it.

## File Structure

- `.api-key` - Your private API key (create this file)
- `app.py` - FastAPI application
- `test.py` - Test script for the API
- `requirements.txt` - Python dependencies
- `Makefile` - Build and run commands