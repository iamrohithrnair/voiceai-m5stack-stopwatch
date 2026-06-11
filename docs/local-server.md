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

See [server/README.md](../server/README.md) for install steps and model configuration.

## Troubleshooting

- **Device shows OTA errors but still works**: expected if the server was offline at boot; local WebSocket config is applied from firmware settings.
- **No speech response**: check `OPENAI_API_KEY` (or Ollama is running), and that `ffmpeg` is installed.
- **Wrong IP in OTA URL**: set `server.public_host` in `server/config.yaml` and `LOCAL_SERVER_HOST` in menuconfig to your machine's LAN IP.
