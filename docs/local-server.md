# Local Server Setup

This fork runs entirely on your own network. The ESP32 firmware talks to `server/app.py` on your computer instead of the xiaozhi.me cloud.

## Architecture

```
ESP32  ──Wi-Fi──►  your PC (server/app.py)
                      ├── OTA  /xiaozhi/ota/     → websocket URL, no activation
                      └── WS   /xiaozhi/v1/      → ASR → LLM → TTS
```

## Firmware configuration

In `idf.py menuconfig` → **Xiaozhi Assistant**:

| Option | Description |
|--------|-------------|
| **Use self-hosted local server** | Enabled by default |
| **Local server hostname or IP** | Your computer's LAN address (e.g. `192.168.1.42`) |
| **Local server port** | Default `8000` |

These values are baked into `sdkconfig.defaults`. Rebuild and flash after changing them.

To use the official cloud again, disable **Use self-hosted local server** and set **Default OTA URL** back to `https://api.tenclass.net/xiaozhi/ota/`.

## Server setup

See [server/README.md](../server/README.md) for install steps.

### Local configuration UI

With the server running, open:

```
http://<your-computer-ip>:8000/console/
```

This replaces the xiaozhi.me web panel. You can edit:

| Setting | What it controls |
|---------|------------------|
| Role template | Presets including Technical Mentor (Angel) |
| Assistant name | How the bot refers to itself |
| Role introduction | System prompt / personality |
| Dialogue language | Response language |
| Voice role | TTS voice |
| Memory type | None, session turns, or rolling summary |
| LLM model / API | Chat model (OpenAI, Ollama, etc.) |
| Speech speed & pitch | TTS tuning |
| MCP / Knowledge base | Saved for device MCP; RAG URL for future use |

**Not in local server yet:** voice clone, per-speaker voice-print memory, cloud MCP marketplace. Use [xiaozhi-esp32-server](https://github.com/xinnan-tech/xiaozhi-esp32-server) for full parity.

Changes apply when the device opens a new voice session.

## Troubleshooting

- **Device shows OTA errors but still works**: expected if the server was offline at boot; local WebSocket config is applied from firmware settings.
- **No speech response**: check `OPENAI_API_KEY` (or Ollama is running), and that `ffmpeg` is installed.
- **Wrong IP in OTA URL**: set `server.public_host` in `server/config.yaml` and `LOCAL_SERVER_HOST` in menuconfig to your machine's LAN IP.
