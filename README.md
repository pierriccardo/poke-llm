# Poke LLM

# Quick start
## Venv, dependencies, API:
```sh
$ make init
$ source .venv/bin/activate
```
## Dataset Quick Setup
```sh
# Download, preprocess and visualize a sample dataset of 10 logs
$ python3 dataset/download.py --format "[Gen 9] OU" --name <ds-name> --num_logs 10
$ python3 dataset/preprocessing.py --dataset <ds-name>
$ python3 dataset/visualize.py --dataset <ds-name> --num_samples 3
```
## Launch finetuning
```sh
$ python3 scripts/finetune.py --dataset <ds-name>
```

## Dataset Preprocessing Explained
Dataset is stored in `dataset/`, which contains two folders for:
- `dataset/raw/`: downloaded data from `download.py` will be saved here
- `dataset/processed`: processed dataset via `preprocessing.py` will be saved here, splitting in train, validation and test
```bash
  dataset
  ├── processed
  │   ├── train/
  │   ├── val/
  │   └── test/
  ├── raw/
```

### 1. Download the dataset
```bash
# will save the dataset inside
python3 dataset/download.py --format "[Gen 9] OU" --num_logs 10
# do not forget "" on format
```
### 2. Preprocess the dataset
The following script preprocess each log in the dataset. Creates N samples (one per turn in the log of that battle) and stores them in `jsonl` file. Each sample is a pair:
```json
  {"input": "Turn 0, Team 1, Charizard, ....", "output": "use Flamethrower"},
  {"input": "Turn 1, Team 1, Charizard, ....", "output": "switch to Blastoise"},
  ...
```

```bash
python3 dataset/preprocessing.py --dataset dataset_gen9ou_100
```

### 3. Visualize
To get a nice visualization of each sample run:
```bash
python3 dataset/visualize.py --dataset dataset_gen9ou_100
```

# API for Exposing Trained Models

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

**Options:**
```bash
make serve PORT=6050        # Use custom port (default: 8000)
make serve DEBUG=true       # Enable debug logging
make init DEBUG=true        # Debug mode for initialization
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

## File Structure

- `.api-key` - Your private API key (create this file)
- `app.py` - FastAPI application
- `test.py` - Test script for the API
- `requirements.txt` - Python dependencies
- `Makefile` - Build and run commands

