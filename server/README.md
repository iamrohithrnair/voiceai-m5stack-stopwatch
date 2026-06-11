# Local XiaoZhi Backend

Full [xiaozhi-esp32-server](https://github.com/xinnan-tech/xiaozhi-esp32-server) stack — same capabilities as xiaozhi.me (智控台 UI, memory, voice clone, knowledge base, MCP).

## Quick start

```bash
cd server
./setup.sh              # clone upstream + config + ASR model
# Edit xiaozhi-esp32-server/main/xiaozhi-server/data/.config.yaml

./start.sh --full       # Docker: voice + web console (:8002)
# or
./start.sh              # voice server only
```

**Requires:** Docker, ~4GB RAM for full stack (2GB server-only with API-based ASR/LLM).

## Endpoints

| Service | URL |
|---------|-----|
| **智控台 (web UI)** | `http://<lan-ip>:8002` |
| OTA (ESP32 firmware) | `http://<lan-ip>:8003/xiaozhi/ota/` |
| WebSocket (voice) | `ws://<lan-ip>:8000/xiaozhi/v1/` |

Configure the ESP32 `LOCAL_SERVER_HOST` to your LAN IP. OTA uses port **8003**, WebSocket uses **8000**.

## Web console (xiaozhi.me equivalent)

Open `http://<lan-ip>:8002` after `./start.sh --full`:

- Configure Role / agent name / role introduction
- Dialogue language & voice
- Memory type & current memory
- LLM, ASR, TTS modules
- MCP, knowledge base, voice clone

First login creates the admin account.

## Configuration

Override defaults in `xiaozhi-esp32-server/main/xiaozhi-server/data/.config.yaml`.

See upstream [Deployment.md](https://github.com/xinnan-tech/xiaozhi-esp32-server/blob/main/docs/Deployment.md) and [Deployment_all.md](https://github.com/xinnan-tech/xiaozhi-esp32-server/blob/main/docs/Deployment_all.md).

## Source mode (no Docker)

```bash
cd xiaozhi-esp32-server/main/xiaozhi-server
conda create -n xiaozhi python=3.10 -y && conda activate xiaozhi
conda install libopus ffmpeg -y
pip install -r requirements.txt
python app.py
```
