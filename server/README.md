# Local XiaoZhi Server

Self-hosted backend for the ESP32 firmware. No [xiaozhi.me](https://xiaozhi.me) account or cloud console required.

## Quick start

1. Install dependencies:

```bash
cd server
uv venv .venv
source .venv/bin/activate
uv pip install -r requirements.txt
brew install ffmpeg   # macOS — required for Opus audio conversion
```

2. Configure models:

```bash
cp config.example.yaml config.yaml
export OPENAI_API_KEY=sk-...   # or point llm/asr at Ollama / another OpenAI-compatible API
```

3. Set your LAN IP in firmware menuconfig (`Local server hostname or IP`) to match this machine.

4. Start the server:

```bash
python app.py
```

5. Open the **local console** in your browser (same settings as xiaozhi.me):

```
http://<your-lan-ip>:8000/console/
```

Configure assistant name, system prompt, LLM model, voice, memory, and API keys from the UI.

6. Flash the ESP32 firmware (local server mode is enabled by default in `sdkconfig.defaults`).

Stop the server with **Ctrl+C**. If port 8000 is already in use, run `lsof -ti:8000 | xargs kill` or `python app.py --port 8001`.

## Model configuration

Edit `config.yaml`:

| Section | Purpose | Examples |
|---------|---------|----------|
| `asr` | Speech-to-text | OpenAI Whisper, local `faster-whisper` |
| `llm` | Chat model | OpenAI, Ollama (`base_url: http://127.0.0.1:11434/v1`) |
| `tts` | Voice output | Microsoft Edge TTS (free), OpenAI TTS |
| `assistant.system_prompt` | Personality / instructions | Keep replies short for voice |

Environment variables in config values use `${VAR_NAME}` syntax.

### Ollama example

```yaml
llm:
  model: llama3.2
  api_key: ollama
  base_url: http://127.0.0.1:11434/v1

asr:
  provider: local_whisper
  model: base
  device: cpu
```

Install local ASR: `pip install faster-whisper`

## Endpoints

| Endpoint | Description |
|----------|-------------|
| `http://<host>:8000/xiaozhi/ota/` | Device OTA + WebSocket config (no activation) |
| `ws://<host>:8000/xiaozhi/v1/` | Voice WebSocket protocol |

Set `server.public_host` in `config.yaml` if auto-detected LAN IP is wrong.
