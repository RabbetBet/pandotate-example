![Try Pandotate in 5 minutes](https://img.shields.io/badge/Try%20Pandotate-5%20mins-blue.svg)

# Pandotate Flask Example App

A minimal Flask proxy that routes AI inference requests through Pandotate(www.pandotate.com), handling model-based routing, cost optimization, retries, timeouts, and response normalization.

## Features

- **Model-to-Provider Routing**: Routes requests based on the `model` field (Mistral, LLaMA, Qwen) to the appropriate backends (Together.ai, Baseten, RunPod).
- **Input Validation**: Ensures a valid JSON payload and required fields (`model`).
- **Retry & Timeout**: Configurable retry logic (1 retry, 200ms delay) and timeout via `PANDOTATE_TIMEOUT` (default 30s).
- **Performance Logging**: Logs request duration and flags slow calls above `SLOW_THRESHOLD_MS` (default 1500ms).
- **Error Handling**: Returns clear HTTP 400 (bad request), 502 (upstream failure), and 504 (timeout) with JSON error bodies.
- **Response Normalization**: Enforces a consistent schema with `model`, `output`, `usage`, and optional `warning` and `slow` flags.

## Setup

1. **Clone the repo**

   ```bash
   git clone https://github.com/yourusername/pandotate-example.git
   cd pandotate-example
   ```

2. **Create a virtual environment** (recommended)

   ```bash
   python3 -m venv venv
   source venv/bin/activate       # macOS/Linux
   # .\venv\Scripts\Activate.ps1  # Windows PowerShell
   ```

3. **Configure environment variables**
   Create a `.env` file in the project root with:

   ```ini
   PANDOTATE_URL=https://api.pandotate.com/api/inference
   PANDOTATE_API_KEY=YOUR_API_KEY_HERE
   PANDOTATE_TIMEOUT=30            # optional, seconds
   SLOW_THRESHOLD_MS=1500         # optional, milliseconds
   ```

4. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

## Running the App

```bash
python app.py
```

The proxy will start on `http://localhost:8000`.

## Testing with cURL

First, export your API key:

```bash
export PANDOTATE_API_KEY=pk_...
```

Then, run:

```bash
curl -X POST "http://localhost:8000/inference" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $PANDOTATE_API_KEY" \
  -d '{
      "model": "mistral-7b",
      "prompt": "Hello, Pandotate!",
      "max_tokens": 50
    }'
```

Expected response:

```json
{
  "model": "mistral-7b",
  "output": "...",
  "usage": {
    "prompt_tokens": 1,
    "completion_tokens": 0,
    "total_tokens": 1
  },
  "slow": false
}
```

## Troubleshooting

- **401 Unauthorized**: Check your `PANDOTATE_API_KEY` for correctness and expiration.
- **504 Gateway Timeout**: Increase `PANDOTATE_TIMEOUT` or test a smaller model (e.g., `mistral-3b`).
- **Invalid JSON body**: Ensure your `Content-Type` header is `application/json` and payload is valid.

## Next Steps

- Point your application to this proxy: update your LLM client base URL to `http://localhost:8000/inference`.
- Customize `MODEL_PROVIDER_MAP` in `config.py` to support additional models or providers.
- Consider deploying to a robust host (Render, AWS, GCP) and adding authentication for production.
