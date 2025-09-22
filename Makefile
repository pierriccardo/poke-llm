# Poke-LLM Makefile

# Configuration
MODEL_ID = TinyLlama/TinyLlama-1.1B-Chat-v1.0
# Alternative models you can try:
# MODEL_ID = microsoft/DialoGPT-medium
# MODEL_ID = gpt2
# MODEL_ID = EleutherAI/gpt-neo-125M

.PHONY: init serve clean help change-model

# Default target
help:
	@echo "Poke-LLM Commands:"
	@echo "  make init   - Install dependencies, download cloudflared, and prepare model"
	@echo "  make serve  - Start FastAPI app and Cloudflare tunnel"
	@echo "  make clean  - Clean up generated files"
	@echo "  make change-model - Change the model configuration"
	@echo "  make help   - Show this help"
	@echo ""
	@echo "Current model: $(MODEL_ID)"

# Initialize everything
init:
	@echo "🚀 Initializing Poke-LLM..."
	@echo "Setting up environment..."
	@if [ ! -d ".venv" ]; then \
		python3 -m venv .venv; \
		chmod +x .venv/bin/activate; \
		echo "✅ Virtual environment created"; \
	else \
		echo "✅ Virtual environment already exists"; \
	fi
	@echo "Installing dependencies..."
	@.venv/bin/python -m pip install -r requirements.txt > /dev/null
	@echo "✅ Dependencies installed"
	@echo "Setting up API key..."
	@if [ ! -f ".api-key" ]; then \
		echo ""; \
		echo "🔑 API Key Setup"; \
		echo "================"; \
		echo "Enter your API key for authentication:"; \
		read -p "API Key: " api_key; \
		echo "$$api_key" > .api-key; \
		echo "✅ API key saved to .api-key"; \
	else \
		echo "✅ API key already exists"; \
	fi
	@echo "Downloading cloudflared..."
	@if [ ! -f "cloudflared" ]; then \
		ARCH=$$(uname -m); \
		if [ "$$ARCH" = "arm64" ]; then \
			URL="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-darwin-arm64.tgz"; \
		else \
			URL="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-darwin-amd64.tgz"; \
		fi; \
		curl -L "$$URL" -o cloudflared.tgz; \
		tar -xzf cloudflared.tgz; \
		chmod +x cloudflared; \
		rm cloudflared.tgz; \
		echo "✅ Cloudflared downloaded"; \
	else \
		echo "✅ Cloudflared already exists"; \
	fi
	@echo "Preparing model $(MODEL_ID) (this may take a while on first run)..."
	@.venv/bin/python -c "from transformers import AutoTokenizer, AutoModelForCausalLM; import torch; tokenizer = AutoTokenizer.from_pretrained('$(MODEL_ID)'); model = AutoModelForCausalLM.from_pretrained('$(MODEL_ID)', dtype=torch.float16, device_map='auto')" > /dev/null 2>&1
	@echo "✅ Model prepared"
	@echo ""
	@echo "🎉 Initialization complete!"
	@echo "Run 'make serve' to start the API"

# Serve the API
serve:
	@echo "🚀 Starting Poke-LLM API..."
	@if [ ! -f ".api-key" ]; then \
		echo "❌ Error: .api-key file not found!"; \
		echo "Create a .api-key file with your API key first."; \
		exit 1; \
	fi
	@if [ ! -d ".venv" ]; then \
		echo "❌ Error: Virtual environment not found!"; \
		echo "Run 'make init' first."; \
		exit 1; \
	fi
	@if [ ! -f "cloudflared" ]; then \
		echo "❌ Error: Cloudflared not found!"; \
		echo "Run 'make init' first."; \
		exit 1; \
	fi
	@echo "Starting FastAPI..."
	@.venv/bin/python -m uvicorn app:app --host 127.0.0.1 --port 8000 &
	@FASTAPI_PID=$$!; \
	echo "FastAPI PID: $$FASTAPI_PID"; \
	sleep 5; \
	echo "Starting tunnel..."; \
	./cloudflared tunnel --url http://127.0.0.1:8000 > tunnel.log 2>&1 & \
	TUNNEL_PID=$$!; \
	echo "Tunnel PID: $$TUNNEL_PID"; \
	sleep 8; \
	TUNNEL_URL=$$(grep -o 'https://[^[:space:]]*\.trycloudflare\.com' tunnel.log 2>/dev/null | head -1); \
	echo ""; \
	echo "🎉 Poke-LLM is running!"; \
	echo "======================="; \
	echo "📱 Local API: http://127.0.0.1:8000"; \
	if [ ! -z "$$TUNNEL_URL" ]; then \
		echo "🌐 Public URL: $$TUNNEL_URL"; \
	else \
		echo "🌐 Public URL: Check tunnel.log for URL"; \
	fi; \
	echo ""; \
	echo "🧪 Test: python test.py"; \
	echo "🛑 Stop: kill $$FASTAPI_PID $$TUNNEL_PID"; \
	echo ""; \
	wait

# Change model configuration
change-model:
	@echo "🤖 Model Configuration"
	@echo "======================"
	@echo "Current model: $(MODEL_ID)"
	@echo ""
	@echo "Available models:"
	@echo "  1) TinyLlama/TinyLlama-1.1B-Chat-v1.0 (default, small & fast)"
	@echo "  2) gpt2 (very small, fast)"
	@echo "  3) distilgpt2 (smaller GPT-2)"
	@echo "  4) microsoft/DialoGPT-medium (conversational)"
	@echo "  5) EleutherAI/gpt-neo-125M (small GPT-Neo)"
	@echo "  6) Custom model"
	@echo ""
	@read -p "Choose option (1-6): " choice; \
	case $$choice in \
		1) new_model="TinyLlama/TinyLlama-1.1B-Chat-v1.0" ;; \
		2) new_model="gpt2" ;; \
		3) new_model="distilgpt2" ;; \
		4) new_model="microsoft/DialoGPT-medium" ;; \
		5) new_model="EleutherAI/gpt-neo-125M" ;; \
		6) read -p "Enter model ID: " new_model ;; \
		*) echo "Invalid option"; exit 1 ;; \
	esac; \
	sed -i.bak "s/MODEL_ID = .*/MODEL_ID = $$new_model/" config.py; \
	sed -i.bak "s/MODEL_ID = .*/MODEL_ID = $$new_model/" Makefile; \
	rm -f config.py.bak Makefile.bak; \
	echo "✅ Model changed to: $$new_model"; \
	echo "Run 'make init' to download the new model"

# Clean up generated files
clean:
	@echo "🧹 Cleaning up..."
	@rm -f cloudflared.tgz tunnel.log fastapi.log
	@rm -rf .venv
	@rm -f cloudflared
	@echo "✅ Cleanup complete"
