import os
import json
import requests
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv

# === Load env ===
load_dotenv()
ENDPOINT = os.getenv("ENDPOINT")
API_VERSION = os.getenv("API_VERSION", "2024-02-01")
MODEL_DEPLOYMENT = os.getenv("MODEL_DEPLOYMENT", "dall-e-3")
API_KEY = os.getenv("OPENAI_API_KEY")

# === Flask ===
app = Flask(__name__)

# === Footer Version ===
FOOTER = "Development version 1.011 🍍"

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/generate", methods=["POST"])
def generate_image():
    try:
        data = request.get_json(silent=True) or {}
        prompt = (data.get("prompt") or "").strip()
        if not prompt:
            return jsonify({"error": "Prompt is required", "footer": FOOTER}), 400

        # REST-style payload per Azure OpenAI DALL·E 3
        payload = {
            "model": MODEL_DEPLOYMENT,
            "prompt": prompt,
            "size": "1024x1024",
            "style": "vivid",
            "quality": "standard",
            "n": 1
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}"
        }

        # Pass api-version via params
        resp = requests.post(
            ENDPOINT,
            headers=headers,
            params={"api-version": API_VERSION},
            data=json.dumps(payload)
        )

        if resp.status_code != 200:
            return jsonify({
                "error": "Request failed",
                "status_code": resp.status_code,
                "raw": safe_json(resp),
                "footer": FOOTER
            }), 500

        body = resp.json()
        image_url = None
        if isinstance(body, dict) and "data" in body and isinstance(body["data"], list) and body["data"]:
            image_url = body["data"][0].get("url")

        if not image_url:
            print("DEBUG: Raw Azure OpenAI DALL·E response:", body)
            return jsonify({
                "error": "No image URL returned",
                "raw_response": body,
                "footer": FOOTER
            }), 500

        return jsonify({"image_url": image_url, "footer": FOOTER})

    except Exception as ex:
        return jsonify({"error": str(ex), "footer": FOOTER}), 500

def safe_json(resp):
    try:
        return resp.json()
    except Exception:
        return {"text": resp.text}

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "endpoint": f"{ENDPOINT}?api-version={API_VERSION}",
        "api_version": API_VERSION,
        "deployment": f"Deployment active: {MODEL_DEPLOYMENT}",
        "auth": "Key",
        "footer": FOOTER
    })

@app.route("/debug", methods=["GET"])
def debug():
    """Debug route to show full request details and last response."""
    test_prompt = "Debug test prompt"
    payload = {
        "model": MODEL_DEPLOYMENT,
        "prompt": test_prompt,
        "size": "256x256",
        "n": 1
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    try:
        resp = requests.post(
            ENDPOINT,
            headers=headers,
            params={"api-version": API_VERSION},
            data=json.dumps(payload)
        )
        return jsonify({
            "request_url": f"{ENDPOINT}?api-version={API_VERSION}",
            "headers": headers,
            "payload": payload,
            "status_code": resp.status_code,
            "response": safe_json(resp),
            "footer": FOOTER
        })
    except Exception as ex:
        return jsonify({
            "error": str(ex),
            "footer": FOOTER
        })

if __name__ == "__main__":
    app.run(debug=True)