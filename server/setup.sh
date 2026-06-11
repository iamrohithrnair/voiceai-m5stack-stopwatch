#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
UPSTREAM="$ROOT/xiaozhi-esp32-server"
SERVER_DIR="$UPSTREAM/main/xiaozhi-server"
MODEL_DIR="$SERVER_DIR/models/SenseVoiceSmall"
MODEL_FILE="$MODEL_DIR/model.pt"
CONFIG="$SERVER_DIR/data/.config.yaml"

lan_ip() {
  ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || hostname -I 2>/dev/null | awk '{print $1}' || echo "192.168.1.100"
}

echo "==> XiaoZhi local server setup"
IP="$(lan_ip)"
echo "    Detected LAN IP: $IP"

if [[ ! -d "$UPSTREAM/.git" ]]; then
  echo "==> Cloning xiaozhi-esp32-server..."
  git clone --depth 1 https://github.com/xinnan-tech/xiaozhi-esp32-server.git "$UPSTREAM"
fi

mkdir -p "$SERVER_DIR/data" "$MODEL_DIR"

if [[ ! -f "$CONFIG" ]]; then
  echo "==> Creating data/.config.yaml from example..."
  sed "s/LAN_IP/$IP/g" "$ROOT/data/.config.yaml.example" > "$CONFIG"
else
  echo "==> Keeping existing data/.config.yaml"
fi

if [[ ! -f "$MODEL_FILE" ]]; then
  echo "==> Downloading FunASR SenseVoiceSmall model (~200MB)..."
  curl -L --progress-bar \
    "https://modelscope.cn/models/iic/SenseVoiceSmall/resolve/master/model.pt" \
    -o "$MODEL_FILE" || {
      echo "WARN: Model download failed. Download manually to:"
      echo "  $MODEL_FILE"
      echo "  https://modelscope.cn/models/iic/SenseVoiceSmall/resolve/master/model.pt"
    }
else
  echo "==> ASR model already present"
fi

echo ""
echo "Setup complete."
echo ""
echo "  Web console (full stack):  http://$IP:8002"
echo "  OTA (ESP32):               http://$IP:8003/xiaozhi/ota/"
echo "  WebSocket:                 ws://$IP:8000/xiaozhi/v1/"
echo ""
echo "Next:"
echo "  1. Edit $CONFIG (LLM API / Ollama)"
echo "  2. ./start.sh --full    # server + 智控台 UI"
echo "     ./start.sh           # voice server only"
echo "  3. Set LOCAL_SERVER_HOST=$IP in idf.py menuconfig, flash firmware"
