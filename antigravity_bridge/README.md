# Antigravity OpenAI Bridge for Zed

This bridge acts as a local proxy server that enables the Zed editor to use the `google-antigravity` Python SDK as its built-in assistant AI.

## Requirements

Ensure you have the required packages installed on your system:

```bash
pip install google-antigravity fastapi uvicorn
```

## Running the Bridge

To launch the proxy server locally on port `8000`:

```bash
python antigravity_openai_bridge.py
```

## Zed Configuration

Add the following to your Zed `settings.json` (accessible via `Ctrl+,` and choosing "Open Settings" in the top-right corner):

```json
{
  "language_models": {
    "openai_compatible": {
      "Antigravity": {
        "api_url": "http://localhost:8000/v1",
        "available_models": [
          {
            "name": "gemini-3.5-flash",
            "display_name": "Antigravity Agent",
            "max_tokens": 128000
          }
        ]
      }
    }
  },
  "assistant": {
    "provider": "openai_compatible",
    "model": "gemini-3.5-flash"
  }
}
```
