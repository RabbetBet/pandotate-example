from flask import Flask, request, jsonify
import os
import requests
import time

app = Flask(__name__)

# Load config from environment
PANDOTATE_URL = os.getenv(
    "PANDOTATE_URL",
    "https://api.pandotate.com/api/inference"
).strip()
PANDOTATE_KEY = os.getenv("PANDOTATE_API_KEY")
PANDOTATE_TIMEOUT = int(os.getenv("PANDOTATE_TIMEOUT", "30"))  # seconds
SLOW_THRESHOLD_MS = int(os.getenv("SLOW_THRESHOLD_MS", "1500"))  # milliseconds

# Debug info
print("Using API key:", (PANDOTATE_KEY or "")[:4] + "…")
print("Forwarding to upstream:", PANDOTATE_URL)
print("Request timeout set to:", PANDOTATE_TIMEOUT, "seconds")
print("Slow threshold set to:", SLOW_THRESHOLD_MS, "ms")

@app.route('/inference', methods=['POST'])
def inference():
    # 1. Parse and validate JSON body
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "Invalid JSON body"}), 400

    # 2. Ensure model field is present
    if "model" not in payload:
        return jsonify({"error": "model field is required"}), 400

    headers = {
        'Authorization': f'Bearer {PANDOTATE_KEY}',
        'Content-Type': 'application/json'
    }

    # 3. Forward with retry + timing
    MAX_RETRIES = 1
    RETRY_DELAY = 0.2  # seconds

    for attempt in range(MAX_RETRIES + 1):
        try:
            start = time.time()
            resp = requests.post(
                PANDOTATE_URL,
                json=payload,
                headers=headers,
                timeout=PANDOTATE_TIMEOUT
            )
            resp.raise_for_status()
            duration_ms = (time.time() - start) * 1000
            app.logger.info(f"Provider call took {duration_ms:.2f} ms")

            data = resp.json()

            # 4. Flag slow responses
            is_slow = duration_ms > SLOW_THRESHOLD_MS
            # Extract and normalize usage
            usage = {
                "prompt_tokens": data.get("tokens", 0),
                "completion_tokens": data.get("completion_tokens", 0),
                "total_tokens": data.get("tokens", 0)
            }
            # Build cleaned response
            cleaned = {
                "model": data.get("model"),
                "output": data.get("output"),
                "usage": usage
            }
            # Collect any extra keys beyond expected + tokens
            extras = set(data.keys()) - {"model", "output", "usage", "tokens", "completion_tokens"}
            if extras:
                cleaned["warning"] = f"Ignored extra keys: {list(extras)}"
            if is_slow:
                cleaned["slow"] = True

            return jsonify(cleaned), resp.status_code

        except requests.Timeout as e:
            app.logger.error("Upstream request timed out", exc_info=True)
            return jsonify({
                "error": "Upstream request timed out",
                "provider": PANDOTATE_URL
            }), 504

        except requests.RequestException as e:
            app.logger.error(f"Attempt {attempt+1} failed: {e}", exc_info=True)
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
            else:
                return jsonify({
                    "error": "Upstream provider failed",
                    "provider": PANDOTATE_URL,
                    "details": str(e)
                }), 502

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)