# === Imports ===
import os
import json
import requests
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv

# === Flask App Setup ===
app = Flask(__name__)

# === Load environment variables from .env ===
load_dotenv()
endpoint = os.getenv("ENDPOINT")  # https://philbot251114instance.services.ai.azure.com/
api_version = os.getenv("API_VERSION")  # e.g. 2024-02-01
model_deployment = os.getenv("MODEL_DEPLOYMENT")  # dall-e-3
api_key = os.getenv("AZURE_OPENAI_API_KEY")

# === Home Route (for browser UI) ===
@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

# === Image Generation Route (Azure OpenAI REST) ===
@app.route("/generate", methods=["POST"])
def generate_image():
    data = request.get_json()
    prompt = data.get("prompt", "").strip()

    if not prompt:
        return jsonify({"error": "Prompt is required"}), 400

    try:
        url = f"{endpoint}/openai/deployments/{model_deployment}/images/generations?api-version={api_version}"

        headers = {
            "Content-Type": "application/json",
            "api-key": api_key
        }

        payload = {
            "prompt": prompt,
            "n": 1,
            "size": "1024x1024"
        }

        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()

        image_url = result.get("data", [{}])[0].get("url")

        if not image_url:
            return jsonify({
                "error": "No image URL returned",
                "raw_response": result
            }), 500

        return jsonify({"image_url": image_url})

    except Exception as ex:
        return jsonify({"error": str(ex)}), 500

# === Run Locally (ignored by Render) ===
if __name__ == "__main__":
    app.run(debug=True)