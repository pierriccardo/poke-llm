# API to Poke LLM

## Quick setup
Create a file `.api-key` and write there your private API key, then just run
```bash
$ sh init.sh
```
the script will install dependencies, cloudflare binary, and automatically run `app.py` in a local server and trigger cloudflare tunneling on a random url. You should see something similar to the following:

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

### JavaScript
```javascript
// Read API key from .api-key file (Node.js)
const fs = require('fs');
const apiKey = fs.readFileSync('.api-key', 'utf8').trim();

fetch('https://your-tunnel-url.trycloudflare.com/generate', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': apiKey
  },
  body: JSON.stringify({
    prompt: 'Hello, how are you?',
    max_new_tokens: 50
  })
})
.then(response => response.json())
.then(data => console.log(data));
```

**Replace `your-tunnel-url` with the actual URL shown when you run the script!**