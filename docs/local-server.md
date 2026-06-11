# Local Server Setup

This project uses **[xiaozhi-esp32-server](https://github.com/xinnan-tech/xiaozhi-esp32-server)** — the same backend as xiaozhi.me, with the full **智控台** web UI for agent configuration, memory, voice clone, knowledge base, and MCP.

## Architecture

```
ESP32 firmware  ──Wi-Fi──►  xiaozhi-esp32-server (Docker)
                              ├── :8003  OTA config
                              ├── :8000  WebSocket voice
                              └── :8002  智控台 web UI (full stack)
```

## 1. Start the backend

```bash
cd server
./setup.sh          # clone upstream, create config, download ASR model
./start.sh --full   # Docker: voice + web console + database
```

Open **http://\<your-lan-ip\>:8002** — this is the xiaozhi.me-equivalent console.

## 2. Flash firmware

In `idf.py menuconfig` → **Xiaozhi Assistant**:

| Setting | Value |
|---------|-------|
| Use self-hosted local server | Enabled |
| Local server hostname or IP | Your PC's LAN IP |
| WebSocket port | `8000` |
| OTA HTTP port | `8003` |

Build and flash. No xiaozhi.me activation code required.

## 3. Configure your agent (智控台)

In the web UI at `:8002`, configure the same fields as xiaozhi.me:

- **Configure Role** — template, assistant name (e.g. Angel), role introduction
- **Dialogue language** & **voice role**
- **Memory type** — session, rolling summary (`mem_local_short`), mem0, etc.
- **LLM / ASR / TTS** modules
- **MCP**, knowledge base, voice clone

Edit `server/xiaozhi-esp32-server/main/xiaozhi-server/data/.config.yaml` for low-level module config, or use the web UI after full-stack deploy.

## Ports

| Port | Service |
|------|---------|
| 8002 | 智控台 (configuration UI) |
| 8003 | OTA (`/xiaozhi/ota/`) |
| 8000 | WebSocket (`/xiaozhi/v1/`) |

## Troubleshooting

- **OTA fails**: confirm `http://<ip>:8003/xiaozhi/ota/` in a browser
- **No voice**: check `docker logs -f xiaozhi-esp32-server`
- **ASR errors**: ensure `models/SenseVoiceSmall/model.pt` exists (re-run `./setup.sh`)
- **LLM errors**: set API keys in `.config.yaml` or switch to Ollama

See [server/README.md](../server/README.md) and upstream [docs](https://github.com/xinnan-tech/xiaozhi-esp32-server/tree/main/docs).
