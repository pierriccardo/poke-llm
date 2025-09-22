#!/bin/bash

# Simple Poke-LLM Launcher
echo "🚀 Starting Poke-LLM..."

# Setup
echo "Setting up environment..."
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

source .venv/bin/activate
pip install -r requirements.txt > /dev/null

# Download cloudflared if needed
if [ ! -f "cloudflared" ]; then
    ARCH=$(uname -m)
    if [[ "$ARCH" == "arm64" ]]; then
        curl -L "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-darwin-arm64.tgz" -o cloudflared.tgz
    else
        curl -L "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-darwin-amd64.tgz" -o cloudflared.tgz
    fi
    tar -xzf cloudflared.tgz
    chmod +x cloudflared
    rm cloudflared.tgz
fi

# Start FastAPI in background
echo "Starting FastAPI..."
source .venv/bin/activate
python -m uvicorn app:app --host 127.0.0.1 --port 8000 &
FASTAPI_PID=$!

# Wait 5 seconds
sleep 5

# Start tunnel
echo "Starting tunnel..."
./cloudflared tunnel --url http://127.0.0.1:8000 > tunnel.log 2>&1 &
TUNNEL_PID=$!

# Wait for tunnel to start and extract URL
echo "Waiting for tunnel URL..."
sleep 8

# Extract tunnel URL from logs
TUNNEL_URL=$(grep -o 'https://[^[:space:]]*\.trycloudflare\.com' tunnel.log 2>/dev/null | head -1)

echo ""
echo "🎉 Poke-LLM is running!"
echo "======================="
echo "📱 Local API: http://127.0.0.1:8000"
if [ ! -z "$TUNNEL_URL" ]; then
    echo "🌐 Public URL: $TUNNEL_URL"
else
    echo "🌐 Public URL: Check tunnel.log for URL"
fi
echo ""
echo "🧪 Test: python test.py"
echo "🛑 Stop: kill $FASTAPI_PID $TUNNEL_PID"
echo ""

# Keep running
wait
