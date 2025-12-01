# === Imports ===
import os
import requests
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.core.credentials import AccessToken

# === Flask App Setup ===
app = Flask(__name__)

# === Load environment variables from .env ===
load_dotenv()
endpoint = os.getenv("ENDPOINT")
model_deployment = os.getenv("MODEL_DEPLOYMENT")

# === Token Fetcher ===
def get_access_token():
    credential = DefaultAzureCredential()
    token: AccessToken = credential.get_token("https://ai.azure.com/.default")
    return token.token

# === Footer Version ===
FOOTER = "Development version 1.004"

# === Home Route ===
@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

# === Image Generation Route ===
@app.route("/generate", methods=["POST"])
def generate_image():
    data = request.get_json()
    prompt = data.get("prompt", "").strip()

    if not prompt:
        return jsonify({"error": "Prompt is required", "footer": FOOTER}), 400

    try:
        url = f"{endpoint}/infer"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {get_access_token()}"
        }
        payload = {
            "inputs": {"prompt": prompt},
            "deployment": model_deployment
        }

        response = requests.post(url, headers=headers, json=payload)

        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError:
            pass  # Foundry may return payload even with 401

        result = response.json()

        image_url = None
        if "outputs" in result:
            if isinstance(result["outputs"], dict):
                image_url = result["outputs"].get("image_url")
                if not image_url and "images" in result["outputs"]:
                    image_url = result["outputs"]["images"][0].get("url")
            elif isinstance(result["outputs"], list):
                image_url = result["outputs"][0].get("url")
        elif "data" in result:
            image_url = result["data"][0].get("url")
        elif "url" in result:
            image_url = result.get("url")

        if not image_url:
            print("DEBUG: Raw Foundry response:", result)  # Log to console
            return jsonify({
                "error": "No image URL returned",
                "raw_response": result,
                "footer": FOOTER
            }), 500

        return jsonify({"image_url": image_url, "footer": FOOTER})

    except Exception as ex:
        return jsonify({"error": str(ex), "footer": FOOTER}), 500

# === Health Check Route ===
@app.route("/health", methods=["GET"])
def health_check():
    try:
        token = get_access_token()
        return jsonify({
            "status": "ok",
            "token_prefix": token[:20] + "...",
            "endpoint": endpoint,
            "deployment": f"Deployment active: {model_deployment}",
            "footer": FOOTER
        })
    except Exception as ex:
        return jsonify({
            "status": "error",
            "message": str(ex),
            "footer": FOOTER
        }), 500

# === Debug Route ===
@app.route("/debug", methods=["GET"])
def debug_info():
    try:
        token = get_access_token()
        env_vars = {key: os.getenv(key) for key in sorted(os.environ.keys())}
        return jsonify({
            "status": "ok",
            "token_prefix": token[:20] + "...",
            "endpoint": endpoint,
            "deployment": f"Currently wired to {model_deployment}",
            "env": env_vars,
            "footer": FOOTER
        })
    except Exception as ex:
        return jsonify({
            "status": "error",
            "message": str(ex),
            "footer": FOOTER
        }), 500

# === Run Locally ===
if __name__ == "__main__":
    app.run(debug=True)