# Poke-LLM Makefile

# Configuration
MODEL_ID = TinyLlama/TinyLlama-1.1B-Chat-v1.0
PORT ?= 8000
DEBUG ?= false
# Alternative models you can try:
# MODEL_ID = microsoft/DialoGPT-medium
# MODEL_ID = gpt2
# MODEL_ID = EleutherAI/gpt-neo-125M

.PHONY: init serve clean help change-model logs

# Default target
help:
	@echo "Poke-LLM Commands:"
	@echo "  make init   - Install dependencies, download cloudflared, and prepare model"
	@echo "  make serve  - Start FastAPI app and Cloudflare tunnel"
	@echo "  make clean  - Clean up generated files"
	@echo "  make change-model - Change the model configuration"
	@echo "  make logs   - Show tunnel logs for debugging"
	@echo "  make help   - Show this help"
	@echo ""
	@echo "Options:"
	@echo "  make serve PORT=6050 - Use custom port (default: 8000)"
	@echo "  make serve DEBUG=true - Enable debug logging"
	@echo "  make init DEBUG=true - Enable debug logging for initialization"
	@echo ""
	@echo "Current model: $(MODEL_ID)"
	@echo "Current port: $(PORT)"

# Initialize everything
init:
	@echo "🚀 Initializing Poke-LLM..."
	@if [ ! -d ".venv" ]; then python3 -m venv .venv; chmod +x .venv/bin/activate; fi
	@if [ "$(DEBUG)" = "true" ]; then \
		.venv/bin/python -m pip install -r requirements.txt; \
	else \
		.venv/bin/python -m pip install -r requirements.txt > /dev/null; \
	fi
	@if [ ! -f ".api-key" ]; then \
		echo "🔑 Enter API key:"; read -p "API Key: " api_key; echo "$$api_key" > .api-key; \
	fi
	@if [ ! -f "cloudflared" ]; then \
		OS=$$(uname -s | tr '[:upper:]' '[:lower:]'); \
		ARCH=$$(uname -m); \
		if [ "$$OS" = "darwin" ]; then \
			URL=$$([ "$$ARCH" = "arm64" ] && echo "cloudflared-darwin-arm64.tgz" || echo "cloudflared-darwin-amd64.tgz"); \
		elif [ "$$OS" = "linux" ]; then \
			URL=$$([ "$$ARCH" = "aarch64" ] && echo "cloudflared-linux-arm64" || echo "cloudflared-linux-amd64"); \
		else \
			echo "❌ Unsupported OS: $$OS"; exit 1; \
		fi; \
		curl -L "https://github.com/cloudflare/cloudflared/releases/latest/download/$$URL" -o $$([ "$$OS" = "darwin" ] && echo "cloudflared.tgz" || echo "cloudflared"); \
		if [ "$$OS" = "darwin" ]; then tar -xzf cloudflared.tgz; rm cloudflared.tgz; fi; \
		chmod +x cloudflared; \
	fi
	@echo "Preparing model $(MODEL_ID)..."
	@if [ "$(DEBUG)" = "true" ]; then \
		.venv/bin/python -c "from transformers import AutoTokenizer, AutoModelForCausalLM; import torch; tokenizer = AutoTokenizer.from_pretrained('$(MODEL_ID)'); model = AutoModelForCausalLM.from_pretrained('$(MODEL_ID)', dtype=torch.float16, device_map='auto')"; \
	else \
		.venv/bin/python -c "from transformers import AutoTokenizer, AutoModelForCausalLM; import torch; tokenizer = AutoTokenizer.from_pretrained('$(MODEL_ID)'); model = AutoModelForCausalLM.from_pretrained('$(MODEL_ID)', dtype=torch.float16, device_map='auto')" 2>&1 | grep -v "UserWarning\|CUDA initialization"; \
	fi
	@echo "✅ Ready! Run 'make serve' to start"

# Serve the API
serve:
	@[ ! -f ".api-key" ] && echo "❌ Run 'make init' first" && exit 1 || true
	@[ ! -d ".venv" ] && echo "❌ Run 'make init' first" && exit 1 || true
	@[ ! -f "cloudflared" ] && echo "❌ Run 'make init' first" && exit 1 || true
	@echo "🚀 Starting on port $(PORT)..."
	@if [ "$(DEBUG)" = "true" ]; then \
		.venv/bin/python -m uvicorn app:app --host 127.0.0.1 --port $(PORT) --log-level debug & \
	else \
		.venv/bin/python -m uvicorn app:app --host 127.0.0.1 --port $(PORT) & \
	fi
	@FASTAPI_PID=$$!; sleep 5; \
	./cloudflared tunnel --url http://127.0.0.1:$(PORT) > tunnel.log 2>&1 & \
	TUNNEL_PID=$$!; sleep 10; \
	TUNNEL_URL=$$(grep -o 'https://[^[:space:]]*\.trycloudflare\.com' tunnel.log 2>/dev/null | head -1); \
	echo ""; \
	echo "🎉 Poke-LLM API is running!"; \
	echo "═══════════════════════════════"; \
	echo "📱 Local:  http://127.0.0.1:$(PORT)"; \
	if [ ! -z "$$TUNNEL_URL" ]; then \
		echo "🌐 Public: $$TUNNEL_URL"; \
	else \
		echo "🌐 Public: ❌ Tunnel failed - check tunnel.log"; \
		echo "🐛 Debug:  make serve DEBUG=true"; \
	fi; \
	echo "🧪 Test:   python test.py --url <public-link> --key <your-api-key>"; \
	echo "🛑 Stop:   kill $$FASTAPI_PID $$TUNNEL_PID"; \
	echo "═══════════════════════════════"; \
	echo ""; \
	wait

# Change model configuration
change-model:
	@echo "🤖 Current: $(MODEL_ID)"
	@echo "1) TinyLlama (default) 2) gpt2 3) distilgpt2 4) DialoGPT 5) gpt-neo 6) Custom"
	@read -p "Choose (1-6): " choice; \
	case $$choice in \
		1) new_model="TinyLlama/TinyLlama-1.1B-Chat-v1.0" ;; \
		2) new_model="gpt2" ;; \
		3) new_model="distilgpt2" ;; \
		4) new_model="microsoft/DialoGPT-medium" ;; \
		5) new_model="EleutherAI/gpt-neo-125M" ;; \
		6) read -p "Model ID: " new_model ;; \
		*) echo "Invalid"; exit 1 ;; \
	esac; \
	sed -i.bak "s/MODEL_ID = .*/MODEL_ID = $$new_model/" config.py Makefile; \
	rm -f config.py.bak Makefile.bak; \
	echo "✅ Changed to: $$new_model"; \
	echo "Run 'make init' to download"

# Show tunnel logs
logs:
	@if [ -f "tunnel.log" ]; then \
		echo "🔍 Tunnel logs:"; \
		echo "═══════════════════════════════"; \
		tail -20 tunnel.log; \
		echo "═══════════════════════════════"; \
	else \
		echo "❌ No tunnel.log found"; \
	fi

# Clean up generated files
clean:
	@rm -f cloudflared.tgz tunnel.log fastapi.log cloudflared
	@rm -rf .venv
	@echo "✅ Cleaned"
